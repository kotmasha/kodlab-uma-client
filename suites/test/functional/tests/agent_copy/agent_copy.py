import os
from UMA.som2_noEP import *
from client.UMARest import *
from qa.util.util import *
from cluster.cluster_setting import *

def test_agent_copy_simple():
    start_uma()

    service =  UMARestService('localhost', '8000')
    EX1 = create_experiment('test_experiment1', service)
    EX2 = create_experiment('test_experiment2', service)

    params = {
        'type': 'default',
    }

    EX1.register_sensor('test_agent')
    agent_qualitative = EX1.construct_agent('test_agent', None, None, params)

    rest_agent = UMAClientAgent('test_experiment1', 'test_agent', service)
    agent_info = rest_agent.get_agent_info()

    assert agent_info['type'] == 'Stationary'
    assert ['plus', 'Stationary'] in agent_info['snapshot_ids']
    assert ['minus', 'Stationary'] in agent_info['snapshot_ids']

    agent_entire_info = rest_agent.copy_agent('test_experiment2', 'test_agent_copy')
    assert agent_entire_info['type'] == 'Stationary'
    assert agent_entire_info['agent_id'] == 'test_agent_copy'
    assert 'plus' in agent_entire_info
    assert 'minus' in agent_entire_info

    stop_uma()

