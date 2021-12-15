import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir) 
import pmpy.abs as abs

def f(a:abs.agent):
    yield a.move("1",.1,[(.5,20)])


env=abs.environment(100,100)
atype=abs.agent_type("a",'o')
btype=abs.agent_type("b",'^')
abs.agent(env,atype,(10,10))
a1=abs.agent(env,btype,(50,10))
a2=abs.agent(env,btype,(50,40))
a3=abs.agent(env,btype,(30,10))
env.process(f(a1))
env.run()
