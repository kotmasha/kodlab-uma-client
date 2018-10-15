import os
import sys
import shutil
import time
import errno
import importlib
import traceback
import subprocess
from subprocess import call
from cluster.cluster import YamlManager
from cluster.cluster_setting import *

current_dir = os.getcwd()
uma_core_test_bin = os.path.join(UMA_SIM_HOME, 'suites', 'test', 'functional', 'playground', 'bin')

def copy_uma_binary(uma_bin_path):
    try:
        shutil.copytree(uma_bin_path, uma_core_test_bin)
        print "UMA binary is successfully copied to playground"
    except OSError as exc:  # python >2.5
        if exc.errno == errno.ENOTDIR:
            shutil.copy(uma_bin_path, uma_core_test_bin)
        else:
            raise

def start_uma():
    os.chdir(uma_core_test_bin)
    cmd = ["UMA.exe", 'start']
    p = call(cmd)
    time.sleep(3)
    os.chdir(current_dir)

def stop_uma():
    os.chdir(uma_core_test_bin)
    cmd = ["UMA.exe", 'stop']
    call(cmd)
    os.chdir(current_dir)

def remove_old_bin():
    old_bin_path = os.path.join(UMA_SIM_HOME, 'suites', 'test', 'functional', 'playground', 'bin')
    try:
        shutil.rmtree(old_bin_path)
    except Exception as ex:
        print "Error when trying to remove bin folder, error: %s" % str(ex)

def test_yml_precheck(data):
    if 'tests' not in data:
        raise Exception("The tests field is missing from the yml!")
    tests = data['tests']

    if 'script' not in tests:
        raise Exception("The script field is missing from the tests field!")

    if 'name' not in tests:
        raise Exception("The name field is missing from the tests field!")

def launch_test(data):
    script = importlib.import_module(data['tests']['script'])
    func = getattr(script, data['tests']['name'])
    func()

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print "To run a functional test: uma_test.py <test.yml>"
        exit()

    test_yml = sys.argv[1]
    data = YamlManager(test_yml).get_dict()
    test_yml_precheck(data)

    remove_old_bin()
    copy_uma_binary(data['uma_bin_path'])

    try:
        start_uma()
        launch_test(data)
        print "Test succeed!"
    except Exception as ex:
        tb = traceback.format_exc()
        print tb
        print "Test Fail!"
    finally:
        stop_uma()

