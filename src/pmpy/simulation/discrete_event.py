'''
Discrete Event Simulation for Project Management in Python.
'''

import simpy
from numpy import array, append
from pandas import DataFrame
from bisect import insort_left
from pmpy.simulation.distributions import distribution

'''
*****************************************
*****entity class*******************
*****************************************
'''
def _switch_dic(dic):
    '''
    siwtch key and value in a dictionary

    '''
    newdic={}
    for key in dic:
        newdic[dic[key]]=key
    return newdic

class entity:
    '''
    A class that defines an entity. Entities are virtual objects essential to useful for modeling dynamic systems. 
    Some examples of entities can be: a customer, communication message, or any resource requiring service.

    ...
    Attributes
    ----------
    name: str
        Name of the entity
    id: int
        A unique id for the entity in the environment
    env: pmpy.environment
        The environemnt in which the entity is defined in
    attr: dict
        a dictionay containting all the special attributes defined for the entity.
    '''
    def __init__(self,env,name,print_actions=False,log=True):
        '''
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
        '''
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
        self.usingResources={}

        #***logs
        self._schedule_log=array([[0,0,0]])#act_id,act_start_time,act_finish_time
        self._status_codes={'wait for':1,'get':2,'start':3,'finish':4,'put':5,'add':6}
        self._status_log=array([[0,0,0]])#time,entity_status_code,actid/resid
        self._waiting_log=array([[0,0,0,0]]) #resource_id,start_waiting,end_waiting,amount waiting for

        if print_actions:
            print(name+'('+str(self.id)+') is created, sim_time:',env.now)

      
    def _activity(self,name,duration):
        '''
        This method defines the activity that the entity is doing.

        Parameters
        ----------
        name : string
            Name of the activty
        Duration : float, int, or distribution
            The duration of that activity
        '''
        if isinstance(duration,distribution):
            d=-1
            while d<0:
                d=duration.sample()
            duration=d
        if self.print_actions:
            print(self.name+'('+str(self.id)+ ') start',name,', sim_time:',self.env.now)
        
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

    def do(self,name,dur):
        '''
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
        '''
        try:
            if isinstance(dur,distribution):
                d=-1
                while d<0:
                    d=dur.sample()
                dur=d
       
            return self.env.process(self._activity(name,dur))
        except:
            print('pmpy: error in do')


    def get(self,res,amount,priority=1,preemp=False):
        '''
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
        '''
        try:
            if isinstance(amount,distribution):
                a=-1
                while a<0:
                    a=amount.sample()
                amount=a
            if type(res)==resource:
                return self.env.process(res.get(self,amount))
            elif type(res)==priority_resource:
                return self.env.process(res.get(self,amount,priority))
            elif type(res)==preemptive_resource:
                return self.env.process(res.get(self,amount,priority,preemp))
        except:
            print('pmpy: error in get')

    def add(self,res,amount):
        '''
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
        '''
        if isinstance(amount,distribution):
            a=-1
            while a<0:
                a=amount.sample() #?can this amount be float!
            amount=a
        return self.env.process(res.add(self,amount))

    def put(self,res,amount):
        '''
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
        '''
        if isinstance(amount,distribution):
            a=-1
            while a<0:
                a=amount.sample()
            amount=a
        return self.env.process(res.put(self,amount))

    def schedule(self):
        '''

        Returns
        -------
        pandas.DataFrame
            The schedule of each entity.
            The columns are activity name, and start time and finish time of that activity
        '''
        df=DataFrame(data=self._schedule_log,columns=['activity','start_time','finish_time'])
        df['activity']=df['activity'].map(_switch_dic(self.act_dic))
        return df

    def waiting_log(self):
        '''

        Returns
        -------
        pandas.DataFrame
            The time the activty started waiting and the time it finished waiting.
            The columns show the resource name for which the entity is waiting for, time when watiting is started, 
            time when waiting is finished, and the number of resources the entity is waiting for
        '''
        df=DataFrame(data=self._waiting_log,columns=['resource','start_waiting','end_waiting','resource_amount'])
        df['resource']=(df['resource'].map(self.env.resource_names))
        return df


    def waiting_time(self):
        '''

        Returns
        -------
        numpy.array
            The waiting durations of the entity each time it waited for a resource
        '''
        a=self._waiting_log()
        a=a['end_waiting']-a['start_waiting']
        return a.values
        
    def status_log(self):
        '''

        Returns
        -------
        pandas.DataFrame
            Any change in the status of an entity, the change can be either
            waiting for a resourcing, getting a reouces, putting a resource back, or adding to a resouce, 
            or it can be starting or finishing an activity
        '''
        df=DataFrame(data=self._status_log,columns=['time','status','actid/resid'])
        df['status']=df['status'].map(_switch_dic(self._status_codes))
        
        return df
