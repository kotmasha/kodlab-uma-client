import sys
import numpy as np
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib as mpl

from numpy.random import randint as rnd
from copy import deepcopy as cp
from collections import deque



## A more standard rounding operation
def my_round(x):
    return np.floor(x) if  x<np.floor(x)+.5 else np.floor(x+1)

## version of str for signed numbers
def signedstr(x):
        return str(x) if x<0 else '+'+str(x)

## Complex integers class
#  - possibly there is something better, but I couldn't find it
#
class icomplex(object):
    def __init__(self,x,y):
        self.real=int(np.floor(x))
        self.imag=int(np.floor(y))
    
    def __repr__(self):
        return str(self.real)+signedstr(self.imag)+'j'

    def __str__(self):
        return str(self.real)+signedstr(self.imag)+'j'

    def __eq__(self,other):
        return self.real==other.real and self.imag==other.imag
    
    def __ne__(self,other):
        return not self==other

    def __add__(self,z):
        return icomplex(self.real+z.real,self.imag+z.imag)

    def __sub__(self,z):
        return icomplex(self.real-z.real,self.imag-z.imag)

    def __mul__(self,z):
        return icomplex(self.real*z.real-self.imag*z.imag,self.real*z.imag+self.imag*z.real)
    
    def conj(self):
        return icomplex(self.real,-self.imag)

    def __abs__(self):
        return (self*self.conj()).real

    def __complex__(self):
        return complex(self.real,self.imag)

    def __floordiv__(self,scale): # $scale$ must be a non-zero integer
        return icomplex(self.real / scale,self.imag / scale)

    def __mod__(self,scale): # $scale$ must be a non-zero integer
        return icomplex(self.real % scale,self.imag % scale)

    def pow(self,x):
        if isinstance(x,int):
            if x==0:
                return 1
            elif x>0:
                return self*pow(self,x-1)
            else:
                raise Exception('Complex integer has only non-negative integer powers.')
        else:
            raise Exception('Complex integer has only non-negative integer powers.')
 
    def convert(self):
        return complex(self.real,self.imag)

    def strip(self):
        return (self.real,self.imag)

#Global Variables
North=icomplex(0,1)
South=icomplex(0,-1)
West=icomplex(-1,0)
East=icomplex(1,0)
Origin=icomplex(0,0)
DIRS=[North,East,South,West]

