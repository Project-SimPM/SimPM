import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir) 

import pmpy.des as d
import pmpy.dist as dist

'''
earthmoving example with repair
'''
def truckProcess(e,loader,ddirt,workedHours):
    while True:
        yield e.get(loader,1,2)
        yield e.do('load',e.attr['loadingDur'])        
        yield e.add(workedHours,e.attr['loadingDur'])
       
        yield e.put(loader,1)
        
        yield e.do('haul',e.attr['haulingDur'])
        yield e.do('dump',e.attr['DumpingDur'])
        yield e.add(ddirt,e.attr['capacity'])
        yield e.do('return',8)

def repairPorcess(e,loader,workedHours):
    while True:
        yield e.get(workedHours,10)
        yield e.get(loader,1,-3)
        yield e.do('repair',10)
        yield e.put(loader,1)
        


env=d.environment()
loader=d.priority_resource(env,'loader',init=1,print_actions=True)
dumpeddirt=d.resource(env,'dirt',init=0,capacity=2000)
workedHours=d.resource(env,'workedHours',init=0,capacity=2000,print_actions=True)

truckent=d.entity(env,'smallTruck',print_actions=True)
truckent.attr['loadingDur']=dist.uniform(4,5)
truckent.attr['haulingDur']=dist.uniform(10,14)
truckent.attr['DumpingDur']=4
truckent.attr['capacity']=80

truckent2=d.entity(env,'bigTruck',print_actions=True)
truckent2.attr['loadingDur']=dist.uniform(4,7)
truckent2.attr['haulingDur']=dist.uniform(12,16)
truckent2.attr['DumpingDur']=5
truckent2.attr['capacity']=100

repairman=d.entity(env,'repair man',print_actions=False)

env.process(truckProcess(truckent,loader,dumpeddirt,workedHours))
env.process(truckProcess(truckent2,loader,dumpeddirt,workedHours))
env.process(repairPorcess(repairman,loader,workedHours))

env.run()
print(env.now)