'''
*****************************************
*****Resource Class*******************
*****************************************
'''
class general_resource():
    '''
    The parent class for all of pmpy.resources
    '''
    def __init__(self,env,name,capacity,init,print_actions=False,log=True):
        '''
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
        '''
        self.name=name
        self.env=env 
        self.log=log
        self.print_actions=print_actions
        env.last_res_id+=1
        self.id=env.last_res_id
        env.resource_names[self.id]=self.name+'('+str(self.id)+')'
        self._in_use=0
        self.container=simpy.Container(env, capacity,init)
        self.queue_length=0
        
        #logs
        self.__status_log=array([[0,0,0,0]])#time,in-use,idle,queue-lenthg
        self.__queue_log=array([[0,0,0,0]])#entityid,startTime,endTime,amount


    def queue_log(self):
        '''

        Returns
        -------
        pandas.DataFrame
            All entities who are wiaitng in for the resource, their start time and
            finish time of waiting are stored in this DataFrame
        '''
        df=DataFrame(data=self.__queue_log,columns=['entity','start_time','finish_time','resource_amount'])
        df['entity']=df['entity'].map(self.env.entity_names)
        return df

    def status_log(self):
        '''

        Returns
        -------
        pandas.DataFrame
            Any changes in the status of the resource and the time of the change is presented 
            in this DataFrame. The recorded statuses are number of in-use resources ,
            number of idle resources, and number of entities waiting for the resoruce. 
        '''
        df=DataFrame(data=self.__status_log,columns=['time','in_use','idle','queue_lenthg'])
        return df

    
    def _request(self,entity,amount):
        '''
        Calculate needed logs when an entity requests the resource.

        Parameters
        ----------
        entity : pmpy.entity
            The entity requesting the resource 
        amount : int
            The number of requested resouces 
        '''
        self.queue_length+=1
        if self.print_actions or entity.print_actions:
            print(entity.name+'('+str(entity.id)+')'
                  +' requested',str(amount),self.name+'(s), sim_time:',self.env.now)
        if self.log:
            self.__status_log=append(self.__status_log,[[self.env.now,self._in_use,self.container.level,self.queue_length]],axis=0)
        if entity.log:
            entity.status_log=append(entity.status_log,[[self.env.now,entity._status_codes['wait for'],self.id]],axis=0)

    def _get(self,entity,amount):
        '''
        Calculate needed logs when an entity got the resource.

        Parameters
        ----------
        entity : pmpy.entity
            The entity getting the resource 
        amount : int
            The number of taken resouces 
        '''
        self.queue_length-=1
        self._in_use+=amount
        if self.print_actions or entity.print_actions:
            print(entity.name+'('+str(entity.id)+')'
                  +' got '+str(amount),self.name+'(s), sim_time:',self.env.now)
        if self.log:
            self.__status_log=append(self.__status_log,[[self.env.now,self._in_use,self.container.level,self.queue_length]],axis=0)
        if entity.log:
            entity.status_log=append(entity.status_log,[[self.env.now,entity._status_codes['get'],self.id]],axis=0)
        entity.usingResources[self]=amount

    def _add(self,entity,amount):
        '''
        Calculate needed logs when an entity add to the resource.

        Parameters
        ----------
        entity : pmpy.entity
            The entity adding the resource 
        amount : int
            The number of added resouces 
        '''
        if self.print_actions or entity.print_actions:
            print(entity.name+'('+str(entity.id)+')'
                  +' add '+str(amount),self.name+'(s), sim_time:',self.env.now)
        if self.log:
            self.__status_log=append(self.__status_log,[[self.env.now,self._in_use,self.container.level,self.queue_length]],axis=0)
        if entity.log:
            entity.status_log=append(entity.status_log,[[entity._status_codes['add'],self.id,self.env.now]],axis=0)

    def _put(self,entity,amount):
        '''
        Calculate needed logs when an entity add to the resource.

        Parameters
        ----------
        res : pmpy.entity
            The entity putting the resource back
        amount : int
            The number of resouces being put back
        '''
        if self not in entity.usingResources:
            raise Warning(entity.name, "did not got ", self.name,"to put it back")
        if self in entity.usingResources and entity.usingResources[self]<amount:
            raise Warning(entity.name, "did not got this many of",self.name, "to put it back")
        entity.usingResources[self]=entity.usingResources[self]-amount
        self._in_use-=amount
        if self.print_actions or entity.print_actions:
            print(entity.name+'('+str(entity.id)+')'
                  +' put back '+str(amount),self.name+'(s), sim_time:',self.env.now)
        if self.log:
            self.__status_log=append(self.__status_log,[[self.env.now,self._in_use,self.container.level,self.queue_length]],axis=0)
        if entity.log:
            entity.status_log=append(entity.status_log,[[entity._status_codes['put'],self.id,self.env.now]],axis=0)
        
    def level(self):
        '''

        Returns
        -------
        int
            The number of resources that are currently availbale
        '''
        return self.container.level

    def idle(self):
        '''

        Returns
        -------
        int
            The number of resources that are currently availbale

        '''
        return self.level()

    def in_use(self):
        '''

        Returns
        -------
        int
            The number of resources that are currently in-use

        '''
        return self._in_use     

    def capacity(self):
        '''

        Returns
        -------
        int
            The maximum capacity for the reource
        '''
        return self.container.capacity



