import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir) 

import simpm.des as des

def prcpm(list_priority):
    def a0(e,r):
        yield e.get(r, 1,list_pr[0])
        yield e.do("activity0",3)
        yield e.put(r,1)
        e.attr["finish_time"]=env.now



    def a1(e,r):
        yield p0
        if en[0].attr["finish_time"]==env.now:
            en[0].attr["critical"]=True
        else:
            en[0].attr["critical"]=False  
        yield e.get(r, 3,list_pr[1])
        yield e.do("activity1",6)
        yield e.put(r,3)
        e.attr["finish_time"]=env.now

    def a2(e,r):
        yield p0
        if en[0].attr["finish_time"]==env.now:
            en[0].attr["critical"]=True
        else:
            en[0].attr["critical"]=False  
        yield e.get(r, 2,list_pr[2])
        yield e.do("activity2",5)
        yield e.put(r,2)
        e.attr["finish_time"]=env.now
    def a3(e,r):
        yield p1&p2
        if en[1].attr["finish_time"]==env.now:
            en[1].attr["critical"]=True
        else:
            en[1].attr["critical"]=False  
        if en[2].attr["finish_time"]==env.now:
            en[2].attr["critical"]=True
        else:
            en[2].attr["critical"]=False  
        yield e.get(r, 3,list_pr[3])
        yield e.do("activity3",1)
        yield e.put(r,3)
        e.attr["finish_time"]=env.now

    def a4(e,r):
        yield p1
        if en[1].attr["finish_time"]==env.now:
            en[1].attr["critical"]=True
        else:
            en[1].attr["critical"]=False
        yield e.get(r, 1,list_pr[4])
        yield e.do("activity4",3)
        yield e.put(r,1)
        e.attr["finish_time"]=env.now

    def a5(e,r):
        yield p2
        if en[2].attr["finish_time"]==env.now:
            en[2].attr["critical"]=True
        else:
            en[2].attr["critical"]=False  
        yield e.get(r, 2,list_pr[5])
        yield e.do("activity5",4)
        yield e.put(r,2)
        e.attr["finish_time"]=env.now


    def a6(e,r):
        yield p4&p5&p3
        if en[3].attr["finish_time"]==env.now:
            en[3].attr["critical"]=True
        else:
            en[3].attr["critical"]=False    
        if en[4].attr["finish_time"]==env.now:
            en[4].attr["critical"]=True
        else:
            en[4].attr["critical"]=False    
        if en[5].attr["finish_time"]==env.now:
            en[5].attr["critical"]=True
        else:
            en[5].attr["critical"]=False    
        yield e.get(r, 2,list_pr[6])
        yield e.do("activity6",2.5)
        yield e.put(r,2)
        e.attr["finish_time"]=env.now
        e.attr["critical"]=True
    env=des.Environment()
    en=env.create_entities("e",7,True,True)


    res=des.PriorityResource(env,"pr_resourse",init=4)
    
    p0=env.process(a0(en[0],res))
    p1=env.process(a1(en[1],res))
    p2=env.process(a2(en[2],res))
    p3=env.process(a3(en[3],res))
    p4=env.process(a4(en[4],res))
    p5=env.process(a5(en[5],res))
    p6=env.process(a6(en[6],res))

    env.run()
    return(env.now)


list_pr=[1,2,1,1,3,1,1]
print(prcpm(list_pr))