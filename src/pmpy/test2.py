# -*- coding: utf-8 -*-
"""
Created on Sun Nov 28 22:43:01 2021

@author: naima
"""

import des as des
import pmpy.dists as dist
import pmpy.mcs as mc

def a0(e,Rs):
        i=0
        yield e[i].get(Rs,Resources[i],Priorities[i])
        yield e[i].do(str(i),Durations[i])
        yield e[i].put(Rs,Resources[i])

def a1(e,Rs):
        yield p0
        i=1
        yield e[i].get(Rs,Resources[i],Priorities[i])
        yield e[i].do(str(i),Durations[i])
        yield e[i].put(Rs,Resources[i])

def a2(e,Rs):
        yield p0
        i=2
        yield e[i].get(Rs,Resources[i],Priorities[i])
        yield e[i].do(str(i),Durations[i])
        yield e[i].put(Rs,Resources[i])


def a3(e,Rs):
        yield p1 & p2
        i=3
        yield e[i].get(Rs,Resources[i],Priorities[i])
        yield e[i].do(str(i),Durations[i])
        yield e[i].put(Rs,Resources[i])

def a4(e,Rs):
        yield p1
        i=4
        yield e[i].get(Rs,Resources[i],Priorities[i])
        yield e[i].do(str(i),Durations[i])
        yield e[i].put(Rs,Resources[i])

def a5(e,Rs):
        yield p2
        i=5
        yield e[i].get(Rs,Resources[i],Priorities[i])
        yield e[i].do(str(i),Durations[i])
        yield e[i].put(Rs,Resources[i])

def a6(e,Rs):
        yield p1 & p2 & p3
        i=6
        yield e[i].get(Rs,Resources[i],Priorities[i])
        yield e[i].do(str(i),Durations[i])
        yield e[i].put(Rs,Resources[i])


Durations=[dist.triang(2,3,4), dist.triang(1,3,5), 5, 1, dist.triang(3.5,5,6), 4, dist.norm(2.5,1)]
Resources=[1, 3, 2, 3, 1, 2, 2] 
Priorities=[1, 2, 1, 1, 3, 1, 1] 

env=des.environment()
e=env.create_entities('e',7,print_actions=False)
Rs=des.priority_resource(env,'totalres',init=4,print_actions=False)
p0=env.process(a0(e,Rs))
p1=env.process(a1(e,Rs))
p2=env.process(a2(e,Rs))
p3=env.process(a3(e,Rs))
p4=env.process(a4(e,Rs))
p5=env.process(a5(e,Rs))
p6=env.process(a6(e,Rs))
env.run()
print(env.now) 

