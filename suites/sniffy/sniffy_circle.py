import numpy as np
from numpy.random import randint as rnd
from collections import deque
#import curses
import time
from UMA.som2_noEP import *
import sys
import os
import cPickle
from client.UMARest import *

def start_experiment(run_params):
    # System parameters
    test_name=run_params['test_name']
    host = run_params['host']
    port = run_params['port']

    # Recording options:
    record_mids=run_params['mids_to_record'] #[id_count,id_dist,id_sig]
    record_global=run_params['ex_dataQ'] #True
    record_agents=run_params['agent_dataQ'] #True

    # Decision cycles:
    TOTAL_CYCLES = run_params['total_cycles']
    BURN_IN_CYCLES = run_params['burn_in_cycles']
    # Parameters and definitions
    AutoTarg=bool(run_params['AutoTarg'])
    SnapType=run_params['SnapType']
    X_BOUND = run_params['circumference']  # length
    BEACON_WIDTH = run_params['beacon_width'] # width of place field centered at each position

    # distance function
    def dist(p, q):
        return min(abs(p-q),X_BOUND-abs(p-q))

    # agent parameters
    MOTION_PARAMS = {
        'type': SnapType,   #'qualitative',
        'AutoTarg': AutoTarg,   #False,
    }

    # initialize a new experiment
    EX = Experiment(test_name, UMARestService(host, port))
    id_dec = 'decision'
    id_count= 'counter'

    # register basic motion agents;
    # - $True$ tag means they will be marked as dependent (on other agents)
    id_rt, cid_rt = EX.register_sensor('rt')
    id_lt, cid_lt = EX.register_sensor('lt')

    # register motivation for motion agents
    # - this one is NOT dependent on agents except through the position, so
    #   it carries the default False tag.
    #id_at_targ, cid_at_targ = EX.register_sensor('atT')
    id_dist = EX.register('dist')
    id_sig = EX.register('sig')
    id_nav, cid_nav = EX.register_sensor('nav')

    # register arbiter variable whose purpose is provide a hard-wired response to a conflict
    # between agents 'lt' and 'rt'.
    id_arbiter = EX.register('arb')

    #
    ### Arbitration
    #

    # arbitration state
    def arbiter(state):
        return bool(rnd(2))
    EX.construct_measurable(id_arbiter, arbiter, [bool(rnd(2))], 0, decdep=True)

    # intention sensors
    id_toRT, cid_toRT = EX.register_sensor('toR')

    def intention_RT(state):
        return id_rt in state[id_dec][0]

    EX.construct_sensor(id_toRT, intention_RT, decdep=False)

    id_toLT, cid_toLT = EX.register_sensor('toL')

    def intention_LT(state):
        return id_lt in state[id_dec][0]

    EX.construct_sensor(id_toLT, intention_LT, decdep=False)

    # failure mode for action $lt^rt$
    id_toF, cid_toF = EX.register_sensor('toF')

    def about_to_enter_failure_mode(state):
        return state[id_toLT][0] and state[id_toRT][0]

    EX.construct_sensor(id_toF, about_to_enter_failure_mode, decdep=False)

    # add basic motion agents with arbitration
    def action_RT(state):
        rt_decided = (id_rt in state[id_dec][0])
        if state[id_toF][0]:
            # return not(rt_decided) if state[id_arbiter][0] else rt_decided
            return state[id_arbiter][0]
        else:
            return rt_decided

    RT = EX.construct_agent(id_rt, id_sig, action_RT, MOTION_PARAMS)

    def action_LT(state):
        lt_decided = (id_lt in state[id_dec][0])
        if state[id_toF][0]:
            # return lt_decided if state[id_arbiter][0] else not(lt_decided)
            return not (state[id_arbiter][0])
        else:
            return lt_decided

    LT = EX.construct_agent(id_lt, id_sig, action_LT, MOTION_PARAMS)

    #
    ### "mapping" system
    #

    ## introduce agent's position

    # select starting position
    START = 0

    # generate target position at distance at least X_BOUND/8 from START position
    TARGET = X_BOUND/8+rnd(7*X_BOUND)/8
 
    # effect of motion on position
    id_pos = EX.register('pos')
    def motion(state):
        triggers = {id_rt: 1, id_lt: -1}
        diff = 0
        for t in triggers:
            diff += triggers[t] * int(state[t][0])
        newpos = (state[id_pos][0] + diff) % X_BOUND
        return newpos
 
    EX.construct_measurable(id_pos, motion, [START, START])

    # set up position sensors
    def xsensor(m,w):  # along x-axis
        return lambda state: dist(state[id_pos][0],m)<=w

    for wid in xrange(1,BEACON_WIDTH):
        for pos in xrange(X_BOUND):
            tmp_name = 'x' + str(pos) + '_' + str(wid)
            id_tmp, id_tmpc = EX.register_sensor(tmp_name)  # registers the sensor pairs
            EX.construct_sensor(id_tmp, xsensor(pos,wid))  # constructs the measurables associated with the sensor
            RT.add_sensor(id_tmp)
            LT.add_sensor(id_tmp)

    # distance to target
    # - $id_dist$ has already been registerd
    def dist_to_target(state):
        return dist(state[id_pos][0], TARGET)

    INIT = dist(START, TARGET)
    EX.construct_measurable(id_dist, dist_to_target, [INIT, INIT])

    ## value signal for agents LT and RT
    # $id_sig$ has already been registered

    # signal scales with distance to target
    rescaling = lambda r: int(r!=0)
    def sig(state):
        return rescaling(state[id_dist][0])

    # initial value for signal:
    INIT = rescaling(dist(START, TARGET))
    # construct the motivational signal
    EX.construct_measurable(id_sig, sig, [INIT, INIT])

    def mot(state):
        return rescaling(state[id_dist][0])-rescaling(state[id_dist][1])<0 or state[id_dist][0]==0
    EX.construct_sensor(id_nav,mot,[False,False])
    RT.add_sensor(id_nav)
    LT.add_sensor(id_nav)

    # -------------------------------------init--------------------------------------------

    for agent_name in EX._AGENTS:
        EX._AGENTS[agent_name].init()

    # ONE UPDATE CYCLE (without action) TO "FILL" THE STATE DEQUES
    EX.update_state([cid_rt, cid_lt])

    #client data objects for the experiment
    UMACD={}
    for agent_id in EX._AGENTS:
        for token in ['plus','minus']:
            UMACD[(agent_id,token)]=UMAClientData(EX._EXPERIMENT_ID,agent_id,token,EX._service)
    # ASSIGN TARGET IF NOT AUTOMATED:
    if MOTION_PARAMS['AutoTarg']:
        pass
    else:
        # SET ARTIFICIAL TARGET ONCE AND FOR ALL
        for agent in [RT,LT]:
            for token in ['plus','minus']:
                tmp_target=agent.generate_signal([id_nav],token).value().tolist()
                UMACD[(agent._ID,token)].setTarget(tmp_target)

        # ANOTHER UPDATE CYCLE (without action)
        EX.update_state([cid_rt,cid_lt])   


    # INTRODUCE DELAYED BEACON SENSORS:
    for agent in [RT, LT]:
        for token in ['plus', 'minus']:
            delay_sigs = [agent.generate_signal(['x'+str(ind)+'_'+str(wid)],token) for ind in xrange(X_BOUND) for wid in xrange(1,BEACON_WIDTH)]
            agent.delay(delay_sigs, token)


    # -------------------------------------RUN--------------------------------------------
    recorder=experiment_output(EX,run_params)

    ## Random walk period
    while EX.this_state(id_count) < BURN_IN_CYCLES:
        # update the state
        instruction=[(id_lt if rnd(2) else cid_lt),(id_rt if rnd(2) else cid_rt)]
        #instruction = [(id_lt if (EX.this_state(id_count) / X_BOUND) % 2 == 0 else cid_lt),
                       #(id_rt if (EX.this_state(id_count) / X_BOUND) % 2 == 1 else cid_rt)]
        EX.update_state(instruction)
        recorder.record()

    ## Main loop
    while EX.this_state(id_count) < TOTAL_CYCLES:
        # make decisions, update the state
        EX.update_state()
        recorder.record()

    recorder.close()

    #print "%s is done!\n" % test_name


if __name__ == "__main__":
    RUN_PARAMS={
        'env_length':int(sys.argv[1]),
        'total_cycles':int(sys.argv[3]),
        'burn_in_cycles':int(sys.argv[2]),
        'name':sys.argv[4],
        'ex_dataQ':False,
        'agent_dataQ':False,
        'mids_to_record':['count','dist','sig'],
        'Nruns':1,
        'beacon_width':3,
        }
    
    DIRECTORY=".\\"+RUN_PARAMS['name']
    TEST_NAME=RUN_PARAMS['name']+'_0'
    
    os.mkdir(DIRECTORY)
    preamblef=open(DIRECTORY+"\\"+RUN_PARAMS['name']+'.pre','wb')
    cPickle.dump(RUN_PARAMS,preamblef)
    preamblef.close()
        
    start_experiment(RUN_PARAMS,TEST_NAME)
