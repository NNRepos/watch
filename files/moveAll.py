"""This script moves watch.cmd, watch.py, requirements to the user's python folder"""

import sys
import shutil
from os import path

try:
    py_path = path.dirname(sys.executable)
    cwd = path.dirname(path.realpath(__file__))
    
    #watch.py
    path_to_watch_folder = path.join(py_path, 'lib', 'site-packages', 'watch_next')
    path_to_nearby_watch_folder = path.join(cwd, 'watch_next')
    if path.isdir(path_to_watch_folder):
        shutil.rmtree(path_to_watch_folder)
    shutil.copytree(path_to_nearby_watch_folder, path_to_watch_folder)
    
    #scripts folder for setx
    path_to_scripts = path.join(py_path, 'scripts')
    path_to_folder_txt = path.join(cwd, 'folder.txt')
    with open(path_to_folder_txt, "wb") as f:
        f.write(path_to_scripts)
    
    #watch.cmd
    path_to_watch_py = path.join (path_to_watch_folder, 'watch.py')
    path_to_watch_cmd = path.join(path_to_scripts, 'watch.cmd')
    cmd_file_content = '@python "' + path_to_watch_py + r'" %1 %2 %3 %4 %5 %6 %7 %8 %9'
    with open(path_to_watch_cmd, "w+") as f:
        f.write(cmd_file_content)
    
except Exception as e:
    print e
    sys.exit(1)