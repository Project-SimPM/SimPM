import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir) 

import simpm.des as d
import simpm.dist as dist

'''
earthmoving example with repair
'''
def truckProcess(e,loader,ddirt,workedHours):
    while True:
        yield e.get(loader,1,2)
        yield e.do('load',e.loadingDur)
        yield e.add(workedHours,e.loadingDur)

        yield e.put(loader,1)

        yield e.do('haul',e.haulingDur)
        yield e.do('dump',e.DumpingDur)
        yield e.add(ddirt,e.capacity)
        yield e.do('return',8)

def repairPorcess(e,loader,workedHours):
    while True:
        yield e.get(workedHours,10)
        yield e.get(loader,1,-3)
        yield e.do('repair',10)
        yield e.put(loader,1)
        


env=d.Environment()
loader=d.PriorityResource(env,'loader',init=1,print_actions=True)
dumpeddirt=d.Resource(env,'dirt',init=0,capacity=2000)
workedHours=d.Resource(env,'workedHours',init=0,capacity=2000,print_actions=True)

truckent=d.Entity(env,'smallTruck',print_actions=True)
truckent.loadingDur=dist.uniform(4,5)
truckent.haulingDur=dist.uniform(10,14)
truckent.DumpingDur=4
truckent.capacity=80

truckent2=d.Entity(env,'bigTruck',print_actions=True)
truckent2.loadingDur=dist.uniform(4,7)
truckent2.haulingDur=dist.uniform(12,16)
truckent2.DumpingDur=5
truckent2.capacity=100

repairman=d.Entity(env,'repair man',print_actions=False)

env.process(truckProcess(truckent,loader,dumpeddirt,workedHours))
env.process(truckProcess(truckent2,loader,dumpeddirt,workedHours))
env.process(repairPorcess(repairman,loader,workedHours))

env.run()
print(env.now)