class resource(general_resource):
    '''
    A class to represent a normal resource in discrete event simulation.
    ...
    Attributes
    ----------
    env:pmpy.environment
        The environment for the entity
    name : string
        Name of the resource
    id : int
        A unique id for the resource in the environment
    capacity: int
        Maximum capacity for the resource
    init: int
        Initial number of resources
    print_actions : bool
        If equal to True, the changes in the resource will be printed in console
    log: bool
        If equals True, various statistics will be collected for the resource
    '''
    def __init__(self,env,name, init=1,capacity=1000,print_actions=False,log=True):
        '''
        Creates an intstance of a pmpy general resource.

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
        '''
        super().__init__(env,name,capacity,init,print_actions,log)
        self.requests=[]

    def get(self,entity,amount):
        '''
        A method for getting(capturing) the resoruce by the entity.

        Parameters
        ----------
        entity : pmpy.entity
            The entity adding the resource 
        amount : int
            The number of resouces to be captured
        '''
        super()._request(entity,amount)
   
        start_waiting=self.env.now
        yield self.container.get(amount)
        super()._get(entity,amount)
        if self.log:
            self.__queue_log=append(self.__queue_log,[[entity.id,start_waiting,self.env.now,amount]],axis=0)
        if entity.log:
            entity.waiting_log=append(entity.waiting_log,[[self.id,start_waiting,self.env.now,amount]],axis=0)
          
            
    def add(self,entity,amount):
        '''
        A method for adding the resoruce by the entity.

        Parameters
        ----------
        entity : pmpy.entity
            The entity adding the resource 
        amount : int
            The number of resouces to be added
        '''
        yield self.container.put(amount)
        super()._add(entity,amount)

    def put(self,entity,amount):
        '''
        A method for putting back(releasing) the resoruce by the entity.

        Parameters
        ----------
        entity : pmpy.entity
            The entity putting back the resource 
        amount : int
            The number of resouces to be put back
        '''
        yield self.container.put(amount)
        super()._put(entity,amount)
        
