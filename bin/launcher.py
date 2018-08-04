# This is the launcher for UMA Simulation
import sys
import os
import importlib
import cPickle
from cluster.cluster import *

def check_fields(data):
    fmt = "{} field is missing from yaml file!"
    for s in ['script', 'func', 'Nruns', 'params']:
        if s not in data:
            raise Exception(fmt.format(s))

def dump_pickle(name, params):
    os.mkdir(name)
    preamblef = open(".\\%s\\%s.pre" % (name, name), "wb")
    cPickle.dump(params, preamblef, protocol=cPickle.HIGHEST_PROTOCOL)
    preamblef.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print "Usage of launcher: launcher.py <test.yml>"
        exit()

    test_yml = sys.argv[1]
    data = YamlManager(test_yml).get_dict()

    check_fields(data)

    script = importlib.import_module(data['script'])
    func = getattr(script, data['func'])

    Nruns = int(data['Nruns'])
    data['params']['Nruns']=data['Nruns']
    params = data['params']
    #print params
    test_name = data['params']['name']
    test_yml_abs_path = os.path.join(os.getcwd(), test_yml)
    print "Simulation label: %s" % test_name
    print "Simulation yml file: %s" % test_yml_abs_path
    print "Using script: %s" % str(script.__name__)
    print "Function called from script: %s" % str(func.__name__)
    print "Will execute %d simulation runs.\n" % Nruns

    dump_pickle(test_name, params)
    cluster = ClusterManager()
    pool = PoolManager()
    pool.start(func, test_yml_abs_path, Nruns, cluster.get_Ninstances(), cluster.get_port(), cluster.get_host())

    print "All runs are done.\n"