#arena base class
class Arena_base():
    def __init__(self,xbounds, ybounds,out_of_bounds=lambda x:False):
        self._xbounds=xbounds #is a tuple of the form (xmin,xmax), bounds for drawing
        self._ybounds=ybounds #is a tuple of the form (ymin,ymax)
        self._objects={}
        self._oob=out_of_bounds #a function accepting an icomplex position and returning Boolean
        self._map=None
        self._ax=None
        self._fig=None
        self._cheeses = []
        self._misc='0'

    def putmisc(self,txt):
        self._misc=str(txt)

    def inBounds(self, pos):
        if pos.real<self._xbounds[0] or pos.real>=self._xbounds[1] or pos.imag<self._ybounds[0] or pos.imag>=self._ybounds[1]:
            return False
        else:
            return not self._oob(pos)

    def attrCalc(self,pos,attributeName):
        if attributeName.find('Gradient')>=0:
            return sum([self._objects[objtag]._rescaling[attributeName](pos-self._objects[objtag]._pos) for objtag in self._objects])
        return sum([self._objects[objtag]._rescaling[attributeName](abs(self._objects[objtag]._pos-pos)) for objtag in self._objects])

    def elevGradient(self,pos):
        return self.attrCalc(pos,'elevationGradient')

    def addMouse(self,tag,pos,attributes,viewports={}):
        self._objects[tag]=mouse(self,tag,pos,attributes,viewports)
        #self._objects.append(mouse(self,tag,pos,attributes,viewports))

    def addRandomMouse(self,tag,viewsize=5):
        mouseAttr={'viewSize':viewsize}
        mouseViewPort={}
        mouseAttr['direction']=[North,West,South,East][rnd(4)]
        mouse_start_pos = icomplex(rnd(self._xbounds[1]-self._xbounds[0]),rnd(self._ybounds[1]-self._ybounds[0]))
        self.addMouse(tag,mouse_start_pos,mouseAttr,mouseViewPort)

    def addRandomMice(self,how_many,viewsize=5):
        # construct x random mice
        for ind in xrange(how_many):
            self.addRandomMouse('mus'+str(ind+1),viewsize)

    def addCheese(self,tag,pos,params):
        self._objects[tag]=cheese(self,tag,pos,params)
        #self._objects.append(cheese(self,tag,pos,params,attributes))

    def addRandomCheese(self,ind,params):
        self.addCheese(
            'ch'+str(ind),
            icomplex(rnd(self._xbounds[1]-self._xbounds[0]),rnd(self._ybounds[1]-self._ybounds[0])),
            params
            )
    
    def addRandomCheeses(self,how_many,params):
        for ind in xrange(how_many):
            self.addRandomCheese(ind+1,params)

    def getMaxElev(self):
        maximum = 0
        for i in self._map:
            for j in i:
                maximum = max(maximum,j)
        return maximum

    def getMice(self,tag='all'):
        if tag=='all':
            tmpMice={}
            for objtag in self._objects.keys():
                if self._objects[objtag]._type=='mouse':
                    tmpMice[tag]=self._objects[objtag]
            return tmpMice
        elif self._objects[tag]._type=='mouse':
            return self._objects[tag]
        else:
            raise Exception('No objects with tag \''+str(tag)+'\' in arena.\n\n')

    def update_objs(self,liszt):
        for objtag in self._objects:
            self._objects[objtag].update(liszt)

    def updatemap(self,attributeName):
        self._map = np.zeros((self._xbounds[1]-self._xbounds[0]+1,self._ybounds[1]-self._ybounds[0]+1))
        for x in xrange (0,self._xbounds[1]-self._xbounds[0]+1):
            for y in xrange (0,self._ybounds[1]-self._xbounds[0]+1):
                self._map[y][x]=self.attrCalc(icomplex(x,y),attributeName)
        
    def generateHeatmap(self,attributeName):
        self._map = np.zeros((self._xbounds[1]-self._xbounds[0]+1,self._ybounds[1]-self._ybounds[0]+1))
        for x in xrange (0,self._xbounds[1]-self._xbounds[0]+1):
            for y in xrange (0,self._ybounds[1]-self._xbounds[0]+1):
                self._map[y][x]=self.attrCalc(icomplex(x,y),attributeName)
        self._fig, self._ax = plt.subplots(1)
        self._fig.suptitle('Mouse experiment, cycle No. '+str(self._misc),fontsize=16)
        self._ax.imshow(self._map, cmap = 'Spectral', vmin = -1, vmax = self.getMaxElev())
        for objtag in self._objects.keys():
            obj=self._objects[objtag]
            if obj._type == 'cheese':
                Circle = plt.Circle((obj._pos.real,obj._pos.imag),0.2,color='w')
                self._cheeses.append(self._ax.add_artist(Circle))
            elif obj._type == 'mouse':
                self._mouse=self._ax.add_patch(patches.Rectangle((obj._pos.real-0.5,obj._pos.imag-0.5),1,1,color=(0.0,0.0,0.0)))
                self._direction=self._ax.arrow(obj._pos.real,obj._pos.imag,obj._attr['direction'].real,obj._attr['direction'].imag,head_width=1,head_length=1.5)
                self._Gradient=self._ax.arrow(obj._pos.real,obj._pos.imag,self.attrCalc(obj._pos,attributeName + 'Gradient').real,self.attrCalc(obj._pos,attributeName + 'Gradient').imag,head_width=1,head_length=1.5,color='r')
            else:
                raise Exception('wrong object type')
        self._ax.invert_yaxis()

    def updateHeatmapFull(self,attributeName):
        self._ax.clear()
        self._map = np.zeros((self._xbounds[1]-self._xbounds[0]+1,self._ybounds[1]-self._ybounds[0]+1))
        for x in xrange (0,self._xbounds[1]-self._xbounds[0]+1):
            for y in xrange (0,self._ybounds[1]-self._xbounds[0]+1):
                self._map[y][x]=self.attrCalc(icomplex(x,y),attributeName)
        self._ax.imshow(self._map, cmap = 'Spectral', vmin = -1, vmax = self.getMaxElev())
        for objtag in self._objects.keys():
            obj=self._objects[objtag]
            if obj._type == 'cheese':
                Circle = plt.Circle((obj._pos.real,obj._pos.imag),0.2,color='w')
                self._ax.add_artist(Circle)
            elif obj._type == 'mouse':
                self._mouse=self._ax.add_patch(patches.Rectangle((obj._pos.real-0.5,obj._pos.imag-0.5),1,1,color=(0.0,0.0,0.0)))
                self._direction=self._ax.arrow(obj._pos.real,obj._pos.imag,obj._attr['direction'].real,obj._attr['direction'].imag,head_width=1,head_length=1.5)
                self._Gradient=self._ax.arrow(obj._pos.real,obj._pos.imag,self.attrCalc(obj._pos,attributeName + 'Gradient').real,self.attrCalc(obj._pos,attributeName + 'Gradient').imag,head_width=1,head_length=1.5,color='r')
            else:
                raise Exception('wrong obj type')
        self._ax.invert_yaxis()

    def updateHeatmap(self,attributeName):
        obj = self.getMice('mus')
        self._mouse.remove()
        self._Gradient.remove()
        self._direction.remove()
        self._fig.suptitle('Mouse experiment, cycle No. '+str(self._misc),fontsize=16)
        self._mouse=self._ax.add_patch(patches.Rectangle((obj._pos.real-0.5,obj._pos.imag-0.5),1,1,color=(0.0,0.0,0.0)))
        self._direction=self._ax.arrow(obj._pos.real,obj._pos.imag,obj._attr['direction'].real,obj._attr['direction'].imag,head_width=1,head_length=1.5)
        self._Gradient=self._ax.arrow(obj._pos.real,obj._pos.imag,self.attrCalc(obj._pos,attributeName + 'Gradient').real,self.attrCalc(obj._pos,attributeName + 'Gradient').imag,head_width=1,head_length=1.5,color='r')
                

