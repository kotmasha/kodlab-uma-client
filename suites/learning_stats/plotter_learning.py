from __future__ import division
import sys
import json
import numpy as np
import matplotlib as mpl
import os
mpl.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib import cm
import matplotlib.animation as animation


#--------------------------------------------------------------------------------------
# This plotter assumes the presence of the following data file structure:
#
# - All output files are located inside a subdir of the working dir named <name>
#
# - The subdir <name> contains a preamble file named "name.pre"
#
# - Each run is recorded in a data file named "name_i.dat", where $i$ is the run index
#
# - The preamble format is a Python DICT with the following standard keys:
#   'Nruns'             -   the number of runs recorded in this directory
#   'name'              -   the string identifier <name>
#   'ex_dataQ'          -   Boolean indicating whether or not experiment update cycle
#                           data was recorded in addition to the experiment state
#   'agent_dataQ'       -   Boolean indicating whether or not per-agent update cycle
#                           data was recorded in addition to the experiment state
#   'mids_to_record'    -   List of mids (belonging to the experiment) whose values
#                           were recorded (for each cycle of each run)
#
# - Additional preamble values are experiment-dependent.
#   For SNIFFY, we have:
#   'env_length'        -   The size of SNIFFY's environment
#   'burn_in_cycles'    -   Length (in cycles) of initial period of randomized behavior
#   'total_cycles'      -   Length (in cycles) of the whole run   
#--------------------------------------------------------------------------------------

def get_pickles(infile):
    for item in infile:
        yield json.loads(item)

def compi(x):
    if type(x)==type(0):
        return x+1 if x%2==0 else x-1
    else:
        raise Exception('Input to \"compi\" must be an integer! \n')

def fcomp(x):
    #assuming x is a footprint and an np.array:
    return 1-x

def convert_implications(matr):
    L=len(matr)
    for i in range(L):
        for j in range(L):
            if j >= len(matr[i]):
                matr[i].append(matr[compi(j)][compi(i)])

    return np.matrix(matr,dtype=int)

def ellone(x,y):
    #assuming x,y are np arrays of the same shape, 
    #return the ell-1 distance between them:
    return np.sum(np.abs(x-y))


#
# Read the preamble (GENERIC)
#

NAME=sys.argv[1]

preamble_file_name = os.path.join(NAME, NAME+".pre")
preamblef=open(preamble_file_name,'rb')
preamble=json.load(preamblef)
preamblef.close()

RUN_NAME=lambda i: NAME+"_"+str(i)
input_file_name=lambda i: os.path.join(NAME, RUN_NAME(i) + ".dat")
supp_file_name=lambda i: os.path.join(NAME, RUN_NAME(i) + ".sup")
NRUNS=preamble['Nruns']


#
# Open the data files (GENERIC)
#

input_file={}
for ind in xrange(NRUNS):
    input_file[ind]=open(input_file_name(ind),'rb')

supp_file={}
for ind in xrange(NRUNS):
    supp_file[ind]=open(supp_file_name(ind),'rb')


#
# Prepare data entries (GENERIC)
#

DATA={}

#- prepare entries for experiment measurables
if preamble['mids_recorded'] is []:
    pass
else:
    for mid in preamble['mids_recorded']:
        DATA[mid]=[[] for ind in xrange(NRUNS)]

#- prepare entries for update cycle reports
if bool(preamble['ex_dataQ']):
    for mid in preamble['ex_data_recorded']:
        DATA[mid]=[[] for ind in xrange(NRUNS)]

#- prepare entries for per-agent update cycle reports
if bool(preamble['agent_dataQ']):
    for mid in preamble['agent_data_recorded']:
        for agent_id in preamble['agents']:
            DATA[(agent_id,mid)]=[[] for ind in xrange(NRUNS)]


#
# Read the data from the .dat files (GENERIC)
#
SUPP={}
for ind in xrange(NRUNS):
    #load data from the supplementary files:
    SUPP[ind]=json.loads(supp_file[ind].readline())  

    #load data from the data files:
    for record in get_pickles(input_file[ind]):
        #- read entries for experiment measurables        
        if preamble['mids_recorded'] is []:
            pass
        else:
            for mid,item in zip(preamble['mids_recorded'],record['mids_recorded']):
                DATA[mid][ind].append(item)
        #- read entries for experiment update cycle data
        if bool(preamble['ex_dataQ']):    
            for tag,item in zip(preamble['ex_data_recorded'],record['ex_data_recorded']):
                DATA[tag][ind].append(item)
        #- read entries for experiment update cycle data        
        if bool(preamble['agent_dataQ']):
            for agent_id in preamble['agents']:
                for tag,item in zip(preamble['agent_data_recorded'],record['agent_data_recorded'][agent_id]):
                    DATA[(agent_id,tag)][ind].append(item)