class priority_request():
    '''
    A class defining the a priority request for capturing the resoruces.
    This class allows to keep all the requests in a sorted list of requests.
    '''
    def __init__(self,entity,amount,priority):
        self.time=entity.env.now
        self.entity=entity
        self.amount=amount
        self.priority=priority
        self.flag=simpy.Container(entity.env,init=0)#show if the resource is obtained
        
    def __gt__(self,other_request):
        '''
        Decides if a resoruce request has a higher priority than antothe resource request
        Lower priority values show higher priority!
        If the priority of two requests is equal and are made at the same time,
        the request with lower number of needed resources will have a higher priority.
        '''
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
        '''
        Defines a resource for which a priroty que is implemented. 

        '''
        super().__init__(env,name,capacity,init,print_actions,log)
        
        self.resource=simpy.PriorityResource(env,1)
        self.requestlist=[]

    def get(self,entity,amount,priority=1):
        '''
        A method for getting the resource. 

        Parameters
        ----------
        entity : pmpy.entity
            The entity adding the resource 
        amount : int
            The number of resouces to be added
        priority : int
            lower values for this input show higher priority
        ''' 
        super()._request(entity,amount)
        pr=priority_request(entity,amount,priority)
        insort_left(self.requestlist,pr)
        yield self.env.timeout(0) #? why do we need this?
        yield entity.env.process(self._check_all_requests())
        yield pr.flag.get(1) #flag shows that the resource is granted
        
    def _check_all_requests(self):
        '''
        Check to see if any rquest for the resource can be granted.
        '''
        while len(self.requestlist)>0 and self.requestlist[-1].amount<=self.container.level:
            r=self.requestlist.pop()
            yield self.container.get(r.amount)
            r.flag.put(1)
            super()._get(r.entity,r.amount)
            if self.log:
                self.__queue_log=append(self.__queue_log,[[r.entity.id,r.time,self.env.now,r.amount]],axis=0)
            if r.entity.log:
                r.entity.waiting_log=append(r.entity.waiting_log,[[self.id,r.time,self.env.now,r.amount]],axis=0)
            
    def add(self,entity,amount):
        '''
        A method for adding the resoruce by the entity.

        Parameters
        ----------
        entity : pmpy.entity
            The entity adding the resource 
        amount : int
            The number of resouces to be added
        '''
        yield self.container.put(amount)
        super()._add(entity,amount)
        return entity.env.process(self._check_all_requests())

    def put(self,entity,amount):
        '''
        A method for putting back the resoruce by the entity.

        Parameters
        ----------
        entity : pmpy.entity
            The entity adding the resource 
        amount : int
            The number of resouces to be added
        '''
        yield self.container.put(amount)
        super()._put(entity,amount)
        return entity.env.process(self._check_all_requests())

class preemptive_resource(priority_resource):
    '''
    this class is to be implemented.
    '''
    pass
    
'''
*****************************************
*****Environment Class*******************
*****************************************
'''
class environment(simpy.Environment):
    '''
    This class defines the simulation environment. 
    All of the processes, entities and resources are defined in this class. 
    '''
    def __init__(self):
        '''
        Creates an instance of the simulation environment
        '''
        super().__init__()
        self.last_entity_id=0
        self.entity_names={}
        self.last_res_id=0
        self.resource_names={}
        self.run_number=0
        self.finishedTime=[]
 
    def create_entities(self,name,total_number,print_actions=False,log=True):
        '''
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
        '''
        Entities=[]
        for i in range(total_number):
            Entities.append(entity(self,name,print_actions,log))
        return Entities

    def create(self,name,time_between_arrivals,number_arrived_each_time,process,resource_list,number_of_arrivals=10000000,print_actions=False,log=True):
        '''
        Create entities by making instances of class Entity and adding them to the environemnt.
        The entities are created during the simulation based on the given time intervals.
        Right after the creation, the processes of the entity should be added to the environment so that the 
        entities start taking actions.

        Parameters
        ----------
        name : string
            Name of the entities, the name of each entity would be name_0, name_1, ...
        time_between_arrivals : float
            Time btween arrival of the entity batches
        number_arrived_each_time : int
            The number of entities created each time, i.e. batch size
        process: func
            The name of the function that specifies the process for the entity
        resource_list : list of pmpy.resource
            List of resources that is the input to the function "process"    
        number_of_arrivals:
            The maximum number of times the entity batches are created
        print_actions : bool
            If equal to True, the actions of the entities will be printed in console
        log: bool
            If equals True, various statistics will be collected for the entities
     
        '''
        for i in range(number_of_arrivals):
            a=self.create_entities(name,number_arrived_each_time,print_actions)
            for e in a:
                self.process(process(e,resource_list)) 
            yield self.timeout(time_between_arrivals)
 
    

'''
*****************************
********future works*********
*****************************
'''
#visualiziation
#graphs of logs
#preempt for breakdown
#Or between resource requests
#input checks
### check each entity should be given to only one process and one environment
#create tests
