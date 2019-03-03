#https://www.pythoncentral.io/introduction-to-sqlite-in-python/
import argparse
import sqlite3
import csv
import json
from os import path
from datetime import datetime

#parameters
DEFAULT_VLC_PATH = r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe"
USER_HOME = path.expanduser('~')

def watch():
    try:
        args = parse() #-h stops here
        print vars(args) #TODO: delete this line when done
        #get settings and db
        cwd = path.dirname(path.realpath(__file__))
        db_path = path.join(cwd, "db")
        settings_path = path.join(cwd, "settings")
        if path.isfile(settings_path):
            settings_dict = read_settings(settings_path)
        elif not args.settings_flag:
            raise Exception("The settings file is missing or corrupt. Please use 'watch -s'")
        else:
            settings_dict = None
        db_exists = path.isfile(db_path)
        db = sqlite3.connect(db_path)
        cursor = db.cursor()
        if not db_exists: #new db
            cursor.execute('''
            CREATE TABLE series(
                id INTEGER PRIMARY KEY UNIQUE,
                "full name" TEXT,
                name TEXT,
                "last season" INTEGER,
                "last episode" INTEGER,
                "total episodes" INTEGER,
                "date added" TEXT)
            ''')
        if args.view_flag or args.export_flag: #we need whole DB for both
            cursor.execute("SELECT * FROM series")
            db_items = cursor.fetchall()
        #view
        if args.view_flag:
            view(db_items)
        #settings
        if args.settings_flag:
            settings_dict = settings(settings_dict, args)
            write_settings(settings_path, settings_dict)
        #add
        if args.add_flag:
            #TODO: add show to DB
            if args.cli_flag:
                pass
            else:
                pass
        #edit
        #delete
        #export
        if args.export_flag:
            if export_id in settings:
                settings['export_id'] = 1
            else:
                settings['export_id'] += 1
            #TODO: get export file location from settings, decide file name (settings), create csv
            export(export_file_path, db_items)
        #watch series
        if args.series_name:
            if args.season:
                if args.episode: #watch <series_name> S<season>E<episode>
                    pass
                else: #season but no episode
                    raise Exception("A season must be followed by an episode.")
            else: #get last episode from sql etc.
                pass 
        #finish
        db.close()
    except Exception as e:
        print "Error:", e


def parse():
    parser = argparse.ArgumentParser(prog='watch',
        description="" +
        "watch an episode of a series in your selected video player. Use watch -s to \n" +
        "change settings (already done if installed correctly), then add a series with \n" +
        "watch -a, and watch it with watch <series_name>. Some examples:\n" +
        "1. watch GoT 1 4 : Watch first season, fourth episode of the series you added as 'got'.\n"
        "2. watch Vikings : Watch the next episode of the series you added as 'vikings'.\n" +
        "3. watch -ve : Print and export your watch stats.",
        epilog='it is recommended to set up the settings, add a series, and then use watch \r\nwithout parameters until the last episode of the series',
        usage='watch [series_name [season episode]] [-h] [-a | -e | -r | -s | -x] [-v] [-c] [-d]',
        formatter_class=argparse.RawDescriptionHelpFormatter)

    group1 = parser.add_mutually_exclusive_group()
    group1.add_argument('-a','--add', help="add a new series to watch", action='store_true', dest='add_flag')
    group1.add_argument('-e','--edit', help="edit a series you've already added, keeping the last and total episodes watched", action='store_true', dest='edit_flag')
    group1.add_argument('-r','--remove', help="remove a series you've added completely.", action='store_true', dest='remove_flag')
    group1.add_argument('-s','--settings', help="edit the settings", action='store_true', dest='settings_flag')
    group1.add_argument('-x','--export', help="export series stats to excel file", action='store_true', dest='export_flag')
    
    parser.add_argument('-v','--view', help="print series stats on terminal", action='store_true', dest='view_flag')
    parser.add_argument('series_name', help="the name of the series to be watched, as specified when added", nargs='?')
    parser.add_argument('season', help="the season to be watched", nargs='?', type=int)
    parser.add_argument('episode', help="the episode to be watched", nargs='?', type=int)
    parser.add_argument('-c','--cli', help="use with add, settings, or export, to open them in a command line interface", action='store_true', dest='cli_flag')
    parser.add_argument('-d','--debug', help="print file name instead of watching it, without saving to database", action='store_true', dest='debug_flag')
    return parser.parse_args()


def add():
    pass


def edit():
    pass


def remove():
    pass


def settings(settings_dict, args):
    #TODO:update player path, export path, etc. in cli/gui and create watch.cmd there
    if settings_dict:
        old_settings_dict = settings_dict
    else:
        #default settings
        old_settings_dict = dict(
            player_path = DEFAULT_VLC_PATH,
            export_path = USER_HOME,
            )
    settings_dict = {}
    if args.cli_flag: #CLI
        #TODO: go over settings one by one
        print "Type in each setting to change it, leave blank for no changes (old value in parentheses)"
        for k,v in old_settings_dict.iteritems():
            prompt_text = str(k) + '(' + str(v) + '):'
            new_setting = raw_input(prompt_text)
            settings_dict[k] = new_setting if new_setting else v
    else: #GUI
        pass
    return settings_dict


def export(export_file_path, db_items):
    pass


def view():
    pass


def read_settings(file):
    with open(file, 'r') as f:
        ret = json.load(f)
    return ret


def write_settings(file, settings_dict):
    with open(file, 'w+') as f:
        json.dump(settings_dict, f)
    return


if __name__ == '__main__':
    watch()
