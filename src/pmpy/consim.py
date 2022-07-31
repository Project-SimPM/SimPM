"""
Continous Simulation for Project Management in Python.
"""

from numpy import NaN, number


class project:
    def __init__(self,time_step=1):
        self.time=0
        self.time_step=time_step
        self.number_of_finished_acts=0
        self.activities=[]
        self.resources=[]

    def step(self):
        
        for a in self.activities:
            a.check_start()
        
        self.time+=self.time_step

        for a in self.activities:
            a.progress()
        
        for a in self.activities:
            a.check_finished()

    def step_with_delay(self):
        for a in self.activities:
            a.check_start()
        
        self.time+=self.time_step

        for a in self.activities:
            a.progress_with_delay()
        
        for a in self.activities:
            a.check_finished()

    def step_with_delay_last_window(self,act_id):
        for a in self.activities:
            a.check_start()
        
        self.time+=self.time_step

        for i in range(len(self.activities)):
            if i==act_id:
                self.activities[i].progress_with_delay()
            else:
                self.progress()
        
        for a in self.activities:
            a.check_finished()

    def simulate(self,until=1000):
        
        for i in range(until):
            self.step()
            if self.number_of_finished_acts==len(self.activities):
                break
    
    
    def simulate_with_delays(self,time_step_number=1000,until=1000):
        #simulate the process until we reach a time_step
        for i in range(until):
            if i<time_step_number:
                self.step_with_delay()
            elif i==time_step_number:
                for j in range(len(self.activities)):
                    self.step_with_delay_last_window(j)# here...how about output
            else:
                self.step()
            if self.number_of_finished_acts==len(self.activities):
                break


    def print_simulation_results(self):
        print("the project duration is:",e.time)
        print("start time and finish time of activities:")
        for a in e.activities:
            print(a.name,":",a.start_time,a.finish_time)

            

class resource:
    """
    Define a resource type for the project project
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
    "define an activity for the project project"
    def __init__(self,project,name, duration,delay_start_time=0,delay_duration=0):
        self.name=name
        self.duration=duration
        self.remaining_duration=duration
        
        self.delay_start_time=delay_start_time
        self.delay_finish_time=delay_start_time+delay_duration
        
        self.started=False
        self.finished=False
        
        self.prerequisite_acts=[]
        
        self.resource_needs=[]
        self.resource_used=[]

        self.start_time=None
        self.finish_time=None

        self.project=project
        self.project.activities.append(self)
 
    def progress(self):
        if self.finished:
            return
        if self.started and not self.finished:
            self.remaining_duration-=self.project.time_step
        
    def progress_with_delay(self):
        
        if self.finished:
            return
        if self.started and not self.finished:
            if self.delay_start_time<self.project.time<=self.delay_finish_time:
                return
            self.remaining_duration-=self.project.time_step
        

    def check_finished(self):
        if self.remaining_duration<=0 and not self.finished:
            self.finish_time=self.project.time
            self.finished=True
            self.give_back_resources()
            e.number_of_finished_acts+=1

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
                    self.resource_used.append((r,q))
            self.start_time=self.project.time
            self.started=True

    def give_back_resources(self):
        for rq in self.resource_used:
            (r,q)=rq
            r.put(q)

    def need_resource(self,resource,quantity):
        self.resourc_needs.append((resource,quantity))


e=project(1)
r=resource(6)
a1=activity(e,"a1",3,delay_start_time=1,delay_duration=3)
a2=activity(e,"a2",4,delay_start_time=1,delay_duration=5)
a3=activity(e,"a3",6)
a3.prerequisite_acts=[a1,a2]
a1.resource_needs=[(r,3)]
a2.resource_needs=[(r,3)]


e.simulate_with_delays(2)
e.print_simulation_results()
