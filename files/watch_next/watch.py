import argparse
import Tkinter
import sqlite3
import csv
import json
import sys
import re

from os import path, walk
from datetime import datetime
from subprocess import Popen

#parameters
DEFAULT_WMP_PATH = r"C:\Program Files (x86)\Windows Media Player\wmplayer.exe"
DEFAULT_VLC_PATH = r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe"
DEFAULT_MPC_PATH = r"C:\Program Files\MPC-HC\mpc-hc64.exe"
#"D:\downloads\Game.of.Thrones.Season.1-6.S01-S06.1080p.10bit.5.1.BluRay.x265.HEVC-MZABI"
USER_HOME = path.expanduser('~')
VIDEO_FILE_EXTENSIONS = r"(webm|mkv|flv|vob|ogv|ogg|drc|gifv|mng|avi|mts|m2ts|mov|qt|wmv|yuv|rm|rmvb|asf|amv|mp4|m4p|m4v|mpg|mp2|mpeg|mpe|mpv|m2v|svi|3gp|3g2|mxf|roq|nsv|f4v|f4p|f4a|f4b)" #no gifs

def watch():
    """This is the main function, parses the arguments and activates the other functions.
    """
    try:
        cwd = path.dirname(path.realpath(__file__)) #watch.py's directory
        settings_path = path.join(cwd, "settings")
        db, cursor = get_db(cwd) #create db in watch.py's directory
        assert sys.platform.startswith('win'), "watch.py is for windows only."
        parser = parse() #-h stops here
        args = parser.parse_args()
        settings_dict = get_settings(args.settings_flag, settings_path)
        #get whole db
        if args.view_flag or args.export_flag: #we need whole DB for both
            cursor.execute("SELECT * FROM series")
            db_items = cursor.fetchall()
        #view
        if args.view_flag:
            view(db_items)
        #settings
        if args.settings_flag:
            settings_dict = settings(settings_dict, args.cli_flag, settings_path)
        #add
        if args.add_flag:
            add(db, cursor, args.cli_flag)
        #edit
        if args.edit_flag:
            edit(db, cursor, args.cli_flag)
        #remove
        if args.remove_flag:
            remove(db, cursor, args.cli_flag)
        #export
        if args.export_flag:
            export(settings_dict, settings_path, db_items)
        #get series data
        prepared = False
        
        #if specified in args
        if args.series_name: 
            series_dict = get_series_from_db(cursor, args.series_name)
            if args.season:
                if args.episode: #watch <series_name> S<season>E<episode>
                    try:
                        season = int(args.season)
                        episode = int(args.episode)
                    except:
                        raise Exception('season and episode must be integers')
                    total = series_dict['total_episodes_watched']
                    prepared = True
                else: #season but no episode
                    raise Exception("A season must be followed by an episode.")
            else: 
                episode, season, _, total = get_next_episode(series_dict)
                prepared = True
        
        #if no other args specified
        elif not (args.add_flag or args.edit_flag or 
            args.remove_flag or args.settings_flag or 
            args.export_flag or args.view_flag):
            if 'last series watched' in settings_dict:
                last_series = settings_dict['last series watched']
                series_dict = get_series_from_db(cursor, last_series)
                episode, season, _, total = get_next_episode(series_dict)
                prepared = True
            else:
                parser.print_help()
                raw_input()
            
        #actually watch
        if prepared:
            settings_dict['last series watched'] = series_dict['name']
            series_dict['last_episode_watched'] = episode
            series_dict['last_season_watched'] = season
            series_dict['total_episodes_watched'] = total + 1
            if season<1 or episode<1:
                raise Exception('season and episode must be positive')
            edit(db, cursor, prompt=False, series_dict=series_dict)
            write_settings(settings_path, settings_dict)
            play(settings_dict, series_dict)
    except Exception as e:
        print "Error:", e #, "at", sys.exc_info()[2].tb_lineno
        raw_input()
        sys.exit(1)
    finally:
        db.close()


def parse():
    parser = argparse.ArgumentParser(prog='watch',
        description="" +
        "watch an episode of a series in your selected video player. Use watch -s to \n" +
        "change settings (already done if installed correctly), then add a series with \n" +
        "watch -a, and watch it with watch <series_name>. Some examples:\n" +
        "1. watch GoT 1 4 : Watch first season, fourth episode of the series you added as 'got'.\n"
        "2. watch Vikings : Watch the next episode of the series you added as 'vikings'.\n" +
        "3. watch -vx : Print and export your watch stats.",
        epilog="" +
        "it is recommended to use watch the following way:\n" +
        "1. set up the settings (e.g. during installation)\n" +
        "2. add a series using watch -a\n" +
        "3. watch the series once using watch <series_name>, and\n" +
        "4. use watch without parameters until the last episode of the series",
        usage='watch [series_name [season episode]] [-h] [-a | -e | -r | -s | -x] [-v] [-c]',
        formatter_class=argparse.RawDescriptionHelpFormatter)
    
    group1 = parser.add_mutually_exclusive_group()
    group1.add_argument('-a','--add', help="add a new series to watch", action='store_true', dest='add_flag')
    group1.add_argument('-e','--edit', help="edit a series you've already added, keeping the last and total episodes watched", action='store_true', dest='edit_flag')
    group1.add_argument('-r','--remove', help="remove a series you've added completely.", action='store_true', dest='remove_flag')
    group1.add_argument('-s','--settings', help="edit the settings", action='store_true', dest='settings_flag')
    group1.add_argument('-x','--export', help="export series stats to csv(excel) file", action='store_true', dest='export_flag')
    
    parser.add_argument('-v','--view', help="print series stats on terminal", action='store_true', dest='view_flag')
    parser.add_argument('series_name', help="the name of the series to be watched, as specified when added", nargs='?')
    parser.add_argument('season', help="the season to be watched", nargs='?', type=int)
    parser.add_argument('episode', help="the episode to be watched", nargs='?', type=int)
    parser.add_argument('-c','--cli', help="use with add, settings, or export, to open them in a command line interface", action='store_true', dest='cli_flag')
    
    return parser


