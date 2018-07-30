import requests
import logging
import sys
import os
import json

class UMARestService:
    def __init__(self, host='localhost', port='8000'):
        #self.logger = logging.getLogger("RestService")
        #self.logger.setLevel(logging.DEBUG)
        self._headers = {'Content-type': 'application/json', 'Accpet': 'text/plain'}
        self._base_url = "http://%s:%s" % (host, port)
        #self._log = open('./client.txt', 'w')

    def post(self, uri, data):
        uri = self._base_url + uri
        try:
            r = requests.post(uri, data=json.dumps(data), headers=self._headers)
        except Exception, e:
            #self._log.write("Errors while doing post request " + uri + ': ' + str(e) + '\n')
            return None
        if r.status_code >= 400 and r.status_code < 500:
            #self._log.write("Client Error(" + str(r.status_code) + "): " + str(r.json()['message'] + '\n'))
            return None
        if r.status_code >= 500:
            #self._log.write("Server Error(" + str(r.status_code) + ") please check server log" + '\n')
            return None
        #self._log.write("(" + str(r.status_code) + ") " + str(r.json()['message']) + '\n')
        return r.json()

    def get(self, uri, query):
        uri = self._base_url + uri
        retry = 0
        while retry < 5:
            try:
                r = requests.get(uri, params=query, headers=self._headers)
                break
            except:
                #self._log.write("Errors while doing get request " + uri + '\n')
                retry += 1
                if retry == 5:
                    return None

        if r.status_code >= 400 and r.status_code < 500:
            #self._log.write("Client Error(" + str(r.status_code) + "): " + str(r.json()['message'] + '\n'))
            return None
        if r.status_code >= 500:
            #self._log.write("Server Error(" + str(r.status_code) + ") please check server log" + '\n')
            return None
        #self._log.write("(" + str(r.status_code) + ") " + str(r.json()['message']) + '\n')
        return r.json()

    def put(self, uri, data, query):
        uri = self._base_url + uri
        try:
            r = requests.put(uri, data=json.dumps(data), params=query, headers=self._headers)
        except:
            #self._log.write("Errors while doing put request " + uri + '\n')
            return None
        if r.status_code >= 400 and r.status_code < 500:
            #self._log.write("Client Error(" + str(r.status_code) + "): " + str(r.json()['message'] + '\n'))
            return None
        if r.status_code >= 500:
            #self._log.write("Server Error(" + str(r.status_code) + ") please check server log" + '\n')
            return None
        #self._log.write("(" + str(r.status_code) + ") " + str(r.json()['message']) + '\n')
        return r.json()

    def delete(self):
        pass

class UMAClientObject:
    def __init__(self, service):
        self._service = service

    def get_service(self):
        return self._service

class UMAClientWorld(UMAClientObject):
    def __init__(self, service):
        # self.logger = logging.getLogger("ClientWorld")
        self._service = service
        pass

    def add_experiment(self, experiment_id):
        data = {'experiment_id': experiment_id}
        result = self._service.post('/UMA/object/experiment', data)
        if not result:
            print "create experiment=%s failed!" % experiment_id
            return None
        else:
            return UMAClientExperiment(experiment_id, self.get_service())

class UMAClientExperiment(UMAClientObject):
    def __init__(self, experiment_id, service):
        #self.logger = logging.getLogger("ClientExperiment")
        self._service = service
        self._experiment_id = experiment_id

    def get_experiment_id(self):
        return self._experiment_id

    def add_agent(self, agent_id, type='default'):
        data = {'experiment_id': self._experiment_id, 'agent_id': agent_id, 'type': type}
        result = self._service.post('/UMA/object/agent', data)
        if not result:
            print "create agent=%s failed!" % agent_id
            return None
        else:
            return UMAClientAgent(self._experiment_id, agent_id, self.get_service())

class UMAClientAgent(UMAClientObject):
    def __init__(self, experiment_id, agent_id, service):
        #self.logger = logging.getLogger("ClientAgent")
        self._service = service
        self._experiment_id = experiment_id
        self._agent_id = agent_id

    def get_experiment_id(self):
        return self._experiment_id

    def get_agent_id(self):
        return self._agent_id

    def add_snapshot(self, snapshot_id):
        data = {'snapshot_id': snapshot_id, 'agent_id': self._agent_id, 'experiment_id': self._experiment_id}
        result = self._service.post('/UMA/object/snapshot', data)
        if not result:
            print "create snapshot=%s failed!" % snapshot_id
            return None
        else:
            return UMAClientSnapshot(self._experiment_id, self._agent_id, snapshot_id, self.get_service())