#objects placeable in the arena
class obj(object):
    def __init__(self,ar,typ,tag,pos):
        if type(typ)==type('0') and type(tag)==type('0'):
            self._ar=ar
            self._type=typ
            self._tag=tag
            self._rescaling = {
                'elevation': lambda x: 0,
                'elevationGradient':lambda x: 0,
                }
        else:
            raise Exception('Object type and tag must be strings.\n\n')
        if type(pos)==type(Origin):
            self._pos=pos
        else:
            raise Exception('Object position must be of type icomplex')
        self._attr={}

    def update(self,liszt=[False,False,False,False,False]):
        return None

    def remove(self):
        del self._ar._objects[self._tag] #note each object is uniquely represented on the list of objects of an arena.

#mouse class:
class mouse(obj):
    def __init__(self,ar,tag,pos,attributes,viewport={}):
        obj.__init__(self,ar,'mouse',tag,pos)
        self._attr = attributes 
        self._viewport = viewport
        self._dFunc = lambda x: pow(4,1+x.real/abs(x))#direction function, input is a gradient 

    def copy_obj(self,arena):
        return mouse(arena,self._tag,self._pos,self._attr,self._viewport)

    def moveForward(self):
        newp =self._pos + self._attr['direction']
        if newp.real>self._ar._xbounds[1] or newp.real<self._ar._xbounds[0] or newp.imag>self._ar._ybounds[1] or newp.imag<self._ar._ybounds[0]:
            return False
        else:
            self._pos=newp
            return True
    
    def moveBackwards(self):
        newp =self._pos - self._attr['direction']
        if newp.real>self._ar._xbounds[1] or newp.real<self._ar._xbounds[0] or newp.imag>self._ar._ybounds[1] or newp.imag<self._ar._ybounds[0]:
            return False
        else:
            self._pos=newp
            return True

    def turnLeft(self):
        self._attr['direction'] *= North

    def turnRight(self):
        self._attr['direction'] *= South

    def teleport(self,posn,pose):
        # set mouse position, if legal
        if not self._ar._oob(posn):
            self._pos=posn
        else:
            raise Exception('Invalid mouse teleport.\n')
        
        # set mouse pose, if legal
        if pose in [North,South,East,West]:
            self._attr['direction']=pose
        else:
            raise Exception('Invalid mouse teleport.\n')

    def calculate_cos_grad(self,attributeName):
        grad=self._ar.attrCalc(self._pos,attributeName+'Gradient')
        posec=complex(self._attr['direction'].real,-self._attr['direction'].imag)
        return ((grad/abs(grad))*posec).real

    def originViewport(self):#finding the actual arena coordinates of the origin of the mouse's vision
        baseCorner = icomplex(self._attr['viewSize'],self._attr['viewSize'])#the top right corner in the mouse's vision relative to the mouse
        botL = baseCorner*North*self._attr['direction']+self._pos #bottom left corner
        return botL

    def updateViewport(self, attribute): #updates 'Viewport'['smell'] in _attr
        if not(attribute in self._viewport):
            self._viewport[attribute] = np.zeros((self._attr['viewSize']*2+1,self._attr['viewSize']*2+1))
        origin = self.originViewport()
        if self._pos.real>self._attr['viewSize']+self._ar._xbounds[0] and self._pos.real<self._ar._xbounds[1]-self._attr['viewSize']and self._pos.imag>self._attr['viewSize']+self._ar._ybounds[0] and self._pos.imag<self._ar._ybounds[1]-self._attr['viewSize']:#checking if some parts of the viewport are outside of arena, if there are standrdizes them
            for x in xrange (0,self._attr['viewSize']*2+1):
                for y in xrange (0, self._attr['viewSize']*2+1):
                    self._viewport[attribute][y][x]=self._ar.attrCalc(origin+icomplex(x,y)*South*self._attr['direction'],attribute)
        else:
            for x in xrange (0,self._attr['viewSize']*2+1):
                for y in xrange (0, self._attr['viewSize']*2+1):
                    p=origin+icomplex(x,y)*South*self._attr['direction'] #temporeraly saving the coordinates of the point x,y
                    if p.real<self._ar._xbounds[0]or p.real>self._ar._xbounds[1]or p.imag>self._ar._ybounds[1]or p.imag<self._ar._ybounds[0]:
                        self._viewport[attribute][y][x]=-1
                    else:
                        self._viewport[attribute][y][x]=self._ar.attrCalc(p,attribute)
    
    def generateHeatmap(self,attributeName):
        self.updateViewport(attributeName)
        self._figure, self._axes = plt.subplots(1)
        self._axes.imshow(self._viewport[attributeName], cmap = 'Spectral',vmin = -1, vmax = self._ar.getMaxElev())
        self._axes.add_patch(patches.Rectangle((self._attr['viewSize']-0.5,self._attr['viewSize']-0.5),1,1,color=(0.0,0.0,0.0)))
        self._axes.arrow(self._attr['viewSize'],self._attr['viewSize'],0,1,head_width=0.3, head_length=0.6)
        self._axes.arrow(self._attr['viewSize'],self._attr['viewSize'],(self._ar.attrCalc(self._pos,attributeName+'Gradient')*complex(0,1)/self._attr['direction'].convert()).real,(self._ar.attrCalc(self._pos,attributeName+'Gradient')*complex(0,1)/self._attr['direction'].convert()).imag,color='r',head_width=0.3, head_length=0.6)
        self._axes.invert_yaxis()
    
    def updateHeatmapFull(self,attributeName):
        self.updateViewport(attributeName)
        self._axes.clear()
        self._axes.imshow(self._viewport[attributeName], cmap = 'Spectral',vmin = -1, vmax = self._ar.getMaxElev())
        self._axes.add_patch(patches.Rectangle((self._attr['viewSize']-0.5,self._attr['viewSize']-0.5),1,1,color=(0.0,0.0,0.0)))
        self._axes.arrow(self._attr['viewSize'],self._attr['viewSize'],0,1,head_width=0.3, head_length=0.6)
        self._axes.arrow(self._attr['viewSize'],self._attr['viewSize'],(self._ar.attrCalc(self._pos,attributeName+'Gradient')*complex(0,1)/self._attr['direction'].convert()).real,(self._ar.attrCalc(self._pos,attributeName+'Gradient')*complex(0,1)/self._attr['direction'].convert()).imag,color='r',head_width=0.3, head_length=0.6)                                                               
        self._axes.invert_yaxis()  

    def semi_update(self, liszt=[False,False,False,False,False]):#a list of boolean values assigned by the agents (FD, BK, RT, LT , arbTop) 
        new_pos = self._pos
        new_dir = self._attr['direction']
        if liszt[0] and not(liszt[1] or liszt[2] or liszt[3]):
            new_pos = self._pos + self._attr['direction']
        elif liszt[1] and not(liszt[0] or liszt[2] or liszt[3]):
            new_pos = self._pos - self._attr['direction'] 
        elif liszt[2] and not(liszt[1] or liszt[0] or liszt[3]):
            new_dir = self._attr['direction']  * icomplex(0,1)
        elif liszt[3] and not(liszt[1] or liszt[2] or liszt[0]):
            new_dir = self._attr['direction']  * icomplex(0,-1)
        elif liszt[0] and liszt[1]:
            return self.semi_update([False,False,liszt[2],liszt[3],liszt[4]])
        elif liszt[3] and liszt[2]:
            return self.semi_update([liszt[0],liszt[1],False,False,liszt[4]])
        elif ((liszt[0] or liszt[1]) and (liszt[2] or liszt[3])):
            if liszt[4]:
                if liszt[0]:
                    new_pos = self._pos + self._attr['direction']
                else:
                    new_pos = self._pos - self._attr['direction']
            else:
                if liszt[2]:
                    new_dir = self._attr['direction']  * icomplex(0,1)
                else:
                    new_dir = self._attr['direction']  * icomplex(0,-1)
        if self._ar.inBounds(new_pos):
            return new_pos,new_dir
        else:
            return self._pos,self._attr['direction']

    def update(self, liszt=[False,False,False,False,False]):
        new_pos,new_dir = self.semi_update(liszt)
        self._pos = new_pos
        self._attr['direction'] = new_dir                    

                                                   

    #-----------------------------sensors---------------------------------
    
    def gradient(self): #gradient relative to the direction that the mouse is looking
        return self._ar.attrCalc(self._pos,'elevationGradient')/self._attr['direction'].convert()*complex(0,1)

    def elevation(self): #elevation of mouse
        return self._ar.attrCalc(self._pos,'elevation')

    def averageElevation(self): #average elevation of mouse viewport
        Sum=0
        for x in self._viewport['elevation']:
            for y in self._viewport['elevation'][x]:
                Sum+=y
        return Sum/pow(self._attr['viewSize']*2+1,2)

    #------------------------direction senosrs----------------------------  
    def DS(self,ind,direction):
        gradient = self.gradient()/direction.convert()
        return self._dFunc(gradient)>= ind
    
    #-------------------------length sensors----------------------

    def LS(self,ind,direction):
        gradient = self.gradient()/direction.convert()
        return gradient.real>=ind

