#This is the wrapper file for the python functional test
import requests
import json
import yaml
import os

class test_wrapper:

    def __init__(self, scheme = 'http', ip = 'localhost', port = '8000'):
        self._url = scheme + '://' + ip + ':' + port
        self._headers = {'Content-type': 'application/json', 'Accpet': 'text/plain'}
        self._log = open('./client.txt', 'w')

    def run_test(self, filename):
        f = open(filename, 'r')
        dict = yaml.load(f)
        for case in dict['tests']:
            test_case = dict[case]
            method = test_case['method']
            url = test_case['url']
            status_code = test_case['status_code']
            if 'data' in test_case:
                data = test_case['data']
            else:
                data = None
            if 'query' in test_case:
                query = test_case['query']
            else:
                query = None
            if 'message' in test_case:
                message = test_case['message']
            else:
                message = None
            if 'kwargs' in test_case:
                kwargs = test_case['kwargs']
            else:
                kwargs = None
            try:
                self.T(method, url, status_code, data, query, message, kwargs)
            except Exception as e:
                print "Error in " + filename + ": " + case
                raise e
        print "%s test passed!" % os.path.basename(filename)

    def T(self, method, url, status_code, data=None, query=None, message=None, kwargs=None):
        url = self._url + url
        if method == "POST":
            response = requests.post(url, json.dumps(data), headers = self._headers)
            if not response.status_code == status_code:
                print response.status_code, status_code
                print response.json()['message']
                assert response.status_code == status_code
            if message is not None:
                if message not in response.json()['message']:
                    print message, response.json()['message']
                    assert message in response.json()['message']
            if kwargs is not None:
                for key, value in kwargs.iteritems():
                    if 'data' not in response.json() or key not in response.json()['data']:
                        print "No %s fields found in return value" % key
                        assert False
                    if not self.compare_obj(response.json()['data'][key], value):
                        print "error key: " + key
                        print value, response.json()['data'][key]
                        assert False
        elif method == "GET":
            response = requests.get(url, params = query, headers = self._headers)
            if not response.status_code == status_code:
                print response.status_code, status_code
                print response.json()['message']
                assert response.status_code == status_code
            if message is not None:
                if message not in response.json()['message']:
                    print message, response.json()['message']
                    assert message in response.json()['message']
            if kwargs is not None:
                for key, value in kwargs.iteritems():
                    if 'data' not in response.json() or key not in response.json()['data']:
                        print "No %s fields found in return value" % key
                        assert False
                    if not self.compare_obj(response.json()['data'][key], value):
                        print "error key: " + key
                        print value, response.json()['data'][key]
                        assert False
        elif method == "DELETE":
            response = requests.delete(url, data=json.dumps(data), headers = self._headers)
            if not response.status_code == status_code:
                print response.status_code, status_code
                print response.json()['message']
                assert response.status_code == status_code
            if message is not None:
                if message not in response.json()['message']:
                    print message, response.json()['message']
                    assert message in response.json()['message']
        elif method == "PUT":
            response = requests.put(url, data = json.dumps(data), params=query, headers = self._headers)
            if not response.status_code == status_code:
                print response.status_code, status_code
                print response.json()['message']
                assert response.status_code == status_code
            if message is not None:
                if message not in response.json()['message']:
                    print message, response.json()['message']
                    assert message in response.json()['message']

    def run(self, test_file):
        pass

    def compare_obj(self, la, lb):
        if type(la) is not list and type(lb) is list:
            return False
        if type(la) is list and type(lb) is not list:
            return False
        if type(la) is not list and type(lb) is not list:
            if type(la) is float and type(lb) is float:
                return abs(la - lb) < 1e-5
            else:
                return la == lb
        if len(la) is not len(lb):
            return False
        return all([self.compare_obj(a, b) for (a, b) in zip(la, lb)])