class UMAClientSnapshot(UMAClientObject):
    def __init__(self, experiment_id, agent_id, snapshot_id, service):
        #self.logger = logging.getLogger("ClientSnapshot")
        self._service = service
        self._experiment_id = experiment_id
        self._agent_id = agent_id
        self._snapshot_id = snapshot_id

    def get_experiment_id(self):
        return self._experiment_id

    def get_agent_id(self):
        return self._agent_id

    def get_snapshot_id(self):
        return self._snapshot_id

    def add_sensor(self, sensor_id, c_sensor_id):
        data = {'experiment_id': self._experiment_id, 'agent_id': self._agent_id, 'snapshot_id': self._snapshot_id,
                'sensor_id': sensor_id, 'c_sid': c_sensor_id, 'w': [], 'd': [], 'diag': []}
        result =  self._service.post('/UMA/object/sensor', data)
        if not result:
            print "add sensor=%s failed!" % sensor_id
            return None
        else:
            return UMAClientSensor(self._experiment_id, self._agent_id, self._snapshot_id, sensor_id, self.get_service())

    def init(self):
        data = {'experiment_id': self._experiment_id, 'agent_id': self._agent_id, 'snapshot_id': self._snapshot_id}
        result = self._service.post('/UMA/object/snapshot/init', data)
        if not result:
            return None
        return result

    def set_auto_target(self, auto_target):
        return self._service.put('/UMA/object/snapshot', {'auto_target': auto_target}, {'experiment_id': self._experiment_id,
                        'agent_id': self._agent_id, 'snapshot_id': self._snapshot_id})

    def set_propagate_mask(self, propagate_mask):
        return self._service.put('/UMA/object/snapshot', {'propagate_mask': propagate_mask}, {'experimentId': self._experiment_id,
                        'agent_id': self._agent_id, 'snapshot_id': self._snapshot_id})

    def set_initial_size(self, initial_size):
        return self._service.put('/UMA/object/snapshot', {'initial_size': initial_size}, {'experiment_id': self._experiment_id,
                        'agent_id': self._agent_id, 'snapshot_id': self._snapshot_id})

    def set_q(self, q):
        return self._service.put('/UMA/object/snapshot', {'q': q}, {'experiment_id': self._experiment_id,
                        'agent_id': self._agent_id, 'snapshot_id': self._snapshot_id})

    def set_threshold(self, threshold):
        return self._service.put('/UMA/object/snapshot', {'threshold': threshold}, {'experiment_id': self._experiment_id,
                        'agent_id': self._agent_id, 'snapshot_id': self._snapshot_id})

    def delay(self, delay_list, uuid_list):
        data = {'experiment_id': self._experiment_id, 'agent_id': self._agent_id, 'snapshot_id': self._snapshot_id,
                'delay_lists': delay_list, 'uuid_lists': uuid_list}
        result = self._service.post('/UMA/object/snapshot/delay', data)
        if not result:
            return False
        return True

    def pruning(self, signal):
        data = {'experiment_id': self._experiment_id, 'agent_id': self._agent_id, 'snapshot_id': self._snapshot_id,
                'signals': signal}
        result = self._service.post('/UMA/object/snapshot/pruning', data)
        if not result:
            return False
        return True

class UMAClientData:
    def __init__(self, experiment_id, agent_id, snapshot_id, service):
        #self.logger = logging.getLogger("ClientData")
        self._service = service
        self._experiment_id = experiment_id
        self._agent_id = agent_id
        self._snapshot_id = snapshot_id

    def get_experiment_id(self):
        return self._experiment_id

    def get_agent_id(self):
        return self._agent_id

    def get_snapshot_id(self):
        return self._snapshot_id

    def getCurrent(self):
        return self._service.get('/UMA/data/current', {'experiment_id': self._experiment_id,
                                    'agent_id': self._agent_id, 'snapshot_id': self._snapshot_id})

    def getPrediction(self):
        return self._service.get('/UMA/data/prediction', {'experiment_id': self._experiment_id,
                                    'agent_id': self._agent_id, 'snapshot_id': self._snapshot_id})

    def getTarget(self):
        return self._service.get('/UMA/data/target', {'experiment_id': self._experiment_id,
                                    'agent_id': self._agent_id, 'snapshot_id': self._snapshot_id})

    def getNegligible(self):
        return self._service.get('/UMA/data/negligible', {'experiment_id': self._experiment_id,
                        'agent_id': self._agent_id, 'snapshot_id': self._snapshot_id})['data']['negligible']

    def setTarget(self, target):
        return self._service.put('/UMA/data/target',{'target': target}, {'experiment_id': self._experiment_id,
                        'agent_id': self._agent_id, 'snapshot_id': self._snapshot_id})

