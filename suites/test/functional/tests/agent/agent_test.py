import os
from UMA.som2_noEP import *
from client.UMARest import *
from qa.util.util import *
from cluster.cluster_setting import *

def test_agent():
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
    params_stationgary = {
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
    agent_stationary = EX.construct_agent('test_agent_stationary', None, None, params_stationgary)

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

    #path = os.path.join(UMA_SIM_HOME, 'suites', 'test', 'functional', 'playground', 'bin', 'ini', 'core.ini')
    #update_ini(path, 'Agent', {'q': '111'})