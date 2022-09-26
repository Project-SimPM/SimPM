"""
Continous Simulation for Project Management in Python.
"""

from numpy import arange


class project:
    """
    Defines the project environment
    """
    def __init__(self,time_step=1):
        self.time=0
        self.time_step=time_step
        self.number_of_finished_acts=0
        self.activities=[]
        self.resources=[]

    def reset(self):
        self.time=0
        self.number_of_finished_acts=0
        for a in self.activities:
            a.reset()
        for r in self.resources:
            r.reset()

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

    def step_with_delay_one_act(self,act_id):
        for a in self.activities:
            a.check_start()
        
        self.time+=self.time_step

        for i in range(len(self.activities)):
            if i==act_id:
                d=self.activities[i].progress_with_delay()
            else:
                self.activities[i].progress()
        
        for a in self.activities:
            a.check_finished()

        return d


    
    def simulate(self,until=1000):
        self.reset()
        for i in arange(0,until,self.time_step):
            self.step()
            if self.number_of_finished_acts==len(self.activities):
                break
    
    def simulate_with_delays(self,until=1000):
        self.reset()
        for i in arange(0,until,self.time_step):
            self.step_with_delay()
            if self.number_of_finished_acts==len(self.activities):
                break
    

    def simulate_with_delays_all_acts(self,delay_window,until=1000):
        """simulate the process until we reach a time_step"""
        self.reset()
        for i in arange(0,until,self.time_step):
            if i<=delay_window:
                self.step_with_delay()
            else:
                self.step()
            if self.number_of_finished_acts==len(self.activities):
                break

    def simulate_with_delays_one_act(self,act_number,delay_window,until=1000):
        """simulate the process until we reach a time_step"""
        self.reset()
        d=None
        for i in arange(0,until,self.time_step):
            if i<delay_window:
                self.step_with_delay()
            elif i==delay_window:
                d=self.step_with_delay_one_act(act_number)# here...how about output
            else:
                self.step()
            if self.number_of_finished_acts==len(self.activities):
                return d

    def delay_analysis(self,):

        print("**********Delay analysis with window size equals",self.time_step,"************")
        overall_responsibility={}
        self.simulate()
        no_delay_duration=self.time
        print("No delay time is:", no_delay_duration)
        self.simulate_with_delays()
        all_delay_duration=self.time
        total_delays=all_delay_duration-no_delay_duration
        previous_time=no_delay_duration
        for window in arange(0,all_delay_duration+1,self.time_step):
            delay_responsibility_for_window={}
            for i in range(len(self.activities)):
                d=self.simulate_with_delays_one_act(i,window)
                delay_impact=self.time-previous_time
                if delay_impact>0:
                    delay_responsibility_for_window[d.responsible_party]=delay_impact
            self.simulate_with_delays_all_acts(window)
            window_impact=self.time-previous_time
            if window_impact>0:
                normaliziation_factor=window_impact/sum(delay_responsibility_for_window.values())
                for responsible_party in delay_responsibility_for_window:
                    delay_responsibility_for_window[responsible_party]*=normaliziation_factor
                print("delays in time window", window,"to",window+self.time_step, "increase total time to",self.time, "with following responsibilities:",delay_responsibility_for_window)
                previous_time=self.time
                
                for party in delay_responsibility_for_window:
                    if party in overall_responsibility:
                        overall_responsibility[party]+=delay_responsibility_for_window[party]
                    else:
                        overall_responsibility[party]=delay_responsibility_for_window[party]



        print("Total delays:",total_delays)
        print(overall_responsibility)
        

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
        self.initially_available=available
        self.initially_busy=busy

    def reset(self):
        self.available=self.initially_available
        self.busy=self.initially_busy


    def get(self,number):
        if self.available>=number:
            self.available-=number
            return True
        else:
            return False

    def put(self,number):
        self.available+=number
            
class delay:
    """
    define a delay in the project
    """
    def __init__(self,activity,start_time, duration,responsible_party):
        self.activity=activity
        self.start_time=start_time
        self.finish_time=start_time+duration
        self.responsible_party=responsible_party
        self.activity.delays.append(self)


class activity:
    "define an activity for the project"
    def __init__(self,project,name, duration):
        self.name=name
        self.duration=duration
        self.remaining_duration=duration
        
        self.delays=[]

        self.started=False
        self.finished=False
        
        self.prerequisite_acts=[]
        
        self.resource_needs=[]
        self.resource_used=[]

        self.start_time=None
        self.finish_time=None

        self.project=project
        self.project.activities.append(self)
 
    def reset(self):
        self.remaining_duration=self.duration
        self.started=False
        self.finished=False
        self.resource_used=[]
        self.start_time=None
        self.finish_time=None

    def progress(self):
        if self.finished:
            return
        if self.started and not self.finished:
            self.remaining_duration-=self.project.time_step
        
    def is_in_delay(self):
        """
        checks if an activity is in a time_step that causes a delay in the project
        """
        for d in self.delays:
            if d.start_time<self.project.time<=d.finish_time:
                return d
        return False
    
    def progress_with_delay(self):
        
        if self.finished:
            return
        
        if self.started and not self.finished:
            d=self.is_in_delay()
            if d:
                return d
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
r2=resource(2)
a1=activity(e,"a1",3)
a2=activity(e,"a2",3)
a3=activity(e,"a3",6)

delay(a1,1,3,"contractor")
delay(a2,2,2,"owner")
delay(a3,7,3,"owner")

a3.prerequisite_acts=[a1,a2]
a1.resource_needs=[(r,3),(r2,2)]
a2.resource_needs=[(r,3),(r2,2)]

e.delay_analysis()
