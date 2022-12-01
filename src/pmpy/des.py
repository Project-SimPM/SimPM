"""
Discrete Event Simulation for Project Management in Python.
"""
import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir) 

import simpy
from numpy import array, append,nansum
from pandas import DataFrame
from bisect import insort_left
import matplotlib.pyplot as plt


from pmpy.dist import distribution


"""
*****************************************
*****entity class*******************
*****************************************
"""
def _switch_dic(dic):
    """
    siwtch key and value in a dictionary

    """
    newdic={}
    for key in dic:
        newdic[dic[key]]=key
    return newdic

class entity:
    """
    A class that defines an entity. Entities are virtual objects essential to useful for modeling dynamic systems. 
    Some examples of entities can be: a customer, communication message, or any resource requiring service.

    ...
    Attributes
    ----------
    name: str
        Name of the entity
    id: int
        A unique id for the entity in the environment
    env: pmpy.des.environment
        The environemnt in which the entity is defined in
    attr: dict
        a dictionay containting all the special attributes defined for the entity.
    """
    def __init__(self,env,name,print_actions=False,log=True):
        """
        Creates an new instance for entity.

        Parameters
        ----------
        env:pmpy.environment
            The environment for the entity
        name : string
            Name of the entity
        print_actions : bool
            If equal to True, the actions of the entity will be printed in console
        log: bool
            If equals True, various statistics will be collected for the entity
        """
        self.env=env
        self.name=name
        env.last_entity_id+=1
        self.id=self.env.last_entity_id
        env.entity_names[self.id]=self.name+'('+str(self.id)+')'
        self.last_act_id=0
        self.act_dic={}
        self.attr={}
        self.print_actions=print_actions
        self.log=log
        self.using_resources={} #a dictionary showig all the resources an entity is using

        #***logs
        self._schedule_log=array([[0,0,0]])#act_id,act_start_time,act_finish_time
        self._status_codes={'wait for':1,'get':2,'start':3,'finish':4,'put':5,'add':6}
        self._status_log=array([[0,0,0]])#time,entity_status_code,actid/resid
        self._waiting_log=array([[0,0,0,0]]) #resource_id,start_waiting,end_waiting,amount waiting for
        self.pending_requests=[] #the simpy requests made by an entity but not granted yet

        if print_actions:
            print(name+'('+str(self.id)+') is created, sim_time:',env.now)
    
      
    def _activity(self,name,duration):
        """
        This method defines the activity that the entity is doing.

        Parameters
        ----------
        name : string
            Name of the activty
        Duration : float, int, or distribution
            The duration of that activity
        """
        if isinstance(duration,distribution):
            d=-1
            while d<0:
                d=duration.sample()
            duration=d
        if self.print_actions:
            print(self.name+'('+str(self.id)+ ') started',name,', sim_time:',self.env.now)
        
        if name not in self.act_dic:
            self.last_act_id+=1
            self.act_dic[name]=self.last_act_id
        if self.log:
            self._schedule_log=append(self._schedule_log,[[self.act_dic[name],self.env.now,self.env.now+duration]],axis=0)
            self._status_log=append(self._status_log,[[self.env.now,self._status_codes['start'],self.act_dic[name]]],axis=0)

        yield self.env.timeout(duration)
  
        if self.print_actions:
            print(self.name+'('+str(self.id)+ ') finished',name,', sim_time:',self.env.now)
        if self.log:
            self._status_log=append(self._status_log,[[self.env.now,self._status_codes['finish'],self.act_dic[name]]],axis=0)
    
    
    def _interruptive_activity(self,name,duration):
        """
        This method defines the activity that the entity is doing.

        Parameters
        ----------
        name : string
            Name of the activty
        Duration : float, int, or distribution
            The duration of that activity
        """
        if isinstance(duration,distribution):
            d=-1
            while d<0:
                d=duration.sample()
            duration=d
        if self.print_actions:
            print(self.name+'('+str(self.id)+ ') started',name,', sim_time:',self.env.now)
        
        if name not in self.act_dic:
            self.last_act_id+=1
            self.act_dic[name]=self.last_act_id
        if self.log:
            self._schedule_log=append(self._schedule_log,[[self.act_dic[name],self.env.now,self.env.now+duration]],axis=0)
            self._status_log=append(self._status_log,[[self.env.now,self._status_codes['start'],self.act_dic[name]]],axis=0)

        #yield self.env.timeout(duration)
        
        done_in=duration
        while done_in:
            try:
                # Working on the part
                start = self.env.now
                print("preemptive activity started at time", start)
                yield self.env.timeout(done_in)
                done_in=0
            except simpy.Interrupt:
                    print("preemptive activity interrupted at time:", self.env.now)
                    done_in -= self.env.now - start  # How much time left?
                    print("some time is left:",done_in)
        if self.print_actions:
            print(self.name+'('+str(self.id)+ ') finished',name,', sim_time:',self.env.now)
        if self.log:
            self._status_log=append(self._status_log,[[self.env.now,self._status_codes['finish'],self.act_dic[name]]],axis=0)

    def do(self,name,dur):
        """
        Defines the activity that the entity is doing.

        Parameters
        ----------
        name : string
            Name of the activity
        duration : float , int, or distribution
            The duration of that activity
        Returns
        -------
        Environment.process
            the process for the activity
        """
        try:
            if isinstance(dur,distribution):
                d=-1
                while d<0:
                    d=dur.sample()
                dur=d
       
            return self.env.process(self._activity(name,dur))
        except:
            print('pmpy: error in  duration of activity',name)

    def interruptive_do(self,name,dur):
        try:
            if isinstance(dur,distribution):
                    d=-1
                    while d<0:
                        d=dur.sample()
                    dur=d
        except:
             print('pmpy: error in  duration of activity',name)
        return self.env.process(self._interruptive_activity(name,dur))
        

        

    def get(self,res,amount=1,priority=1,preempt:bool=False):
        """
        Entity requests to get a resource using this method. 

        Parameters
        ----------
        res : pmpy.resource
            the resource to be captured by the entity
        amount :  int
            The number of resouces to be captured
        priority : int
            The priority of the request for getting the resource 
        preempt : bool
            Preemptive resources are not yet implemented
        Returns
        -------
        pmpy.environment.process
            The process for the request
        """
        try:
            if isinstance(amount,distribution):
                a=-1
                while a<0:
                    a=amount.sample()
                amount=int(a)
            if type(res)==resource:
                return self.env.process(res.get(self,amount))
            elif type(res)==priority_resource:
                return self.env.process(res.get(self,amount,priority))
            elif type(res)==preemptive_resource:
                if amount>1:
                    print("Warning: amount of preemptive resource is always 1")
                return res.get(self,priority,preempt)
        except:
            print('pmpy: error in get')

    def add(self,res,amount=1):
        """
        Entity increases the number of resources using this method.

        Parameters
        ----------
        res : pmpy.resource
            the resource to be added by the entity
        amount :  int
            The number of resouces to be added
        Returns
        -------
        pmpy.environment.process
            The process for adding resources
        """
        if isinstance(amount,distribution):
            a=-1
            while a<0:
                a=amount.sample() #?can this amount be float!
            amount=int(a)
        return self.env.process(res.add(self,amount))

    def put(self,res,amount=1,request=None):
        """
        Entity puts back the resources using this method.

        Parameters
        ----------
        res : pmpy.resource
            the resource to be added by the entity
        amount :  int
            The number of resouces to be put back
        Returns
        -------
        pmpy.environment.process
            The process for putting back the resources
        """
        if isinstance(amount,distribution):
            a=-1
            while a<0:
                a=amount.sample()
            amount=int(a)
        if type(res)==preemptive_resource:
            
                if amount>1:
                    amount=1
                    print("Warning: amount of preemptive resource is always 1")
                return self.env.process(res.put(self,request))
        return self.env.process(res.put(self,amount))
    def is_pending(self,res,amount:int=1):
        """

        Parameters:
        -----------
        res : resource
            Resource for which the eneity is waiting for.
        amount: int
            Number of resources that the entity is waiting for.
            If the number of entities is not specified, waiting for any number of resources is ok

        Returns
        --------
        True if entity is waiting for the resource, and False if the entity is not waiting for the resource
        """

        for r in res.request_list:
            if r.entity==self and r.amount==amount:
                return True
        return False

    def not_pending(self,res,amount:int=1):
        """

        Parameters:
        -----------
        res : resource
            Resource for which the eneity is waiting for.
        amount: int
            Number of resources that the entity is waiting for.
            If the number of entities is not specified, waiting for any number of resources is ok

        Returns
        --------
        Flase if the entitiy is not waiting for the resource, and True if the entity is not waiting for the resource
        """
        return not self.is_pending(res,amount)

    def cancel(self,res,amount:int=1):
        """
        cancels a resource request if it is pending, and put it back if it is already granted.
       
        Parameters
        -----------
        res : resource
            Resource for which the eneity is waiting for.
        amount: int
            Number of resources that the entity is waiting for.
            If the number of entities is not specified, waiting for any number of resources is ok

  
         """

        for r in res.request_list:
            if r.entity==self and r.amount==amount:
                res.cancel(r)
                return 
        
        self.put(res,amount) #a problem may occur of someone adds to the resouce meanwhile we are canceling
        
                    
    def schedule(self):
        """

        Returns
        -------
        pandas.DataFrame
            The schedule of each entity.
            The columns are activity name, and start time and finish time of that activity
        """
        df=DataFrame(data=self._schedule_log[1: , :],columns=['activity','start_time','finish_time'])
        df['activity']=df['activity'].map(_switch_dic(self.act_dic))
        return df

    def waiting_log(self):
        """

        Returns
        -------
        pandas.DataFrame
            The time the entity started waiting and the time it finished waiting.
            The columns show the resource name for which the entity is waiting for, time when waiting is started, 
            time when waiting is finished, and the number of resources the entity is waiting for
        """
        df=DataFrame(data=self._waiting_log[1: , :],columns=['resource','start_waiting','end_waiting','resource_amount'])
        df['resource']=(df['resource'].map(self.env.resource_names))
        return df


    def waiting_time(self):
        """

        Returns
        -------
        numpy.array
            The waiting durations of the entity each time it waited for a resource
        """
        a=self.waiting_log()
        a=a['end_waiting']-a['start_waiting']
        return a.values
        
    def status_log(self):
        """

        Returns
        -------
        pandas.DataFrame
            shows any change in the status of an entity, the change can be either
            waiting for a resourcing, getting a resources, putting a resource back, or adding to a resouce, 
            or it can be starting or finishing an activity
        """
        df=DataFrame(data=self._status_log[1: , :],columns=['time','status','actid/resid'])
        df['status']=df['status'].map(_switch_dic(self._status_codes))
        
        return df
