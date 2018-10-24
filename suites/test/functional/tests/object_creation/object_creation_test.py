import os
from UMA.som2_noEP import *
from client.UMARest import *
from qa.util.util import *
from cluster.cluster_setting import *

def test_experiment_creation():
    start_uma()
    service =  UMARestService('localhost', '8000')
    EX = Experiment('test_experiment', service)
    rest = UMAClientExperiment('test_experiment', service)
    assert rest.get_experiment_info() is not None

    rest = UMAClientExperiment('test_experiment1', service)
    assert rest.get_experiment_info() is None
    stop_uma()

def test_agent_creation():
    start_uma()
    service =  UMARestService('localhost', '8000')
    EX = Experiment('test_experiment', service)

    params_qualitative = {
        'type': 'qualitative',
        'AutoTarg': True,
    }
    params_discounted = {
        'type': 'discounted',
        'AutoTarg': True,
    }
    params_empirical = {
        'type': 'empirical',
        'AutoTarg': True,
    }
    params_stationary = {
        'type': 'default',
        'AutoTarg': True,
    }

    EX.register_sensor('test_agent_qualitative')
    agent_qualitative = EX.construct_agent('test_agent_qualitative', None, None, params_qualitative)
    EX.register_sensor('test_agent_discounted')
    agent_discounted = EX.construct_agent('test_agent_discounted', None, None, params_discounted)
    EX.register_sensor('test_agent_empirical')
    agent_empirical = EX.construct_agent('test_agent_empirical', None, None, params_empirical)
    EX.register_sensor('test_agent_stationary')
    agent_stationary = EX.construct_agent('test_agent_stationary', None, None, params_stationary)

    rest = UMAClientExperiment('test_experiment', service)
    agents = rest.get_experiment_info()['agent_ids']

    assert ['test_agent_qualitative', 'Qualitative'] in agents
    assert ['test_agent_discounted', 'Discounted'] in agents
    assert ['test_agent_empirical', 'Empirical'] in agents
    assert ['test_agent_stationary', 'Stationary'] in agents
    assert len(agents) == 4

    rest = UMAClientAgent('test_experiment', 'test_agent_qualitative', service)
    assert rest.get_agent_info() is not None

    rest = UMAClientAgent('test_experiment', 'test_agent_discounted', service)
    assert rest.get_agent_info() is not None

    rest = UMAClientAgent('test_experiment', 'test_agent_empirical', service)
    assert rest.get_agent_info() is not None

    rest = UMAClientAgent('test_experiment', 'test_agent_stationary', service)
    assert rest.get_agent_info() is not None

    rest = UMAClientAgent('test_experiment', 'test_agent_none', service)
    assert rest.get_agent_info() is None
    stop_uma()

def test_snapshot_creation_with_parameters():
    path = os.path.join(UMA_SIM_HOME, 'suites', 'test', 'functional', 'playground', 'bin', 'ini', 'core.ini')
    update_ini(path, 'Agent', {'q': '0.9', 'threshold': '0.125', 'total': '1', 'auto_target': '1', 'propagate_mask': '1'})
    update_ini(path, 'Agent::Qualitative', {'total': '-1'})
    update_ini(path, 'Agent::Discounted', {'total': '0', 'q': '0'})
    update_ini(path, 'Agent::Empirical', {'total': '2', 'q': '0'})

    start_uma()
    service =  UMARestService('localhost', '8000')
    EX = Experiment('test_experiment', service)

    params_qualitative = {
        'type': 'qualitative',
        'auto_target': False,
        'q': 0.01
    }
    params_discounted = {
        'type': 'discounted',
        'auto_target': False,
        'threshold': 0.25,
        'q': 0.8
    }
    params_empirical = {
        'type': 'empirical',
        'auto_target': False,
    }
    params_stationary = {
        'type': 'default',
        'auto_target': False,
    }

    EX.register_sensor('test_agent_qualitative')
    agent_qualitative = EX.construct_agent('test_agent_qualitative', None, None, params_qualitative)
    EX.register_sensor('test_agent_discounted')
    agent_discounted = EX.construct_agent('test_agent_discounted', None, None, params_discounted)
    EX.register_sensor('test_agent_empirical')
    agent_empirical = EX.construct_agent('test_agent_empirical', None, None, params_empirical)
    EX.register_sensor('test_agent_stationary')
    agent_stationary = EX.construct_agent('test_agent_stationary', None, None, params_stationary)

    rest_snapshot_qualitative_plus = UMAClientSnapshot('test_experiment', 'test_agent_qualitative', 'plus', service)
    rest_snapshot_qualitative_plus_info = rest_snapshot_qualitative_plus.get_snapshot_info()
    assert rest_snapshot_qualitative_plus_info['auto_target'] == False
    assert rest_snapshot_qualitative_plus_info['q'] == 0
    assert rest_snapshot_qualitative_plus_info['threshold'] == 0.125
    assert rest_snapshot_qualitative_plus_info['total'] == -1
    assert rest_snapshot_qualitative_plus_info['propagate_mask'] == True

    rest_snapshot_discounted_plus = UMAClientSnapshot('test_experiment', 'test_agent_discounted', 'plus', service)
    rest_snapshot_discounted_plus_info = rest_snapshot_discounted_plus.get_snapshot_info()
    assert rest_snapshot_discounted_plus_info['auto_target'] == False
    assert rest_snapshot_discounted_plus_info['q'] == 0
    assert rest_snapshot_discounted_plus_info['threshold'] == 0.25
    assert rest_snapshot_discounted_plus_info['total'] == 0
    assert rest_snapshot_discounted_plus_info['propagate_mask'] == True

    rest_snapshot_empirical_plus = UMAClientSnapshot('test_experiment', 'test_agent_empirical', 'plus', service)
    rest_snapshot_empirical_plus_info = rest_snapshot_empirical_plus.get_snapshot_info()
    assert rest_snapshot_empirical_plus_info['auto_target'] == False
    assert rest_snapshot_empirical_plus_info['q'] == 0
    assert rest_snapshot_empirical_plus_info['threshold'] == 0.125
    assert rest_snapshot_empirical_plus_info['total'] == 2
    assert rest_snapshot_empirical_plus_info['propagate_mask'] == True

    rest_snapshot_stationary_plus = UMAClientSnapshot('test_experiment', 'test_agent_stationary', 'plus', service)
    rest_snapshot_stationary_plus_info = rest_snapshot_stationary_plus.get_snapshot_info()
    assert rest_snapshot_stationary_plus_info['auto_target'] == False
    assert rest_snapshot_stationary_plus_info['q'] == 0
    assert rest_snapshot_stationary_plus_info['threshold'] == 0.125
    assert rest_snapshot_stationary_plus_info['total'] == 1
    assert rest_snapshot_stationary_plus_info['propagate_mask'] == True

    stop_uma()