# close the data & supplementary files:
for ind in xrange(NRUNS):
    input_file[ind].close()
    supp_file[ind].close()


#------------------------------------------------------------------------------------
# At this point, each DATA[tag] item is a 2-dim Python list object,
# with the tags taking the form of:
# - an experiment measurable id;
# - a measurement tag from the update cycle (time stamp, decision, etc.);
# - a double tag of the form (agent_id,tag) indicating an agent-specific measurement
#   from that agent's update cycle.
#
# From this point on, all instructions are specific to the experiment at hand
#------------------------------------------------------------------------------------

#
# Prepare the plots (EXPERIMENT-SPECIFIC)
#

#Construct implications matrices for each run
GROUND_IMP=[]
IMPS=[]
DIVS=[]
for ind in xrange(NRUNS):
    FP=[np.array(item) for item in SUPP[ind]['footprints']] #for each run, load its sensor footprints
    VM=np.array(SUPP[ind]['values']) #for each run, load the values of each position
    L=len(FP) #the number of footprint vectors

    if preamble['SnapType']=='qualitative':
        #qualitative implications among the footprints:
        lookup_val=lambda x,y: np.PINF if not sum(x*y) else np.extract(x*y,VM).min()
        imp_check=lambda x,y: lookup_val(x,fcomp(y))>max(lookup_val(x,y),lookup_val(fcomp(x),fcomp(y)))
    else:
        #standard implications (inclusions) among footprints:
        imp_check=lambda x,y: all(x<=y)


    #ground truth implications:
    GROUND_IMP.append(np.matrix([[imp_check(FP[xind],FP[yind]) for xind in xrange(L)] for yind in xrange(L)],dtype=int))
    #construct implications from observer agent's "minus" snapshot:
    run_imps=[]
    run_divs=[]
    for t in xrange(len(DATA['counter'][ind])):
        tmp_matr=convert_implications(DATA[('obs','implications')][ind][t]['minus'][:L:])
        run_imps.append(tmp_matr)
        run_divs.append(ellone(tmp_matr,GROUND_IMP[ind]))
    IMPS.append(run_imps)
    DIVS.append(run_divs)

#for ind in xrange(NRUNS):
#    print SUPP[ind]['footprints']
#    print GROUND_IMP[ind]
#exit(0)

#Prepare the axes
fig,ax=plt.subplots()
#my_img=ax.imshow(GROUND_IMP[0], cmap = 'Spectral', vmin = 0, vmax = 1)
#
#def plot_implications(matr):
#    my_img.set_data(matr)
#
#anim = animation.FuncAnimation(
#    fig=imps_fig,
#    func=plot_implications,
#    #init_func=animation_init,
#    frames=IMPS[1],
#    repeat=False,
#    save_count=preamble['total_cycles'],
#    interval=50,
#    )
#
#plt.show()
#anim.save('out.gif',writer='imagemagick')

#THE REAL THING
#exit(0)
plt.subplots_adjust(left=0.05,right=0.95,bottom=0.1,top=0.9)
fig.suptitle('Sniffy: l1-distance of the implication record to the ground truth\n as a function of time during training by random exploration',fontsize=22)
plt.xlabel('time elapsed (cycles)',fontsize=16)
plt.ylabel('l1-distance to ground truth implication matrix',fontsize=16)

#Form the plots
t=np.array(DATA['counter'][0])
dmean=np.mean(np.array(DIVS),axis=0)
dstd=np.std(np.array(DIVS),axis=0)

plt.plot(t,dmean,'-r',alpha=1,label='Mean over '+str(NRUNS)+' runs')
plt.fill_between(t,dmean-dstd,dmean+dstd,alpha=0.2,color='r',label='std. deviation over '+str(NRUNS)+' runs')
ymin,ymax=plt.ylim()
plt.plot([preamble['burn_in_cycles'],preamble['burn_in_cycles']],[ymin,ymax],'-bo',label='training period ends')
ax.legend()

#Show the plots
plt.show()