"""
*****************************************
*****Resource Class*******************
*****************************************
"""
class general_resource():
    """
    The parent class for all of pmpy.resources
    """
    def __init__(self,env,name,capacity,init,print_actions=False,log=True):
        """
        Creates an intstance of a pmpy general resource.

        Parameters
        ----------
        env:pmpy.environment
            The environment for the entity
        name : string
            Name of the resource
        id : int
            A unique id for the resource in the environment
        capacity:
            Maximum capacity for the resource
        init : int
            Initial number of resources
        print_actions : bool
            If equal to True, the changes in the resource will be printed in console
        log: bool
            If equals True, various statistics will be collected for the resource
        """
        self.name=name
        self.env=env 
        self.log=log
        self.print_actions=print_actions
        env.last_res_id+=1
        self.id=env.last_res_id
        env.resource_names[self.id]=self.name+'('+str(self.id)+')'
        self.in_use=0
        self.idle=init
        self.container=simpy.Container(env, capacity,init)
        self.queue_length=0 #number of entities waiting for a resource
        self.request_list=[]
        self.attr={} #attributes for resoruces
        
        #logs
        self._status_log=array([[0,0,0,0]])#time,in-use,idle,queue-length
        self._queue_log=array([[0,0,0,0]])#entityid,startTime,endTime,amount


    def queue_log(self):
        """

        Returns
        -------
        pandas.DataFrame
            All entities waiting for the resource, their start waiting time and
            finish waiting time are stored in this DataFrame
        """
        df=DataFrame(data=self._queue_log[1: , :],columns=['entity','start_time','finish_time','resource_amount'])
        df['entity']=df['entity'].map(self.env.entity_names)
        return df

    def status_log(self):
        """

        Returns
        -------
        pandas.DataFrame
            Any changes in the status of the resource and the time of the change is presented 
            in this DataFrame. The recorded statuses are number of in-use resources ,
            number of idle resources, and number of entities waiting for the resource. 
        """
        df=DataFrame(data=self._status_log[1: , :],columns=['time','in_use','idle','queue_length'])
        return df

    
    def waiting_time(self):
        """

        Returns
        -------
        numpy.array
            The waiting durations for a resource
        """
        a=self.queue_log()
        a=a['finish_time']-a['start_time']
        return a.values

    ####*****************plotting is still under construction*************
    # def plot_utilization(self):
    #     l=self.status_log()
    #     y=l["in_use"].values/(l["in_use"].values+l["idle"].values)
    #     x=l["time"].values
    #     plt.plot(x,y*100)
    #     plt.show()

    # def plot_idleness(self):
    #     l=self.status_log()
    #     l["idleness%"]=l["idle"].values/(l["in_use"].values+l["idle"].values)*100
    #     l.plot(x="time",y="idleness%")
    #     plt.show()
    
    # def plot_queue_length(self):
        
    #     l=self.status_log()
    #     l.plot(x="time",y="queue_length")
    #     plt.show()

    def average_utilization(self):
        """

        Returns
        -------
        int
            The average utilization for the resource
        """
        l=self.status_log()
        t1=l["time"].values[:-1]
        t2=l["time"].values[1:]
        y=l["in_use"].values/(l["in_use"].values+l["idle"].values)
        y_dur=y[:-1]
        d=t2-t1
        r= nansum(d*y_dur)/l["time"].values[-1]
        return r

    def average_idleness(self):
        """
        Returns
        -------
        int
            The average idleness for the resource
        """
        return 1-self.average_utilization()
    
    
    def total_time_idle(self):
        """
        Returns
        -------
        int
            The total idle time of the resource
        """
        l=self.status_log()
        t1=l["time"].values[:-1]
        t2=l["time"].values[1:]
        this_level=l["idle"].values
        this_level=this_level[:-1]
        d=t2-t1
        r= nansum(d*this_level)
        return r

    def total_time_in_use(self):
        """
        Returns
        -------
        int
            The total idle time of the resource
        """
        l=self.status_log()
        t1=l["time"].values[:-1]
        t2=l["time"].values[1:]
        this_level=l["in_use"].values
        this_level=this_level[:-1]
        d=t2-t1
        r= nansum(d*this_level)
        return r

    def average_level(self):
        """
        Returns
        -------
        int
            The average level for the resource
        """
        l=self.status_log()
        return self.total_time_idle()/l["time"].values[-1]



    def _request(self,entity,amount):
        """
        Calculate needed logs when an entity requests the resource.

        Parameters
        ----------
        entity : pmpy.entity
            The entity requesting the resource 
        amount : int
            The number of requested resouces 
        """
        self.queue_length+=1
        if self.print_actions or entity.print_actions:
            print(entity.name+'('+str(entity.id)+')'
                  +' requested',str(amount),self.name+'(s)'+'('+str(self.id)+')'+', sim_time:',self.env.now)
        if self.log:
            self._status_log=append(self._status_log,[[self.env.now,self.in_use,self.idle,self.queue_length]],axis=0)
            #if self.container.level+self.in_use==0:
            #    print("why")
        if entity.log:
            entity._status_log=append(entity._status_log,[[self.env.now,entity._status_codes['wait for'],self.id]],axis=0)

    def _get(self,entity,amount):
        """
        Calculate needed logs when an entity got the resource.

        Parameters
        ----------
        entity : pmpy.entity
            The entity getting the resource 
        amount : int
            The number of taken resouces 
        """
        self.queue_length-=1
        self.in_use+=amount
        self.idle-=amount
        if self.print_actions or entity.print_actions:
            print(entity.name+'('+str(entity.id)+')'
                  +' got '+str(amount),self.name+'(s)'+'('+str(self.id)+')'+', sim_time:',self.env.now)
        if self.log:
            self._status_log=append(self._status_log,[[self.env.now,self.in_use,self.idle,self.queue_length]],axis=0)
        if self.idle+self.in_use==0:
                print("why")
        if entity.log:
            entity._status_log=append(entity._status_log,[[self.env.now,entity._status_codes['get'],self.id]],axis=0)
        entity.using_resources[self]=amount

    def _add(self,entity,amount):
        """
        Calculate needed logs when an entity add to the resource.

        Parameters
        ----------
        entity : pmpy.entity
            The entity adding the resource 
        amount : int
            The number of added resouces 
        """
        if self.print_actions or entity.print_actions:
            print(entity.name+'('+str(entity.id)+')'
                  +' added '+str(amount),self.name+'(s)'+'('+str(self.id)+')'+', sim_time:',self.env.now)
        if self.log:
            self._status_log=append(self._status_log,[[self.env.now,self.in_use,self.idle,self.queue_length]],axis=0)
        if self.container.level+self.in_use==0:
                print("why")
        
        if entity.log:
            entity._status_log=append(entity._status_log,[[entity._status_codes['add'],self.id,self.env.now]],axis=0)

    def _put(self,entity,amount):
        """
        Calculate needed logs when an entity add to the resource.

        Parameters
        ----------
        res : pmpy.entity
            The entity putting the resource back
        amount : int
            The number of resouces being put back
        """
        if self not in entity.using_resources:
            raise Warning(entity.name, "did not got ", self.name,"to put it back")
        if self in entity.using_resources and entity.using_resources[self]<amount:
            raise Warning(entity.name, "did not got this many of",self.name, "to put it back")

        entity.using_resources[self]=entity.using_resources[self]-amount

        self.in_use-=amount
        self.idle+=amount

        if self.print_actions or entity.print_actions:
            print(entity.name+'('+str(entity.id)+')'
                  +' put back '+str(amount),self.name+'(s)'+'('+str(self.id)+')'+', sim_time:',self.env.now)

        if self.log:
            self._status_log=append(self._status_log,[[self.env.now,self.in_use,self.idle,self.queue_length]],axis=0)

        if entity.log:
            entity._status_log=append(entity._status_log,[[entity._status_codes['put'],self.id,self.env.now]],axis=0)
        
    def level(self):
        """

        Returns
        -------
        int
            The number of resources that are currently available
        """
        return self.container.level

    def idle(self):
        """

        Returns
        -------
        int
            The number of resources that are currently available

        """
        return self.level()

    def in_use(self):
        """

        Returns
        -------
        int
            The number of resources that are currently in-use

        """
        return self.in_use     

    def capacity(self):
        """

        Returns
        -------
        int
            The maximum capacity for the resource
        """
        return self.container.capacity

    def average_queue_length(self):
        """
        Returns
        -------
        float
            The average  queue length for a resource
        """
        return sum(self.waiting_time())/(self.env.now)

