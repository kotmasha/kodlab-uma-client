import os
from UMA.som2_noEP import *
from client.UMARest import *
from qa.util.util import *
from cluster.cluster_setting import *

def test_saving_loading():
    start_uma()

    service = UMARestService('localhost', '8000')
    EX1 = create_experiment('test_experiment', service)

    params_qualitative = {
        'type': 'qualitative',
        'AutoTarg': True,
        'discount': 0.01,
        'threshold': 1.23,
        'total': 1.1
    }
    params_discounted = {
        'type': 'discounted',
        'AutoTarg': False,
        'threshold': 0.25,
        'discount': 0.8,
        'total': 1.0
    }
    params_empirical = {
        'type': 'empirical',
        'AutoTarg': False,
        'threshold': 0.234,
        'discount': 0.02,
        'total': 1.1
    }
    params_stationary = {
        'type': 'default',
        'AutoTarg': True,
        'discount': 0.9,
        'total': 2.0,
        'threshold': 0.2
    }

    EX1.register_sensor('test_agent_qualitative')
    agent_qualitative = EX1.construct_agent('test_agent_qualitative', None, None, params_qualitative)
    EX1.register_sensor('test_agent_discounted')
    agent_discounted = EX1.construct_agent('test_agent_discounted', None, None, params_discounted)
    EX1.register_sensor('test_agent_empirical')
    agent_empirical = EX1.construct_agent('test_agent_empirical', None, None, params_empirical)
    EX1.register_sensor('test_agent_stationary')
    agent_stationary = EX1.construct_agent('test_agent_stationary', None, None, params_stationary)

    test_sensor1, c_test_sensor1 = EX1.register_sensor('test_sensor1')
    test_sensor2, c_test_sensor2 = EX1.register_sensor('test_sensor2')
    test_sensor3, c_test_sensor3 = EX1.register_sensor('test_sensor3')
    test_sensor4, c_test_sensor4 = EX1.register_sensor('test_sensor4')

    agent_qualitative.add_sensor(test_sensor1)
    agent_qualitative.add_sensor(test_sensor2)
    agent_discounted.add_sensor(test_sensor3)
    agent_discounted.add_sensor(test_sensor4)
    agent_empirical.add_sensor(test_sensor1)
    agent_empirical.add_sensor(test_sensor3)
    agent_empirical.add_sensor(test_sensor4)
    agent_stationary.add_sensor(test_sensor4)

    agent_qualitative.init()
    agent_empirical.init()
    agent_discounted.init()
    agent_stationary.init()

    EX1.save_experiment()
    EX1.remove_experiment()

    EX2 = create_experiment('test_experiment', service)
    EX2.load_experiment()

    # check agents loaded
    agents = UMAClientExperiment('load_test_experiment', service).get_experiment_info()['agent_ids']

    assert ['test_agent_qualitative', 'Qualitative'] in agents
    assert ['test_agent_discounted', 'Discounted'] in agents
    assert ['test_agent_empirical', 'Empirical'] in agents
    assert ['test_agent_stationary', 'Stationary'] in agents

    # check agent qualitative
    agent_qualitative_client = UMAClientAgent('load_test_experiment', 'test_agent_qualitative', service)
    agent_qualitative_info = agent_qualitative_client.get_agent_info()

    assert ['plus', 'Qualitative'] in agent_qualitative_info['snapshot_ids']
    assert ['minus', 'Qualitative'] in agent_qualitative_info['snapshot_ids']

    for snapshot_id in ['plus', 'minus']:
        snapshot_qualitative_info = UMAClientSnapshot('load_test_experiment', 'test_agent_qualitative',
                                                      snapshot_id, service).get_snapshot_info()
        assert snapshot_qualitative_info['auto_target'] == True
        assert snapshot_qualitative_info['q'] == 0.01
        assert snapshot_qualitative_info['threshold'] == 1.23
        assert snapshot_qualitative_info['total'] == 1.1
        assert snapshot_qualitative_info['initial_size'] == 2
        assert ['test_sensor1', 'test_sensor1*'] in snapshot_qualitative_info['sensors']
        assert ['test_sensor2', 'test_sensor2*'] in snapshot_qualitative_info['sensors']

    # check agent empirical
    agent_empirical_client = UMAClientAgent('load_test_experiment', 'test_agent_empirical', service)
    agent_empirical_info = agent_empirical_client.get_agent_info()

    assert ['plus', 'Empirical'] in agent_empirical_info['snapshot_ids']
    assert ['minus', 'Empirical'] in agent_empirical_info['snapshot_ids']

    for snapshot_id in ['plus', 'minus']:
        snapshot_empirical_info = UMAClientSnapshot('load_test_experiment', 'test_agent_empirical',
                                                      snapshot_id, service).get_snapshot_info()

        assert snapshot_empirical_info['auto_target'] == False
        assert snapshot_empirical_info['q'] == 0.02
        assert snapshot_empirical_info['threshold'] == 0.234
        assert snapshot_empirical_info['total'] == 1.1
        assert snapshot_empirical_info['initial_size'] == 3
        assert ['test_sensor1', 'test_sensor1*'] in snapshot_empirical_info['sensors']
        assert ['test_sensor3', 'test_sensor3*'] in snapshot_empirical_info['sensors']
        assert ['test_sensor4', 'test_sensor4*'] in snapshot_empirical_info['sensors']

    # check for agent discounted
    agent_discounted_client = UMAClientAgent('load_test_experiment', 'test_agent_discounted', service)
    agent_discounted_info = agent_discounted_client.get_agent_info()

    assert ['plus', 'Discounted'] in agent_discounted_info['snapshot_ids']
    assert ['minus', 'Discounted'] in agent_discounted_info['snapshot_ids']

    for snapshot_id in ['plus', 'minus']:
        snapshot_discounted_info = UMAClientSnapshot('load_test_experiment', 'test_agent_discounted',
                                                      snapshot_id, service).get_snapshot_info()

        assert snapshot_discounted_info['auto_target'] == False
        assert snapshot_discounted_info['q'] == 0.8
        assert snapshot_discounted_info['threshold'] == 0.25
        assert snapshot_discounted_info['total'] == 1.0
        assert snapshot_discounted_info['initial_size'] == 2
        assert ['test_sensor3', 'test_sensor3*'] in snapshot_discounted_info['sensors']
        assert ['test_sensor4', 'test_sensor4*'] in snapshot_discounted_info['sensors']

    # check for agent stationary
    agent_stationary_client = UMAClientAgent('load_test_experiment', 'test_agent_stationary', service)
    agent_stationary_info = agent_stationary_client.get_agent_info()

    assert ['plus', 'Stationary'] in agent_stationary_info['snapshot_ids']
    assert ['minus', 'Stationary'] in agent_stationary_info['snapshot_ids']

    for snapshot_id in ['plus', 'minus']:
        snapshot_stationary_info = UMAClientSnapshot('load_test_experiment', 'test_agent_stationary',
                                                      snapshot_id, service).get_snapshot_info()

        assert snapshot_stationary_info['auto_target'] == True
        assert snapshot_stationary_info['q'] == 0.9
        assert snapshot_stationary_info['threshold'] == 0.2
        assert snapshot_stationary_info['total'] == 2.0
        assert snapshot_stationary_info['initial_size'] == 1
        assert ['test_sensor4', 'test_sensor4*'] in snapshot_stationary_info['sensors']

    stop_uma()