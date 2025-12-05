#******Earth moving simulation(plus breakdown)******* (meeting #17)
import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir) 

import simpm
import simpm.des as des
import numpy as np
def truck_process(truck: des.Entity,loader_1,loader_2,dumped_dirt):
    while True:
     yield truck.get(loader_1,1,2)|truck.get(loader_2,1,2)
     yield truck.do("wait",0)
     if truck.not_pending(loader_1):
         L=loader_1
         truck.cancel(loader_2,1)
     elif truck.not_pending(loader_2):
         L=loader_2
         truck.cancel(loader_1,1)
     start_load_list.append(env.now)
     yield truck.do("loading",truck.load_dur)
     yield truck.put(L,1)
     yield truck.add(dumped_dirt,truck.capacity)
     start_haul_list.append(env.now)
     yield truck.do("hauling",truck.haul_dur)
     yield truck.do("dumping",truck.dump_dur)
     yield truck.do("returning",truck.return_dur)
     if dumped_dirt.level()>10000:
         break

def loader_breakdown_proc(repair_man,loader):
    while True:
        yield repair_man.do("wait",loader.time_betwin_break)
        yield repair_man.get(loader,1,1)
        yield repair_man.do("repairing",loader.time_to_fix)
        yield repair_man.put(loader,1)
        
        

env=des.Environment()
dumped_dirt=des.Resource(env,"dumped_dirt",init=0,capacity=150000)
start_load_list=[]
start_haul_list=[]
large_trucks=[]
small_trucks=[]
loader_1=des.PriorityResource(env,"Loader1",1,print_actions=True)
loader_1.time_betwin_break=500
loader_1.time_to_fix=20
loader_2=des.PriorityResource(env,"Loader2",1,print_actions=True)
loader_2.time_betwin_break=600
loader_2.time_to_fix=25
for i in range(4):
    large_trucks.append(des.Entity(env,"truck"))
    large_trucks[i].capacity=20
    large_trucks[i].load_dur=5
    large_trucks[i].haul_dur=35
    large_trucks[i].dump_dur=2
    large_trucks[i].return_dur=20
    p=env.process(truck_process(large_trucks[i],loader_1,loader_2,dumped_dirt))
for i in range(3):
    small_trucks.append(des.Entity(env,"truck"))
    small_trucks[i].capacity=15
    small_trucks[i].load_dur=3
    small_trucks[i].haul_dur=25
    small_trucks[i].dump_dur=1.5
    small_trucks[i].return_dur=13
    env.process(truck_process(small_trucks[i],loader_1,loader_2,dumped_dirt))


repair_man=des.Entity(env,"repair_man",print_actions=True)
env.process(loader_breakdown_proc(repair_man,loader_1))
env.process(loader_breakdown_proc(repair_man,loader_2))
simpm.run(env, dashboard=True, until=p)
production_rate=(dumped_dirt.level()/env.now)
print("Production Rate is:",production_rate,"m3/minute")
l2=np.array(start_load_list)
l1=np.array(start_haul_list)
loader_utilization_time=l1-l2
loader_utilization_sum=(sum(loader_utilization_time))
loader_utilization=(loader_utilization_sum/env.now)
print("Loader Utilization is:",loader_utilization)
loader_idleness=1-loader_utilization
print("Loader Idleness is:",loader_idleness)
print("simulation time: ",env.now)