class UMAClientSensor:
    def __init__(self, experiment_id, agent_id, snapshot_id, sensor_id, service):
        #self.logger = logging.getLogger("ClientSensor")
        self._service = service
        self._experiment_id = experiment_id
        self._agent_id = agent_id
        self._snapshot_id = snapshot_id
        self._sensor_id = sensor_id

    def get_experiment_id(self):
        return self._experiment_id

    def get_agent_id(self):
        return self._agent_id

    def get_snapshot_id(self):
        return self._snapshot_id

    def get_sensor_id(self):
        return self._sensor_id

    def getAmperList(self):
        result = self._service.get('/UMA/object/sensor', {'experiment_id': self._experiment_id,
                            'agent_id': self._agent_id, 'snapshot_id': self._snapshot_id, 'sensor_id': self._sensor_id})
        if not result:
            return None
        result = result['data']['amper_list']
        return result

    def getAmperListID(self):
        result = self._service.get('/UMA/object/sensor', {'experiment_id': self._experiment_id,
                            'agent_id': self._agent_id, 'snapshot_id': self._snapshot_id, 'sensor_id': self._sensor_id})
        if not result:
            return None
        result = result['data']['amper_list_id']
        return result

    def setAmperList(self, amper_list):
        result = self._service.post('/UMA/object/sensor', {'experiment_id': self._experiment_id,
                            'agent_id': self._agent_id, 'snapshot_id': self._snapshot_id, 'sensor_id': self._sensor_id,
                            'amper_list': amper_list})
        if not result:
            return None
        return result

class UMAClientAttrSensor:
    def __init__(self):
        #self.logger = logging.getLogger("ClientAttrSensor")
        pass

class UMAClientSimulation:
    def __init__(self, experiment_id, service):
        #self.logger = logging.getLogger("ClientSimulation")
        self._service = service
        self._experiment_id = experiment_id

    def get_experiment_id(self):
        return self._experiment_id

    def make_decision(self, agent_id, obs_plus, obs_minus, phi, active):
        #post to service:
        data =  {'experiment_id': self._experiment_id, 'agent_id': agent_id, 'phi': phi,
                 'active': active, 'obs_plus': obs_plus, 'obs_minus': obs_minus}
        result = self._service.post('/UMA/simulation/decision', data)
        if not result:
            return None
        result = result['data']
        plus = {'res': float(result['res_plus']), 'current': result['current_plus'],
                'prediction': result['prediction_plus'], 'target': result['target_plus']}
        minus = {'res': float(result['res_minus']), 'current': result['current_minus'],
                 'prediction': result['prediction_minus'], 'target': result['target_minus']}
        return {'plus': plus, 'minus': minus}

    def make_up(self, signal):
        data =  {'experiment_id': self._experiment_id, 'agent_id': self._agent_id, 'snapshot_id': self._snapshot_id,
                 'signal': signal}
        result = self._service.post('/UMA/simulation/up', data)
        if not result:
            return None
        return list(result['data']['signal'])

    def make_abduction(self, signals):
        data =  {'experiment_id': self._experiment_id, 'agent_id': self._agent_id, 'snapshot_id': self._snapshot_id,
                 'signals': signals}
        result = self._service.post('/UMA/simulation/abduction', data)
        if not result:
            return None
        return list(result['data']['abduction_even']), list(result['data']['abduction_odd'])

    def make_propagate_masks(self):
        data =  {'experiment_id': self._experiment_id, 'agent_id': self._agent_id, 'snapshot_id': self._snapshot_id}
        result = self._service.post('/UMA/simulation/propagateMasks', data)
        if not result:
            return None
        return list(result['data']['propagate_mask'])

    def make_ups(self, signals):
        data =  {'experiment_id': self._experiment_id, 'agent_id': self._agent_id,
                 'snapshot_id': self._snapshot_id, 'signals': signals}
        result = self._service.post('/UMA/simulation/ups', data)
        if not result:
            return None
        return list(result['data']['signals'])

    def make_downs(self, signals):
        data =  {'experiment_id': self._experiment_id, 'agent_id': self._agent_id, 'snapshot_id': self._snapshot_id,
                 'signals': signals}
        result = self._service.post('/UMA/simulation/downs', data)
        if not result:
            return None
        return list(result['data']['signals'])

    def make_propagation(self, signals, load):
        data =  {'experimentId': self._experiment_id, 'agentId': self._agent_id, 'snapshotId': self._snapshot_id,
                 'signals': signals, 'load': load}
        result = self._service.post('/UMA/simulation/propagation', data)
        if not result:
            return None
        return list(result['data']['signals'])

    def make_blocks(self, dists, delta):
        data =  {'experiment_id': self._experiment_id, 'agent_id': self._agent_id, 'snapshot_id': self._snapshot_id,
                 'dists': dists, 'delta': delta}
        result = self._service.post('/UMA/simulation/blocks', data)
        if not result:
            return None
        return list(result['data']['blocks'])

    def make_npdirs(self):
        data = {'experiment_id': self._experiment_id, 'agent_id': self._agent_id, 'snapshot_id': self._snapshot_id}
        result = self._service.post('/UMA/simulation/npdirs', data)
        if not result:
            return None
        return list(result['data']['npdirs'])