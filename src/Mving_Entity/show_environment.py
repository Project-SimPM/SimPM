import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir) 
import pmpy.MovingEntity as MovingEntity

import matplotlib.pyplot as plt



def f(a:MovingEntity.agent):
    yield a.move("1",a.attr["speed"],[(.5,20)])



env=MovingEntity.Environment((-10,100),(0,100))
atype=MovingEntity.agent_type("a",'o')
btype=MovingEntity.agent_type("b",'^')
a0=MovingEntity.agent(env,atype,(10,10))
a0.attr["speed"]=1
a1=MovingEntity.agent(env,btype,(50,10))
a1.attr["speed"]=.1
a2=MovingEntity.agent(env,btype,(50,40))
a2.attr["speed"]=.5
a3=MovingEntity.agent(env,btype,(30,10))
a3.attr["speed"]=.3
env.process(f(a1))
env.process(f(a2))
env.process(f(a3))
env.process(f(a0))
env.run()