#cheese class:
class cheese(obj):
    def __init__(self,ar,tag,pos,params = {'nibbles':1,'nibbleDist':1}):
        obj.__init__(self,ar,'cheese',tag,pos)
        self._rescaling['elevation'] = lambda x: 10*np.exp(-x/25)
        self._rescaling['elevationGradient']=lambda x: -10/25*np.exp(-abs(x)/100)*2*complex(x.real,x.imag)
        self._params = params # params is a dictionary of initialization parmeters
        self._attr={'counter':0}
      
    def copy_obj(self,arena):
        return cheese(arena,self._tag,self._pos,self._params)

    def update(self,liszt=[False,False,False,False,False]):
        nibbleP=False
        for objtag in self._ar._objects:
            item=self._ar._objects[objtag]
            if item._type == 'mouse' and np.sqrt(abs(item._pos-self._pos))<=self._params['nibbleDist']:
                nibbleP=True
                break

        if nibbleP:
            self._attr['counter']+=1
        else:
            self._attr['counter']=0

        if self._attr['counter']>=self._params['nibbles']:
            self.remove()

   
    
        
                
def main():
    xbounds = 0 , 40
    ybounds = 0, 40
    arena = Arena_base(xbounds, ybounds, [])
    arena.addRandomCheeses(5)
    arena.addRandomMouse('mus',viewsize=5)
    arena.generateHeatmap('elevation')
    arena._objects['mus'].generateHeatmap('elevation')
    arena._fig.show()
    arena._objects['mus']._figure.show()
    userInput = raw_input("what would you like to do now? w,a,s,d or st to stop")
    mouse = arena.getMice('mus')
    print mouse
    while userInput != 'st':
        lenObj = len(arena._objects.keys())
        if userInput == 'w':
            mouse.moveForward()
        elif userInput == 's':
            mouse.moveBackwards()
        elif userInput == 'a':
            mouse.turnLeft()
        elif userInput == 'd':
            mouse.turnRight()
        for objtag in arena._objects.keys():
            obj=arena._objects[objtag]
            if obj._type == 'cheese':
                obj.update()
        if lenObj> len(arena._objects):
            arena.updateHeatmapFull('elevation')
            lenObj = len(arena._objects)
        else:
            arena.updateHeatmap('elevation')
        mouse.updateHeatmapFull('elevation')
        arena._fig.show()
        mouse._figure.show()
        userInput = raw_input("what would you like to do now? w,a,s,d or st to stop")
        
if __name__=='__main__':
    main()