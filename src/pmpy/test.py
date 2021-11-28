import des as des
def truck_process(truck:des.entity,loader:des.resource,dumped_dirt:des.resource):
    while True:
        yield truck.get(loader,1)
        yield truck.do("loading",7)
        yield truck.put(loader,1)
        yield truck.do("hauling",17)
        yield truck.do("dumping",3)
        yield truck.add(dumped_dirt,60)

        yield truck.do("return",13)
env=des.environment()
truck=env.create_entities("truck",10,print_actions=False,log=True)
loader=des.resource(env,"loader")
dumped_dirt=des.resource(env,"dirt",init=0,capacity=100000)
for t in truck:
    env.process(truck_process(t,loader,dumped_dirt))
env.run()
print(env.now)
print(truck[0].schedule())
print(truck[0].waiting_time())
print(loader.queue_log())
print(loader.status_log())
print(loader.waiting_time())

