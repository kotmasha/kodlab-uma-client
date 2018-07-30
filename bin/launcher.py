# This is the launcher for UMA Simulation
import sys
import os
import importlib
import cPickle
from cluster.cluster import *

def check_fields(data):
    fmt = "{} field is missing from yaml file!"
    for s in ['script', 'fun', 'iter', 'params']:
        if s not in data:
            raise Exception(fmt.format(s))

def dump_pickle(name, params):
    os.mkdir(name)
    preamblef = open(".\\%s\\%s.pre" % (name, name), "wb")
    cPickle.dump(params, preamblef, protocol=cPickle.HIGHEST_PROTOCOL)
    preamblef.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print "Usage of launcher: launcyer.py <test.yml>"
        exit()

    test_yml = sys.argv[1]
    data = YamlManager(test_yml).get_dict()

    check_fields(data)

    script = importlib.import_module(data['script'])
    fun = getattr(script, data['fun'])
    iter = int(data['iter'])
    params = data['params']
    test_name = data['params']['name']
    test_yml_abs_path = os.path.join(os.getcwd(), test_yml)
    print "name of the test: %s" % test_name
    print "test yml file: %s" % test_yml_abs_path
    print "script using: %s" % str(script.__name__)
    print "fun calling from script: %s" % str(fun.__name__)
    print "will do the test for %d times" % iter

    dump_pickle(test_name, params)
    cluster = ClusterManager()
    pool = PoolManager()
    pool.start(fun, test_yml_abs_path, iter, cluster.get_instance(), cluster.get_port(), cluster.get_host())

    print "all test are done"