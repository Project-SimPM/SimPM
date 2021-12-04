from des import *
'''
Canceling a request for a resource to model "OR" for getting resources

'''

def p1(a:entity,R2,R):
    
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

    
env=environment()
e1=entity(env,'e1',print_actions=True)
e2=entity(env,'e2',print_actions=True)
R=priority_resource(env,'Truck1',init=0,print_actions=True)
R2=priority_resource(env,'Truck2',print_actions=True)
env.process(p1(e1,R2,R))
env.process(p2(e2,R))

env.run()
