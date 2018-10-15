import os
from UMA.som2_noEP import *
from client.UMARest import *

def test_experiment():
    service =  UMARestService('localhost', '8000')
    EX = Experiment('test_experiment', service)
    rest = UMAClientExperiment('test_experiment', service)
    assert rest.get_experiment_info() is not None

    rest = UMAClientExperiment('test_experiment1', service)
    assert rest.get_experiment_info() is None