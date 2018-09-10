import numpy as np
from numpy.random import randint as rnd
from collections import deque
#import curses
import time
from UMA.som2_noEP import *
import sys
import os
import json
from client.UMARest import *

def start_experiment(run_params):
    # System parameters
    test_name=run_params['test_name']
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
    Variation=run_params['Variation'] #snapshot type variation to be used ('uniform' or 'value-based')

    # Parameters
    X_BOUND = run_params['env_length']  # no. of edges in discrete interval = no. of GPS sensors
    try:
        Discount=float(run_params['discount']) #discount coefficient, if any
    except KeyError:
        Discount=0.875
    try:
        Threshold=float(run_params['threshold']) #implication threshold, defaulting to the square of the probability of a single position.
    except KeyError:
        Threshold=1./pow(X_BOUND+1.,2)

    # Environment description
    def in_bounds(pos):
        return (pos >= 0 and pos <= X_BOUND)
    def dist(p, q):
        return abs(p - q) #distance between two points in environment

    # agent parameters according to .yml file

    MOTION_PARAMS = {
        'type': SnapType,
        'AutoTarg': AutoTarg,
        'discount': Discount,
        'threshold': Threshold,
    }

    # register basic motion agents;
    # - $True$ tag means they will be marked as dependent (on other agents)
    id_rt, cid_rt = EX.register_sensor('rt')
    id_lt, cid_lt = EX.register_sensor('lt')
    #Register "observer" agent:
    #  This agent remains inactive throghout the experiment, in order to record 
    #  all the UNCONDITIONAL implications among the initial sensors (in its 'minus'
    #  snapshot).
    #  For this purpose, each sensor's FOOTPRINT in the state space (positions in
    #  the interval) is recorded, so that implications may be calaculated according
    #  to the inclusions among footprints.
    id_obs,cid_obs=EX.register_sensor('obs')

    # register motivation for motion agents
    # - this one is NOT dependent on agents except through the position, so
    #   it carries the default "decdep=False" tag.
    id_dist = EX.register('dist')
    # Value signals for different setups determined as a *function* of distance to target
    id_sig = EX.register('sig')
    # ...which function? THIS function (see $rescaling$ below):
    RESCALING={
        'qualitative':{
            'uniform': lambda r: r,
            'value-based': lambda r: r,
            },
        'discounted':{
            'uniform': lambda r: 1,
            'value-based': lambda r: pow(1.-Discount,r-X_BOUND),
            },
        'empirical':{
            'uniform': lambda r: 1,
            'value-based': lambda r: X_BOUND+1-r,
            },
        }
    rescaling=RESCALING[SnapType][Variation]

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

    # OBSERVER agent simply collects implications among the assigned sensors, always inactive
    def action_OBS(state):
        return False
    OBS = EX.construct_agent(id_obs,id_sig,action_OBS,MOTION_PARAMS)
    
    #
    ### "mapping" system
    #

    ## introduce agent's position

    # select starting position
    START = rnd(X_BOUND + 1)

    # effect of motion on position
    id_pos = EX.register('pos')

    def motion(state):
        triggers = {id_rt: 1, id_lt: -1}
        diff = 0
        for t in triggers:
            diff += triggers[t] * int(state[t][0])
        newpos = state[id_pos][0] + diff
        if in_bounds(newpos):
            return newpos
        else:
            return state[id_pos][0]

    EX.construct_measurable(id_pos, motion, [START, START])

    # generate target position
    TARGET = START
    while dist(TARGET, START)==0:
        TARGET = rnd(X_BOUND+1)

    # set up position sensors
    def xsensor(footprint):  # along x-axis
        return lambda state: bool(footprint[state[id_pos][0]])
    def make_footprint():
        return [rnd(2) for ind in xrange(X_BOUND+1)]

    #generate randomized position sensors and record their semantics
    FOOTPRINTS=[]
    all_comp=lambda x: [1-t for t in x]
    for ind in xrange(X_BOUND):
        tmp_name = 'x' + str(ind)
        tmp_footprint=make_footprint()
        FOOTPRINTS.append(tmp_footprint)
        FOOTPRINTS.append(all_comp(tmp_footprint))
        id_tmp, id_tmpc = EX.register_sensor(tmp_name)
        EX.construct_sensor(id_tmp,xsensor(tmp_footprint))
        RT.add_sensor(id_tmp)
        LT.add_sensor(id_tmp)
        OBS.add_sensor(id_tmp)

    # distance to target
    # - $id_distM$ has already been registerd
    def dist_to_target(state):
        return dist(state[id_pos][0], TARGET)
    INIT = dist(START, TARGET)
    EX.construct_measurable(id_dist, dist_to_target, [INIT, INIT])

    #
    ### MOTIVATIONS
    #

    #construct the motivational signal for agents RT,LT and OBS:
    def sig(state):
        return rescaling(state[id_dist][0])
    INIT = rescaling(dist(START,TARGET))
    EX.construct_measurable(id_sig, sig, [INIT, INIT])

    #record the value at each position
    VALUES=[rescaling(dist(ind,TARGET)) for ind in xrange(X_BOUND+1)]


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
    QUERY_IDS={agent_id:{} for agent_id in EX._AGENTS}
    for agent_id in EX._AGENTS:
        for token in ['plus', 'minus']:
            delay_sigs = [EX._AGENTS[agent_id].generate_signal(['x' + str(ind)], token) for ind in xrange(X_BOUND)]
            EX._AGENTS[agent_id].delay(delay_sigs, token)
            QUERY_IDS[agent_id][token]=EX._AGENTS[agent_id].make_sensor_labels(token)

    # START RECORDING
    EX.update_state([cid_lt,cid_rt,cid_obs])
    recorder=experiment_output(EX,run_params)
    recorder.addendum('footprints',FOOTPRINTS)
    recorder.addendum('query_ids',QUERY_IDS)
    recorder.addendum('values',VALUES)

    # -------------------------------------RUN--------------------------------------------

    ## Random walk period
    while EX.this_state(id_count) <= BURN_IN_CYCLES:
        # update the state
        instruction=[
            (id_lt if rnd(2) else cid_lt),  #random instruction for LT
            (id_rt if rnd(2) else cid_rt),  #random instruction for RT
            cid_obs,                           #OBS should always be inactive
            ]
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
