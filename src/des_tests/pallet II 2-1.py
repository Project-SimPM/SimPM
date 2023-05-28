import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir) 

import simpm.des as des
import simpm.dist as dist
import matplotlib as plt

def create_pallets(factory:des.Environment,res,damage_pallets_factory):
    while True :
            yield factory.do("work",dist.uniform(3,5))
            yield factory.add(res,10)    
    
def truck_process(truck,pallets,site_pallets,damage_pallets_site,damage_pal_fact):
    while True:
        yield truck.get(pallets,450)
        yield truck.do("travel",dist.triang(50,60,65))
        yield truck.add(site_pallets,450)
        yield truck.do("travel",dist.triang(50,60,65))
       
def worker1_process(worker,site_pallets,installed_pallets) :
    while True:
            yield worker.get(site_pallets,1)
            yield worker.do('install',dist.uniform(1,1.5))
            yield worker.add(installed_pallets,1)
            if installed_pallets.level()>=20000:
                break

def worker2_process(worker,site_pallets,installed_pallets) :
    while True:
            yield worker.get(site_pallets,1)
            yield worker.do('install',dist.uniform(1.5,2))
            yield worker.add(installed_pallets,1)
            if installed_pallets.level()>=20000:
                break
            
def worker3_process(worker,site_pallets,installed_pallets) :
    while True:
            yield worker.get(site_pallets,1)
            yield worker.do('install',dist.uniform(1,1.5))
            yield worker.add(installed_pallets,1)
            if installed_pallets.level()>=20000:
                break
                        
env=des.Environment()
factory=des.Entity(env,'factory')
pallets=des.Resource(env,'factrory_pallet',init=0,capacity=10000)
site_pallets=des.Resource(env,'site_pallet',init=0,capacity=10000)
installed_pallets=des.Resource(env,'installed_pallet',init=0,capacity=30000)
worker1=des.Entity(env,'woker')
worker2=des.Entity(env,'woker')
worker3=des.Entity(env,'woker')
truck=env.create_entities('truck',2)
damage_pallets_site=des.Resource(env,"damage_pallets_site",0)
damage_pallets_factory=des.Resource(env,"damage_pallets_site",0)
env.process(create_pallets(factory,pallets,damage_pallets_factory))
env.process(truck_process(truck[0],pallets,site_pallets,damage_pallets_site,damage_pallets_factory))
env.process(truck_process(truck[1],pallets,site_pallets,damage_pallets_site,damage_pallets_factory))
p1=env.process(worker1_process(worker1,site_pallets,installed_pallets))
p2=env.process(worker2_process(worker2,site_pallets,installed_pallets))
p3=env.process(worker3_process(worker3,site_pallets,installed_pallets))
env.run(until=p1|p2|p3)
print(env.now)
a=truck[0].waiting_time()
b=truck[1].waiting_time()
c=worker1.waiting_time()
d=worker2.waiting_time()
e=dist.emperical(a)
f=dist.emperical(b)
g=dist.emperical(c)
h=dist.emperical(d)
e.plot_pdf()
f.plot_pdf()
g.plot_pdf()
h.plot_pdf()
print('baraye truck ha saf ijad mishavd vali taqriban waiting time worcker ha bad az residn avalin pallet ha sefr ast')
print('average truck 1 waiting time=',(sum(a)/len(a)))
print('average truck 2 waiting time=',(sum(b)/len(b)))
print('average worcker 1 waiting time=',(sum(c)/len(c)))
print('average worcker 2 waiting time=',(sum(d)/len(d)))
print("tosie mishavad tedad worcker ha afzayesh dade sahvad")
print("zaman taghribi nasb 20000 pallet ba 2 worcker hododn barab 14800 ast")
print('zaman taqribi nasbe 20000 pallet bad az ezafe kardan 1 worcker=',env.now)