def add(db, cursor, cli):
    new_series = {
        'name' : "",
        'full_name' : "",
        'path' : ""
    }
    if cli:
        print "Type in the following values:"
        for k,v in new_series.iteritems():
            prompt_text = unslugify(str(k)) + ':'
            new_series[k] = raw_input(prompt_text)
            if k=='path':
                new_series[k] = new_series[k].strip(''''"''')
    else: #GUI
        pass
    new_series['last_season_watched'] = 1
    new_series['last_episode_watched'] = 0
    new_series['total_episodes_watched'] = 0
    new_series['date_added'] = datetime.now().strftime("%B %m, %Y, %H:%M:%S")
    cursor.execute('''INSERT INTO series(name, "full name", path, "last season watched", "last episode watched", "total episodes watched", "date added")
        VALUES(:name, :full_name, :path, :last_season_watched, :last_episode_watched, :total_episodes_watched, :date_added)
    ''', new_series)
    db.commit()


def edit(db, cursor, cli=False, prompt=True, series_dict=None):
    """Edits a DB row with user interference(prompt=True),
    or without it (prompt=False, series_dict!=None).
    series_dict must be slugified.
    """
    if prompt:
        if cli: #TODO: use if cli else in between common lines
            series_name = raw_input("Enter the name(short) of the series you want to edit(use watch -v to view your series):")
            series_dict = get_series_from_db(cursor, series_name)
            print "Type in each value to edit the field, leave blank for no changes (old value in parentheses)"
            for k,v in series_dict.iteritems():
                if k=='id' or k=='total_episodes_watched':
                    continue
                prompt_text = unslugify(str(k)) + '(' + str(v) + '):'
                new_value = raw_input(prompt_text)
                if k=='path':
                    series_dict[k] = series_dict[k].strip(''''"''')
                if new_value and (k=='last_episode_watched' or k=='last_season_watched' or k=='total_episodes_watched'):
                    try:
                        int(new_value)
                    except Exception:
                        raise Exception(str(k) + " has to be a number.")
                series_dict[k] = new_value or v
        else: #GUI
            pass
    #store in db
    cursor.execute('''DELETE FROM series WHERE name=?''', (series_dict['name'],))
    cursor.execute('''INSERT INTO series(name, "full name", path, "last season watched", "last episode watched", "total episodes watched", "date added")
        VALUES(:name, :full_name, :path, :last_season_watched, :last_episode_watched, :total_episodes_watched, :date_added)
    ''', series_dict)
    db.commit()
    if prompt:
        raw_input("edit successful.")


def remove(db, cursor, cli):
    if cli: #TODO: use if cli else in between common lines
        series_name = raw_input("Enter the name(short) of the series you want to remove(use watch -v to view your series):")
    else: #GUI
        pass
    series_dict = get_series_from_db(cursor, series_name)
    #remove from db
    cursor.execute('''DELETE FROM series WHERE name=?''', (series_dict['name'],))
    db.commit()
    raw_input("removal successful.")


def settings(settings_dict, cli, settings_path):
    #TODO: GUI
    if settings_dict:
        old_settings_dict = settings_dict
        settings_dict = {}
    else:
        #default settings
        old_settings_dict = {
            'player path' : DEFAULT_VLC_PATH,
            'export path' : USER_HOME,
            }
    if cli:
        print "Type in each setting to change it, leave blank for no changes (old value in parentheses)"
        for k,v in old_settings_dict.iteritems():
            if k == 'player path':
                print "type wmp for default Windows Media Player path, and same for vlc/mpc"
            prompt_text = unslugify(str(k)) + '(' + str(v) + '):'
            new_setting = raw_input(prompt_text).strip(''''"''') or v
            if k == 'player path':
                nslow = new_setting.lower()
                if nslow == 'wmp':
                    new_setting = DEFAULT_WMP_PATH
                elif nslow == 'vlc':
                    new_setting = DEFAULT_VLC_PATH
                elif nslow == 'mpc':
                    new_setting = DEFAULT_MPC_PATH
                if not path.isfile(new_setting):
                    raise Exception('The player path is incorrect')
                if new_setting.endswith('lnk'):
                    raise Exception('The player path must not be a shortcut')
            if k == 'export path':
                if not path.isdir(new_setting):
                    raise Exception('The export path is incorrect')
            settings_dict[k] = new_setting
    else: #GUI
        pass
    write_settings(settings_path, settings_dict)
    return settings_dict