class request():
    """
    A class defining the a priority request for capturing the resources.
    This class allows to keep all the requests in a sorted list of requests.
    """
    def __init__(self,entity,amount):
        self.time=entity.env.now
        self.entity=entity
        self.amount=amount
        self.flag=simpy.Container(entity.env,init=0)#show if the resource is obtained when flag truns 1
        
    

class resource(general_resource):
    def __init__(self,env,name, init=1,capacity=1000,print_actions=False,log=True):
        """
        Defines a resource for which a priority queue is implemented. 

        Parameters
        ----------
        env:pmpy.environment
            The environment for the entity
        name : string
            Name of the resource
        capacity: int
            Maximum capacity for the resource, defualt value is 1000.
        init: int
            Initial number of resources, defualt value is 1.
        print_actions : bool
            If equal to True, the changes in the resource will be printed in console.
            defualt value is False
        log: bool
            If equals True, various statistics will be collected for the resource.
            defualt value is True.
        """
        super().__init__(env,name,capacity,init,print_actions,log)
        
        #self.resource=simpy.PriorityResource(env,1) #shoule be deleted
       

    def get(self,entity,amount):
        """
        A method for getting the resource. 

        Parameters
        ----------
        entity : pmpy.entity
            The entity adding the resource 
        amount : int
            The number of resouces to be added
        priority : int
            lower values for this input show higher priority
        """ 
        super()._request(entity,amount)
        pr=request(entity,amount)
        entity.pending_requests.append(pr) #append priority request to the eneity
        self.request_list.append(pr)
        #yield self.env.timeout(0) #? why do we need this?
        yield entity.env.process(self._check_all_requests())
        yield pr.flag.get(1) #flag shows that the resource is granted
        
    def _check_all_requests(self):
        """
        Check to see if any rquest for the resource can be granted.
        """
        while len(self.request_list)>0 and self.request_list[0].amount<=self.container.level:
            r=self.request_list.pop(0) #remove the first element from the list
            simpy_request=self.container.get(r.amount)
            yield simpy_request
            r.entity.pending_requests.remove(r) 
            r.flag.put(1)
            super()._get(r.entity,r.amount)
            if self.log:
                self._queue_log=append(self._queue_log,[[r.entity.id,r.time,self.env.now,r.amount]],axis=0)
            if r.entity.log:
                r.entity._waiting_log=append(r.entity._waiting_log,[[self.id,r.time,self.env.now,r.amount]],axis=0)

    def cancel(self,priority_request):
        if request in self.request_list:
            self.request_list.remove(priority_request)
        else:
            print("warning: the request can not be cancled as it is not in the request list")


    def add(self,entity,amount):
        """
        A method for adding the resource by the entity.

        Parameters
        ----------
        entity : pmpy.entity
            The entity adding the resource 
        amount : int
            The number of resouces to be added
        """
        yield self.container.put(amount)
        super()._add(entity,amount)
        return entity.env.process(self._check_all_requests())

    def put(self,entity,amount):
        """
        A method for putting back the resource by the entity.

        Parameters
        ----------
        entity : pmpy.entity
            The entity adding the resource 
        amount : int
            The number of resouces to be added
        """
        yield self.container.put(amount)
        super()._put(entity,amount)
        return entity.env.process(self._check_all_requests())

        
