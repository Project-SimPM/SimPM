import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir) 

from pmpy.des import *

'''
testing priority resources
'''

def p1(env,a,R):
    print('e1 want to get 3 at time:', env.now)
    yield a.get(R,3,1)
    print('e1 got 3 at time:', env.now)

def p2(env,b,R):
    print('e2 want to get 2 at time:', env.now)
    yield b.get(R,2,2)
    print('e2 got 2 at time:', env.now)

def p3(env,b,R):
    yield b.do('wait',1)
    print('e3 want to get 2 at time:', env.now)
    yield b.get(R,2,-3)
    print('e3 got 2 at time:', env.now)

def pr(env,d,R):
    yield d.do('wait',3)
    yield d.add(R,3)
    yield d.do('wait',3)
    yield d.add(R,2)
    yield d.do('wait',2)
    yield d.add(R,3)
    
env=environment()
e1=entity(env,'e1')
e2=entity(env,'e2')
e3=entity(env,'e3')
er=entity(env,'er')
R=priority_resource(env,'Truck',init=0,capacity=3,print_actions=True)
env.process(p1(env,e1,R))
env.process(p2(env,e2,R))
env.process(pr(env,er,R))
env.process(p3(env,e3,R))

env.run()
