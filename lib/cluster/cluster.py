from multiprocessing import Pool
from multiprocessing import Process
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

    def start(self, func, filename, Nruns, Ninstances, port, host):
        self.filename = filename
        self.instance = Ninstances
        self.Nruns = Nruns
        self.port = port
        self.host = host

        n = 0
        pool = {}
        clk = time.time()

        while n < Nruns:
            for p in pool.keys():
                if not pool[p].is_alive():
                    print "%s is done" % p
                    del pool[p]

            l = len(pool)
            while l < self._Nprocesses and n < Nruns:
                params = self.parameter_generator(n, filename, host, port)
                #print params
                kwargs = {'run_params': params}
                process = Process(target=func, kwargs=kwargs)
                process.daemon = True # set the process to daemon, in case pool crash, all processes will be cleared
                pool[params['test_name']] = process
                process.start()
                print "start test: %s" % params['test_name']
                n += 1
                l += 1

            time.sleep(1)

        for p in pool:
            pool[p].join()
            print "%s is done" % p

        print "All runs are done!\n"
        print "Elapsed time: " + str(time.time() - clk) + "\n"

    def parameter_generator(self, idx, filename, host, port):
        info = YamlManager(filename).get_dict()
        params = info['params']
        name = params['name']
        params['Nruns']=info['Nruns']
        params['host'] = host
        params['port'] = str(int(port) + idx % self.instance)
        params['test_name'] = "%s_%d" % (name, idx)
        return params

    def get_Nprocesses(self):
        return self._Nprocesses