class priority_request():
    """
    A class defining the a priority request for capturing the resources.
    This class allows to keep all the requests in a sorted list of requests.
    """
    def __init__(self,entity,amount,priority):
        self.time=entity.env.now
        self.entity=entity
        self.amount=amount
        self.priority=priority
        self.flag=simpy.Container(entity.env,init=0)#show if the resource is obtained
        
    def __gt__(self,other_request):
        """
        Decides if a resource request has a higher priority than antothe resource request
        Lower priority values show higher priority!
        If the priority of two requests is equal and are made at the same time,
        the request with lower number of needed resources will have a higher priority.
        """
        if self.priority==other_request.priority:
            if self.time==other_request.time:
                return self.amount<other_request.amount
            else:
                return self.time<other_request.time
        return self.priority<other_request.priority
    
    def __eq__(self,other_request):
        return self.priority==other_request.priority and self.time==other_request.time and self.amount==other_request.amount


    def __ge__(self,other_request):
        return self>other_request or self==other_request

        
class priority_resource(general_resource):
    def __init__(self,env,name, init=1,capacity=1000,print_actions=False,log=True):
        """
        Defines a resource for which a priority queue is implemented. 

        Parameters
        ----------
        env:pmpy.environment
            The environment for the entity
        name : string
            Name of the resource
        capacity: int
            Maximum capacity for the resource, defualt value is 1000.
        init: int
            Initial number of resources, defualt value is 1.
        print_actions : bool
            If equal to True, the changes in the resource will be printed in console.
            defualt value is False
        log: bool
            If equals True, various statistics will be collected for the resource.
            defualt value is True.
        """
        super().__init__(env,name,capacity,init,print_actions,log)
        self.request_list=[]
        #self.resource=simpy.PriorityResource(env,1) #shoule be deleted
       

    def get(self,entity,amount,priority=1):
        """
        A method for getting the resource. 

        Parameters
        ----------
        entity : pmpy.entity
            The entity adding the resource 
        amount : int
            The number of resouces to be added
        priority : int
            lower values for this input show higher priority
        """ 
        super()._request(entity,amount)
        pr=priority_request(entity,amount,priority)
        entity.pending_requests.append(pr) #append priority request to the eneity
        insort_left(self.request_list,pr)
        yield self.env.timeout(0) #? why do we need this?
        yield entity.env.process(self._check_all_requests())
        yield pr.flag.get(1) #flag shows that the resource is granted
        
    def _check_all_requests(self):
        """
        Check to see if any rquest for the resource can be granted.
        """
        while len(self.request_list)>0 and self.request_list[-1].amount<=self.container.level:
            r=self.request_list.pop()
            yield self.container.get(r.amount)
            r.entity.pending_requests.remove(r)
            r.flag.put(1)
            super()._get(r.entity,r.amount)
            if self.log:
                self._queue_log=append(self._queue_log,[[r.entity.id,r.time,self.env.now,r.amount]],axis=0)
            if r.entity.log:
                r.entity._waiting_log=append(r.entity._waiting_log,[[self.id,r.time,self.env.now,r.amount]],axis=0)

    def cancel(self,priority_request):
        #***the followig code did not work***
        #if priority_request in self.request_list:
            #self.request_list.remove(priority_request)
            #remove does not work since it uses equal defined in the priority resource class
        for i in range(len(self.request_list)):
            pr=self.request_list[i]
            if pr.entity==priority_request.entity and pr.amount==priority_request.amount:
                del self.request_list[i]
                return
        
        print("warning: the priority request can not be cancled as it is not in the request list")


    def add(self,entity,amount):
        """
        A method for adding the resource by the entity.

        Parameters
        ----------
        entity : pmpy.entity
            The entity adding the resource 
        amount : int
            The number of resouces to be added
        """
        yield self.container.put(amount)
        super()._add(entity,amount)
        return entity.env.process(self._check_all_requests())

    def put(self,entity,amount):
        """
        A method for putting back the resource by the entity.

        Parameters
        ----------
        entity : pmpy.entity
            The entity adding the resource 
        amount : int
            The number of resouces to be added
        """
        yield self.container.put(amount)
        super()._put(entity,amount)
        return entity.env.process(self._check_all_requests())

