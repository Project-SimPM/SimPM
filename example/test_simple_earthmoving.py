import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir) 
import simpm.des as des
def truck_process(truck:des.Entity,loader:des.Resource,dumped_dirt:des.Resource):
    while True:
        yield truck.get(loader,1)
        yield truck.do("loading",7)
        yield truck.put(loader,1)
        yield truck.do("hauling",17)
        yield truck.do("dumping",3)
        yield truck.add(dumped_dirt,60)

        yield truck.do("return",13)
env=des.Environment()
truck=env.create_entities("truck",10,print_actions=False,log=True)
loader=des.Resource(env,"loader")
dumped_dirt=des.Resource(env,"dirt",init=0,capacity=100000)
for t in truck:
    env.process(truck_process(t,loader,dumped_dirt))
env.run()
print(env.now)
print(truck[0].schedule())
print(truck[0].waiting_time())
print(loader.queue_log())
print(loader.status_log())
print(loader.waiting_time())
print("average_queue_length:",loader.average_queue_length())
print("average_utlization:",loader.average_utilization())
print("average_idleness:",loader.average_idleness())
print("truck0 waiting time:",truck[0].waiting_time().mean())
print("total time in use:",loader.total_time_in_use())
print("total time idle:",loader.total_time_idle())
print("average level of loader:",loader.average_level())
print("average queue length:",loader.average_queue_length())