def test_agent_copy():
    start_uma()

    service =  UMARestService('localhost', '8000')
    EX1 = create_experiment('test_experiment1', service)
    EX2 = create_experiment('test_experiment2', service)

    params_qualitative = {
        'type': 'qualitative',
        'AutoTarg': True,
        'discount': 0.01,
        'threshold': 1.23
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

    rest_agent_qualitative = UMAClientAgent('test_experiment1', 'test_agent_qualitative', service)
    agent_qualitative_info = rest_agent_qualitative.copy_agent('test_experiment2', 'test_agent_qualitative_copy')

    rest_agent_empirical = UMAClientAgent('test_experiment1', 'test_agent_empirical', service)
    agent_empirical_info = rest_agent_empirical.copy_agent('test_experiment2', 'test_agent_empirical_copy')
    
    rest_agent_discounted = UMAClientAgent('test_experiment1', 'test_agent_discounted', service)
    agent_discounted_info = rest_agent_discounted.copy_agent('test_experiment2', 'test_agent_discounted_copy')
    
    rest_agent_stationary = UMAClientAgent('test_experiment1', 'test_agent_stationary', service)
    agent_stationary_info = rest_agent_stationary.copy_agent('test_experiment2', 'test_agent_stationary_copy')

    # qualitative
    assert agent_qualitative_info['type'] == 'Qualitative'
    assert agent_qualitative_info['agent_id'] == 'test_agent_qualitative_copy'
    for snapshot in ['plus', 'minus']:
        assert agent_qualitative_info['plus']['q'] == 0.01
        assert agent_qualitative_info[snapshot]['initial_size'] == 2
        assert agent_qualitative_info[snapshot]['auto_target'] == True
        assert agent_qualitative_info[snapshot]['threshold'] == 1.23
        assert agent_qualitative_info[snapshot]['total'] == -1
        assert ['test_sensor1', 'test_sensor1*'] in agent_qualitative_info[snapshot]['sensors']
        assert ['test_sensor2', 'test_sensor2*'] in agent_qualitative_info[snapshot]['sensors']

    # empirical
    assert agent_empirical_info['type'] == 'Empirical'
    assert agent_empirical_info['agent_id'] == 'test_agent_empirical_copy'
    for snapshot in ['plus', 'minus']:
        assert agent_empirical_info[snapshot]['initial_size'] == 3
        assert agent_empirical_info[snapshot]['q'] == 0.02
        assert agent_empirical_info[snapshot]['auto_target'] == False
        assert agent_empirical_info[snapshot]['threshold'] == 0.234
        assert agent_empirical_info[snapshot]['total'] == 1.1
        assert ['test_sensor1', 'test_sensor1*'] in agent_empirical_info[snapshot]['sensors']
        assert ['test_sensor3', 'test_sensor3*'] in agent_empirical_info[snapshot]['sensors']
        assert ['test_sensor4', 'test_sensor4*'] in agent_empirical_info[snapshot]['sensors']

    # discounted
    assert agent_discounted_info['type'] == 'Discounted'
    assert agent_discounted_info['agent_id'] == 'test_agent_discounted_copy'
    for snapshot in ['plus', 'minus']:
        assert agent_discounted_info[snapshot]['initial_size'] == 2
        assert agent_discounted_info[snapshot]['q'] == 0.8
        assert agent_discounted_info[snapshot]['auto_target'] == False
        assert agent_discounted_info[snapshot]['threshold'] == 0.25
        assert agent_discounted_info[snapshot]['total'] == 1.0
        assert ['test_sensor3', 'test_sensor3*'] in agent_discounted_info[snapshot]['sensors']
        assert ['test_sensor4', 'test_sensor4*'] in agent_discounted_info[snapshot]['sensors']
        
    # stationary
    # discounted
    assert agent_stationary_info['type'] == 'Stationary'
    assert agent_stationary_info['agent_id'] == 'test_agent_stationary_copy'
    for snapshot in ['plus', 'minus']:
        assert agent_stationary_info[snapshot]['initial_size'] == 1
        assert agent_stationary_info[snapshot]['q'] == 0.9
        assert agent_stationary_info[snapshot]['auto_target'] == True
        assert agent_stationary_info[snapshot]['threshold'] == 0.2
        assert agent_stationary_info[snapshot]['total'] == 2.0
        assert ['test_sensor4', 'test_sensor4*'] in agent_stationary_info[snapshot]['sensors']

    stop_uma()

def test_saving_loading_copy():
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
    EX3 = create_experiment('new_test_experiment', service)

    rest_agent_qualitative = UMAClientAgent('load_test_experiment', 'test_agent_qualitative', service)
    agent_qualitative_info = rest_agent_qualitative.copy_agent('new_test_experiment', 'test_agent_qualitative_copy')

    rest_agent_empirical = UMAClientAgent('load_test_experiment', 'test_agent_empirical', service)
    agent_empirical_info = rest_agent_empirical.copy_agent('new_test_experiment', 'test_agent_empirical_copy')

    rest_agent_discounted = UMAClientAgent('load_test_experiment', 'test_agent_discounted', service)
    agent_discounted_info = rest_agent_discounted.copy_agent('new_test_experiment', 'test_agent_discounted_copy')

    rest_agent_stationary = UMAClientAgent('load_test_experiment', 'test_agent_stationary', service)
    agent_stationary_info = rest_agent_stationary.copy_agent('new_test_experiment', 'test_agent_stationary_copy')

    # qualitative
    assert agent_qualitative_info['type'] == 'Qualitative'
    assert agent_qualitative_info['agent_id'] == 'test_agent_qualitative_copy'
    for snapshot in ['plus', 'minus']:
        assert agent_qualitative_info[snapshot]['q'] == 0.01
        assert agent_qualitative_info[snapshot]['initial_size'] == 2
        assert agent_qualitative_info[snapshot]['auto_target'] == True
        assert agent_qualitative_info[snapshot]['threshold'] == 1.23
        assert agent_qualitative_info[snapshot]['total'] == 1.1
        assert ['test_sensor1', 'test_sensor1*'] in agent_qualitative_info[snapshot]['sensors']
        assert ['test_sensor2', 'test_sensor2*'] in agent_qualitative_info[snapshot]['sensors']

    # empirical
    assert agent_empirical_info['type'] == 'Empirical'
    assert agent_empirical_info['agent_id'] == 'test_agent_empirical_copy'
    for snapshot in ['plus', 'minus']:
        assert agent_empirical_info[snapshot]['initial_size'] == 3
        assert agent_empirical_info[snapshot]['q'] == 0.02
        assert agent_empirical_info[snapshot]['auto_target'] == False
        assert agent_empirical_info[snapshot]['threshold'] == 0.234
        assert agent_empirical_info[snapshot]['total'] == 1.1
        assert ['test_sensor1', 'test_sensor1*'] in agent_empirical_info[snapshot]['sensors']
        assert ['test_sensor3', 'test_sensor3*'] in agent_empirical_info[snapshot]['sensors']
        assert ['test_sensor4', 'test_sensor4*'] in agent_empirical_info[snapshot]['sensors']

    # discounted
    assert agent_discounted_info['type'] == 'Discounted'
    assert agent_discounted_info['agent_id'] == 'test_agent_discounted_copy'
    for snapshot in ['plus', 'minus']:
        assert agent_discounted_info[snapshot]['initial_size'] == 2
        assert agent_discounted_info[snapshot]['q'] == 0.8
        assert agent_discounted_info[snapshot]['auto_target'] == False
        assert agent_discounted_info[snapshot]['threshold'] == 0.25
        assert agent_discounted_info[snapshot]['total'] == 1.0
        assert ['test_sensor3', 'test_sensor3*'] in agent_discounted_info[snapshot]['sensors']
        assert ['test_sensor4', 'test_sensor4*'] in agent_discounted_info[snapshot]['sensors']

    # stationary
    # discounted
    assert agent_stationary_info['type'] == 'Stationary'
    assert agent_stationary_info['agent_id'] == 'test_agent_stationary_copy'
    for snapshot in ['plus', 'minus']:
        assert agent_stationary_info[snapshot]['initial_size'] == 1
        assert agent_stationary_info[snapshot]['q'] == 0.9
        assert agent_stationary_info[snapshot]['auto_target'] == True
        assert agent_stationary_info[snapshot]['threshold'] == 0.2
        assert agent_stationary_info[snapshot]['total'] == 2.0
        assert ['test_sensor4', 'test_sensor4*'] in agent_stationary_info[snapshot]['sensors']

    stop_uma()