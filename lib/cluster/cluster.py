from multiprocessing import Pool
import sys
import os
import yaml
import time
import cPickle
from cluster_setting import *

class YamlManager:
    def __init__(self, filename):
        try:
            with open(filename, 'r') as f:
                self._dict = yaml.load(f)
        except Exception as ex:
            print "Fatal error reading %s, please check the file, err=%s" % (filename, str(ex))
            exit(0)

    def get_dict(self):
        return self._dict

    def get_value(self, key):
        return self._dict[key]

class ClusterManager:
    def __init__(self):
        self._dict = YamlManager(os.path.join(UMA_SIM_HOME, 'lib', 'cluster', CLUSTER_YML)).get_dict()
        self._Ninstances = self._dict['Cluster']['Ninstances']
        self._host = self._dict['Cluster']['host']
        self._port = int(self._dict['Cluster']['port'])

    def get_Ninstances(self):
        return self._Ninstances

    def get_host(self):
        return self._host

    def get_port(self):
        return self._port

class PoolManager:
    def __init__(self):
        self._dict = YamlManager(os.path.join(UMA_SIM_HOME, 'lib', 'cluster', POOL_YML)).get_dict()
        self._Nprocesses = int(self._dict['Pool']['Nprocesses'])
        self._p = Pool(processes=self._Nprocesses)

    def start(self, func, filename, Nruns, Ninstances, port, host):
        self.filename = filename
        self.instance = Ninstances
        self.port = port
        self.host = host
        self.nruns = Nruns

        clk = time.clock()
        self._p.map(func, self.gen_params(filename, Nruns, host, port),chunksize=1)
        self._p.close()
        self._p.join()
        print "All runs are done!\n"
        print "Elapsed time: " + str(time.clock() - clk) + "\n"

    def parameter_generator(self, idx, filename, host, port):
        info = YamlManager(filename).get_dict()
        params = info['params']
        name = params['name']
        params['Nruns']=info['Nruns']
        params['host'] = host
        params['port'] = str(int(port) + idx % self.instance)
        params['test_name'] = "%s_%d" % (name, idx)
        return params

    def gen_params(self, filename, Nruns, host, port):
        for i in range(Nruns):
            yield self.parameter_generator(i, filename, host, port)

    def get_Nprocesses(self):
        return self._Nprocesses