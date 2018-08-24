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
    test_name=run_params['name']
    host = run_params['host']
    port = run_params['port']

    # initialize a new experiment
    EX = Experiment(test_name, UMARestService(host, port))
    id_dec = 'decision'
    id_count= 'counter'

    # Recording options:
    record_mids=run_params['mids_to_record'] #[id_count,id_dist,id_sig]
    record_global=run_params['ex_dataQ'] #True
    record_agents=run_params['agent_dataQ'] #True
    #recorder will be initialized later, at the end of the initialization phase,
    #to enable collection of all available data tags

    # Decision cycles:
    TOTAL_CYCLES = run_params['total_cycles']
    BURN_IN_CYCLES = run_params['burn_in_cycles']
    # Parameters and definitions
    AutoTarg=bool(run_params['AutoTarg'])
    SnapType=run_params['SnapType']
    try:
        Discount=float(run_params['discount'])
    except KeyError:
        Discount=None

    # Environment
    X_BOUND = run_params['env_length']  # length
    BEACON_WIDTH = run_params['beacon_width']

    # distance function
    def dist(p, q):
        return min(abs(p-q),X_BOUND-abs(p-q))

    # "Qualitative" agent parameters

    MOTION_PARAMS = {
        'type': SnapType,
        'AutoTarg': AutoTarg,
        'discount': Discount,
    }

    # register basic motion agents;
    # - $True$ tag means they will be marked as dependent (on other agents)
    id_rt, cid_rt = EX.register_sensor('rt')
    id_lt, cid_lt = EX.register_sensor('lt')
    id_obs,cid_obs=EX.register_sensor('obs')

    # register motivation for motion agents
    # - this one is NOT dependent on agents except through the position, so
    #   it carries the default False tag.
    id_at_targ, cid_at_targ = EX.register_sensor('atT')
    id_dist = EX.register('dist')
    id_sig = EX.register('sig')
    id_sig_freq = EX.register('freq')
    id_nav, cid_nav = EX.register_sensor('nav')

    # register arbiter variable whose purpose is provide a hard-wired response to a conflict
    # between agents 'lt' and 'rt'.
    id_arbiter = EX.register('ar')

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

    # OBSERVER agent simply collects implications among the assigned sensors, always active
    def action_OBS(state):
        return True
    OBS = EX.construct_agent(id_obs,id_sig_freq,action_OBS,MOTION_PARAMS) 

    #
    ### "mapping" system
    #

    ## introduce agent's position

    # select starting position
    START = 0

    # effect of motion on position
    id_pos = EX.register('pos')

    def motion(state):
        triggers = {id_rt: 1, id_lt: -1}
        diff = 0
        for t in triggers:
            diff += triggers[t] * int(state[t][0])
        return (state[id_pos][0] + diff) % X_BOUND
        
    EX.construct_measurable(id_pos, motion, [START, START])

    # generate target position
    TARGET = X_BOUND/8+rnd((7*X_BOUND)/8)

    # set up position sensors
    def xsensor(m,delta):  # along x-axis
        return lambda state: dist(state[id_pos][0],m)<=delta

    for ind in xrange(X_BOUND):
        tmp_name = 'x' + str(ind)
        id_tmp, id_tmpc = EX.register_sensor(tmp_name)  # registers the sensor pairs
        EX.construct_sensor(id_tmp, xsensor(ind,BEACON_WIDTH))  # constructs the measurables associated with the sensor
        RT.add_sensor(id_tmp)
        LT.add_sensor(id_tmp)
        OBS.add_sensor(id_tmp)

    # record the semantics of the position sensors:
    FOOTPRINTS={}
    for ind in xrange(X_BOUND):
        FOOTPRINTS['x'+str(ind)]=[0 for pos in xrange(X_BOUND)]
        for pos in xrange(X_BOUND):
            FOOTPRINTS['x'+str(ind)][pos]+=xsensor(ind,BEACON_WIDTH)({id_pos:[pos]})

    # distance to target
    # - $id_distM$ has already been registerd
    def dist_to_target(state):
        return dist(state[id_pos][0], TARGET)

    INIT = dist(START, TARGET)
    EX.construct_measurable(id_dist, dist_to_target, [INIT, INIT])

    #
    ### MOTIVATIONS
    #
    def sig_freq(state):
        return 1.
    EX.construct_measurable(id_sig_freq,sig_freq,[1.,1.])

    ## value signal for agents LT and RT
    # signal scales with distance to target
    if SnapType=='qualitative':
        rescaling = lambda r: r
    else:
        #SnapType is default
        rescaling = lambda r: pow(1.-Discount,r-X_BOUND)

    def sig(state):
        return rescaling(state[id_dist][0])
        # initial value for signal:

    INIT = rescaling(dist(START, TARGET))
    # construct the motivational signal
    EX.construct_measurable(id_sig, sig, [INIT, INIT])

    if MOTION_PARAMS['AutoTarg']:
        # if auto-targeting mode is on, do nothing
        pass
    else:
        # otherwise, construct and assign the nav sensor
        if SnapType=='qualitative':
            def nav(state):
                return state[id_sig][0]<state[id_sig][1] or state[id_dist][0]==0
        else:
            def nav(state):
                return state[id_sig][0]>state[id_sig][1] or state[id_dist][0]==0
        EX.construct_sensor(id_nav,nav,[False,False])
        # Add nav sensor to agents
        RT.add_sensor(id_nav)
        LT.add_sensor(id_nav)
        OBS.add_sensor(id_nav)

    # -------------------------------------init--------------------------------------------

    for agent_name in EX._AGENTS:
        EX._AGENTS[agent_name].init()

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
        for agent_id in EX._AGENTS:
            for token in ['plus','minus']:
                tmp_target=EX._AGENTS[agent_id].generate_signal([id_nav],token).value().tolist()
                UMACD[(agent_id,token)].setTarget(tmp_target)

    # INTRODUCE DELAYED GPS SENSORS:
    for agent_id in EX._AGENTS:
        for token in ['plus', 'minus']:
            delay_sigs = [EX._AGENTS[agent_id].generate_signal(['x' + str(ind)], token) for ind in xrange(X_BOUND)]
            EX._AGENTS[agent_id].delay(delay_sigs, token)

    # START RECORDING
    EX.update_state([cid_lt,cid_rt,id_obs])
    recorder=experiment_output(EX,run_params)
    recorder.addendum('footprints',FOOTPRINTS)


    # -------------------------------------RUN--------------------------------------------

    ## Random walk period
    while EX.this_state(id_count) <= BURN_IN_CYCLES:
        # update the state
        instruction=[
            (id_lt if rnd(2) else cid_lt),  #random instruction for LT
            (id_rt if rnd(2) else cid_rt),  #random instruction for RT
            id_obs,                           #OBS should always be active
            ]
        #instruction = [(id_lt if (EX.this_state(id_count) / X_BOUND) % 2 == 0 else cid_lt),
                       #(id_rt if (EX.this_state(id_count) / X_BOUND) % 2 == 1 else cid_rt)]
        EX.update_state(instruction)
        recorder.record()

    ## Main loop
    while EX.this_state(id_count) <= TOTAL_CYCLES:
        # make decisions, update the state
        EX.update_state()
        recorder.record()

    # Wrap up and collect garbage
    recorder.close()
    EX.remove_experiment()


if __name__ == "__main__":
    RUN_PARAMS={
        'AutoTarg':True,
        'SnapType':'qualitative',
        'env_length':int(sys.argv[1]),
        'beacon_width':2,
        'total_cycles':int(sys.argv[3]),
        'burn_in_cycles':int(sys.argv[2]),
        'name':sys.argv[4],
        'ex_dataQ':True,
        'agent_dataQ':True,
        'mids_to_record':['counter','dist','sig'],
        'Nruns':1,
        'host':'localhost',
        'port':8000,
        }
    
    DIRECTORY=os.path.join(os.getcwd(),RUN_PARAMS['name'])
    TEST_NAME=RUN_PARAMS['name']+'_0'
    
    try:
        os.mkdir(DIRECTORY)
    except:
        pass
    preamblef=open(os.path.join(DIRECTORY,RUN_PARAMS['name']+'.pre'),'wb')
    json.dump(RUN_PARAMS,preamblef)
    preamblef.close()
        
    start_experiment(RUN_PARAMS)
