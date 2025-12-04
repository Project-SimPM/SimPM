import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir) 
'''
Canceling a request for a resource to model "OR" for getting resources

'''
import simpm
from simpm.des import *

def p1(a:Entity,R2,R):
    
    yield a.get(R,2)|a.get(R2,3)

    if a.not_pending(R,2): #a got R
        a.cancel(R2,3)
        yield a.do('do something using R',10)
        yield a.put(R)
    elif a.not_pending(R2,3): #using R2
        a.cancel(R,2)
        yield a.do('something using R2',5)
        yield a.put(R2)
   
            
        
def p2(b,R):
    yield b.do('wait',3)
    yield b.add(R,3)

    
env=Environment()
e1=Entity(env,'e1',print_actions=True)
e2=Entity(env,'e2',print_actions=True)
R=PriorityResource(env,'Truck1',init=0,print_actions=True)
R2=PriorityResource(env,'Truck2',print_actions=True)
env.process(p1(e1,R2,R))
env.process(p2(e2,R))

simpm.run(env, dashboard="post")
