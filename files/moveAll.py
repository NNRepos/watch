"""This script moves watch.cmd, watch.py, requirements to the user's python folder"""

import sys
import shutil
from os import path

py_path = path.dirname(sys.executable)
here = path.dirname(path.realpath(__file__))

path_to_watch_folder = path.join(py_path, 'lib', 'site-packages', 'watch')
path_to_watch_py = path.join (path_to_watch_folder, 'watch.py')
path_to_watch_cmd = path.join(py_path, 'scripts', 'watch.cmd')

#watch.py
if path.isdir(path_to_watch_folder):
    raise Exception("watch folder already exists in site-packages")
shutil.copytree(path.join(here, 'watch'), path_to_watch_folder)

#watch.cmd
cmd_file_content = '@python "' + path_to_watch_py + r'" %1 %2 %3 %4 %5 %6 %7 %8 %9'
with open(path_to_watch_cmd, "w+") as f:
    f.write(cmd_file_content)