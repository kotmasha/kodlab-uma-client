import sys
import os
import time
from ConfigParser import SafeConfigParser

# update the conf file
def update_ini(ini_path, stanza, kwargs):
    parser = SafeConfigParser()
    parser.read(ini_path)

    for k, v in kwargs.iteritems():
        parser.set(stanza, k, v)

    with open(ini_path, 'w') as f:
        parser.write(f)