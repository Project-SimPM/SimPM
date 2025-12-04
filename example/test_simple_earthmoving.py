import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
# Add the project root and source directory so the example can run without installation.
sys.path.insert(0, parentdir)
sys.path.insert(0, os.path.join(parentdir, "src"))
import simpm
import simpm.des as des
def truck_process(truck:des.Entity,loader:des.Resource,dumped_dirt:des.Resource):
    while True:
        remaining = dumped_dirt.capacity() - dumped_dirt.level()
        if remaining <= 0:
            break
        load_amount = min(60, remaining)
        yield truck.get(loader,1)
        yield truck.do("loading",7)
        yield truck.put(loader,1)
        yield truck.do("hauling",17)
        yield truck.do("dumping",3)
        # Re-check capacity just before dumping to avoid blocking on a full container
        # when multiple trucks are hauling simultaneously.
        remaining_after_haul = max(0, dumped_dirt.capacity() - dumped_dirt.level())
        # This re-check remains necessary even with the new fail-fast guards in
        # the Resource class. Other trucks can finish hauling while this one is
        # en route, so we cap the dump amount to whatever capacity is left
        # rather than raising on an over-capacity add.
        if remaining_after_haul == 0:
            break

        yield truck.add(dumped_dirt, min(load_amount, remaining_after_haul))

        if dumped_dirt.level() >= dumped_dirt.capacity():
            break

        yield truck.do("return",13)
env=des.Environment()
truck=env.create_entities("truck",10,print_actions=False,log=True)
loader=des.Resource(env,"loader")
dumped_dirt=des.Resource(env,"dirt",init=0,capacity=100000)
for t in truck:
    env.process(truck_process(t,loader,dumped_dirt))

# Run the simulation until no events remain. Each truck exits its loop once the dirt
# container reaches capacity, so the environment will halt automatically regardless
# of dashboard mode.
simpm.run(env, dashboard="post")
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