def export(settings_dict, settings_path, db_items):
    if 'export id' not in settings_dict:
        settings_dict['export id'] = 0
    settings_dict['export id'] += 1
    export_file_name = "series" + "{:>03}".format(settings_dict['export id']) + ".csv"
    export_file_path = path.join(settings_dict['export path'], export_file_name)
    try:
        with open(export_file_path, "wb") as f:
            if db_items:
                writer = csv.writer(f)
                writer.writerow(db_items[0].keys())
                for row in db_items:
                    writer.writerow(row)
            else:
                f.write("The database is empty.")
    except:
        raise Exception("The export path is incorrect")
    write_settings(settings_path, settings_dict)


def view(db_items):
    if db_items:
        keys = db_items[0].keys()
        print "printing database:"
        for row in db_items:
            for k,v in zip(keys, row):
                print (str(k) + ": " + str(v)).center(119,' ')
            print ''.center(119,'_')
    else:
        print "looks like the database is empty."
    raw_input("press enter to proceed")


def read_settings(file):
    with open(file, 'r') as f:
        ret = json.load(f)
    return ret


def write_settings(file, settings_dict):
    with open(file, 'w+') as f:
        json.dump(settings_dict, f)
    return


def get_settings(flag, settings_path): #TODO: make sure no1 using settings b4 they exist
    if path.isfile(settings_path):
        settings_dict = read_settings(settings_path)
        if 'player path' not in settings_dict or \
            'export path' not in settings_dict:
            raise Exception("The settings file is corrupt. Please delete it from site-packages, and use 'watch -s'")
    elif not flag:
        raise Exception("The settings file is missing. Please use 'watch -s'")
    else:   
        settings_dict = {}
    return settings_dict


def get_db(cwd):
    db_path = path.join(cwd, "db")
    db_exists = path.isfile(db_path)
    db = sqlite3.connect(db_path)
    db.row_factory = sqlite3.Row
    cursor = db.cursor()
    if not db_exists: #new db
        cursor.execute('''
        CREATE TABLE series(
            id INTEGER PRIMARY KEY UNIQUE,
            name TEXT UNIQUE,
            "full name" TEXT,
            path TEXT,
            "last season watched" INTEGER,
            "last episode watched" INTEGER,
            "total episodes watched" INTEGER,
            "date added" TEXT)
        ''')
    db.commit
    return db, cursor


def slugify(str):
    return re.sub(' ', '_', str)


def unslugify(str):
    return re.sub('_', ' ', str)


def get_series_from_db(cursor, series_name):
    cursor.execute('''SELECT * FROM series WHERE name = ?''',
        (series_name,))
    result = cursor.fetchone()
    if not result:
        raise Exception("no series with such name: " + str(series_name))
    dict_keys = map(slugify, result.keys())
    series_dict = dict(zip(dict_keys, result))
    return series_dict


def find_file(series_path, season, episode):
    target = r".*S0*" + str(season) + "E0*" + str(episode) + r"(\D.*|)\." + VIDEO_FILE_EXTENSIONS
    found = False
    for root, dirs, files in walk(series_path):
        if found:
            break;
        for file in files:
            if(re.match(target,file, flags=re.IGNORECASE)):
                found=[episode, season, path.join(root,file)]
    else: #nothing found
        episode = 1
        season += 1
        target = r".*S0*" + str(season) + "E0*" + str(episode) + r"(\D.*|)\." + VIDEO_FILE_EXTENSIONS
        for root, dirs, files in walk(series_path):
            for file in files:
                if(re.match(target,file, flags=re.IGNORECASE)):
                    found=[episode, season, path.join(root,file)]
    return found

def get_next_episode(series_dict): #TODO
    series_path = series_dict['path']
    episode = series_dict['last_episode_watched'] + 1
    season = series_dict['last_season_watched']
    total = series_dict['total_episodes_watched']
    found = find_file(series_path, season, episode)
    if not found:
        if total > 0: #was found before
            raise Exception("CONGRATULATIONS! You have finished " + series_dict['full_name'] +
            "!\r\nYou can add another series using watch -a, or look at your stats using watch -v")
        else:
            raise Exception("It seems like the path(" + series_path + ") is incorrect.\r\n" +
                "Please change it using watch -e")
    found.append(total)
    return found

def play(settings_dict, series_dict): #TODO
    #get video
    series_path = series_dict['path']
    episode = series_dict['last_episode_watched']
    season = series_dict['last_season_watched']
    found = find_file(series_path, season, episode)
    found_path = found[2]
    #get player
    player_path = settings_dict['player path']
    #awaken
    Popen([player_path,found_path],stdin=None, stdout=None, stderr=None)


if __name__ == '__main__':
    try:
        watch()
    except KeyboardInterrupt:
        print "Leaving already?"