class preemptive_resource(general_resource):
    """
    this class is under construction.
    """
    def __init__(self,env,name, print_actions=False,log=True):
        """
        Defines a resource for which a priority queue is implemented. 

        Parameters
        ----------
        env:pmpy.environment
            The environment for the entity
        name : string
            Name of the resource
        capacity: int
            Maximum capacity for the resource, defualt value is 1000.
        init: int
            Initial number of resources, defualt value is 1.
        print_actions : bool
            If equal to True, the changes in the resource will be printed in console.
            defualt value is False
        log: bool
            If equals True, various statistics will be collected for the resource.
            defualt value is True.
        """
        super().__init__(env,name,1,1,print_actions,log)
        
        self.resource=simpy.PreemptiveResource(env,1)
        self.request=None #the request of the entity that is currently using the resource
        self.current_entities=None
        self.suspended_entities=None
        
    def get(self,entity,priority: int,preempt:bool=False):
        super()._request(entity,1)
        while True:
            try:
                r=self.resource.request(priority,preempt)
                return r
            except:
                print("resource is preempted")
            
        self.request=r #the request that is currently using the rsource
        super()._get(entity,1)

    def put(self,entity,request=None):
        #to be added: when waiting to ptu pack soemthing some logs should be calculated
        yield self.resource.release(request)
        super()._put(entity,1)

    
    
"""
*****************************************
*****Environment Class*******************
*****************************************
"""
class environment(simpy.Environment):
    """
    This class defines the simulation environment. 
    All of the processes, entities and resources are defined in this class. 

    Attributes
    ----------
    now : float
        current simulation time
    
    """
    def __init__(self):
        """
        Creates an instance of the simulation environment
        """
        super().__init__()
        self.last_entity_id=0
        self.entity_names={}
        self.last_res_id=0
        self.resource_names={}
        self.run_number=0
        self.finishedTime=[]
 
    def create_entities(self,name,total_number,print_actions=False,log=True):
        """
        Create entities by making instances of class entity and adding them to the environemnt.
        All the entities are created at the current simulation time: env.now

        Parameters
        ----------
        name : string
            Name of the entities, the name of each entity would be name_0, name_1, ...
        print_actions : bool
            If equal to True, the actions of the entities will be printed in console
        log: bool
            If equals True, various statistics will be collected for the entities

        Returns
        -------
        list of entitiy
            A list containing all the created entities
        """
        Entities=[]
        for i in range(total_number):
            Entities.append(entity(self,name,print_actions,log))
        return Entities



 