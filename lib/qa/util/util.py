import sys
import os
import time
from subprocess import call
from ConfigParser import SafeConfigParser
from cluster.cluster_setting import *
import platform

current_dir = os.getcwd()
uma_core_test_bin = os.path.join(UMA_SIM_HOME, 'suites', 'test', 'functional', 'playground', 'bin')
binary_name = "UMA.exe" if 'Windows' == platform.system() else "./UMA"


# start UMA
def start_uma():
    os.chdir(uma_core_test_bin)

    cmd = [binary_name, 'start']
    p = call(cmd)
    time.sleep(3)
    os.chdir(current_dir)

# stop UMA
def stop_uma():
    os.chdir(uma_core_test_bin)
    cmd = [binary_name, 'stop']
    call(cmd)
    os.chdir(current_dir)

# update the conf file
def update_ini(ini_path, stanza, kwargs):
    parser = SafeConfigParser()
    parser.read(ini_path)

    for k, v in kwargs.iteritems():
        parser.set(stanza, k, v)

    with open(ini_path, 'w') as f:
        parser.write(f)