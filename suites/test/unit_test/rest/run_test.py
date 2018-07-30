from test_wrapper import *
import os

test = test_wrapper()

def dfs(path):
    for filename in os.listdir(path):
        filename = os.path.join(path, filename)
        if os.path.isfile(filename) and filename.endswith('.yml'):
            test.run_test(filename)
        elif os.path.isdir(filename):
            dfs(filename)

dfs('./data')

#test.run_test('test_data/agent_test.yml')
#print "Agent test passed"
#test.run_test('test_data/snapshot_test.yml')
#print "Snapshot test passed"
#test.run_test('test_data/sensor_test.yml')
#print "Sensor test passed"
#test.run_test('test_data/measurable_test.yml')
#print "Measurable test passed"
#test.run_test('data/simulation/matrix_test.yml')
#print "Matrix test passed"
#test.run_test('test_data/amper_test.yml')
#print "Amper test passed"
#test.run_test('test_data/delay_test.yml')
#print "Delay test passed"
#test.run_test('test_data/pruning_test.yml')
#print "Pruning test passed"
#test.run_test('test_data/abduction_test.yml')
#print "Abduction test passed"