"""
@author: naimeh Sadeghi
"""
import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir) 
import simpm
from simpm.des import *
'''
testing preemptive resources
this is not working yet
'''

def p1(a:Entity,R):

    yield a.get(R,1,False)
    yield a.interruptive_do('something',10)
    yield a.put(R)
    

def p2(b,R):
    yield b.do('b_act',5)

    r=b.get(R,priority=-1,preempt=True)
    yield r
    print("interrupted")
    yield b.do('b_act2',5)
    yield b.put(R)

    
    
env=Environment()
e1=Entity(env,'e1',print_actions=True)
e2=Entity(env,'e2',print_actions=True)
R=PreemptiveResource(env,'Truck',print_actions=True)
env.process(p1(e1,R))
env.process(p2(e2,R))

simpm.run(env, dashboard=True)
