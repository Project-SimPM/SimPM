import pmpy.simulation.discrete_event as des

def earthmoving(truck,res):
    global dirt
    while dirt>100:
        yield truck.get(res,1) 
        yield truck.do('loading',5)
        truck.put(res,1)
        yield truck.do('hauling',30)
        yield truck.do('dumping',5)
        yield truck.do('returning',20)
        dirt-=100
    print(dirt)

dirt=500

env=des.Environment()
loader = des.Resource(env,'loader', capacity=1)

truck= des.Entity(env,'truck',print_actions=True)
truck2= des.Entity(env,'truck2',print_actions=False)
env.process(earthmoving(truck,loader))
env.process(earthmoving(truck2,loader))
env.run()  
