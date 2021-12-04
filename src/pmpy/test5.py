from des import *
'''
testing preemptive resources
this is not working yet
'''

def p1(a,R):
    
    yield a.get(R)
    yield a.do('something',10)
    yield a.put(R)

def p2(b,R):
    yield b.do('b_act',5)
    yield b.get(R,priority=-1,preempt=True)
    yield b.do('b_act2',5)
    yield b.put(R)
    
env=environment()
e1=entity(env,'e1',print_actions=True)
e2=entity(env,'e2',print_actions=True)
R=preemptive_resource(env,'Truck',print_actions=True)
env.process(p1(e1,R))
env.process(p2(e2,R))

env.run()
