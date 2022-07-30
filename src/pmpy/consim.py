"""
Continous Simulation for Project Management in Python.
"""

from numpy import number


class environment:
    def __init__(self,time_step=1):
        self.time=0
        self.time_step=time_step
        self.number_of_finished_acts=0
        self.activities=[]
        self.resources=[]

    def step(self):
        self.time+=self.time_step
        for a in self.activities:
            a.progress()#to implement as part of step
        
        for a in self.activities:
            a.update_status()#to implement as part of step
        

    def simulate(self,until=1000):
        
        for i in range(until):
            self.step()
            if self.number_of_finished_acts==len(self.activities):
                break
            

class resouce:
    """
    Define a resource type for the project environment
    """
    def __init__(self,available,busy=0):
        self.available=available
        self.busy=busy
    def get(self,number):
        if self.available>=number:
            self.available-=number
            return True
        else:
            return False

    def put(self,number):
        self.available+=number
            



class activity:
    "define an activity for the project environment"
    def __init__(self,environment,duration,delay_start_time=None,delay_finish_time=None):
        self.duration=duration
        self.remaining_duration=duration
        
        self.delay_start_time=delay_start_time
        self.delay_finish_time=delay_finish_time
        
        self.started=False
        self.finished=False
        
        self.prerequisite_acts=[]
        
        self.resource_needs=[]
        self.resource_used=[]

        self.environment=environment
        self.environment.activities.append(self)
 
    def step(self):
        if self.finished:
            return
        if not self.started:
            self.check_start()
        if self.started and not self.finished:
            self.remaining_duration-=self.environment.time_step
        if self.remaining_duration<=0:
            self.finish()

    def check_start(self):
        if not self.started:
            for act in self.prerequisite_acts:
                if not act.finished:
                    return
            self.resource_used=[]
            for rq in self.resource_needs:
                (r,q)=rq
                if not r.get(q):
                    self.give_back_resources()
                    return
                else:
                    self.resource_used.append(r,q)
            self.started=True

    def give_back_resources(self):
        for rq in self.resource_used:
            (r,q)=rq
            r.put(q)
        
    def finish(self):
        self.finished=True
        self.give_back_resources()
        e.number_of_finished_acts+=1

    def need_resource(self,resource,quantity):
        self.resourc_needs.append((resource,quantity))


e=environment(1)
a1=activity(e,3)
a2=activity(e,4)
#a3=activity(e,5)
a2.prerequisite_acts=[a1]

e.simulate()
print("the project duration is:",e.time)