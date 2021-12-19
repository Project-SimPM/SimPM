"""
Discrete Event Simulation for Project Management in Python.
"""
import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir) 

import simpy
from numpy import array, append
from pandas import DataFrame
from bisect import insort_left
import matplotlib.pyplot as plt
from pmpy.dist import distribution
from matplotlib import animation, lines
import pmpy.des as des


"""
*****************************************
*****agent class*******************
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
class agent_type():
    def __init__(self,name,shape):
        self.shape=shape
        self.name=name
        self.agents=[]
    def xy_list(self):
        xlist=[]
        ylist=[]
        for a in self.agents:
           xlist.append(a.x) 
           ylist.append(a.y)
        return xlist,ylist
        
        
class agent(des.entity):
    """
    A class that defines an Agents. Agents are virtual objects essential to useful for modeling dynamic systems. 
    Some examples of Agents can be: a customer, communication message, or any resource requiring service.

    ...
    Attributes
    ----------
    name: str
        Name of the agent
    id: int
        A unique id for the agent in the environment
    env: pmpy.abs.environment
        The environemnt in which the agent is defined in
    attr: dict
        a dictionay containting all the special attributes defined for the agent.
    shape : string
        the shape of agent in matplotlib
    x:location x
        the location x of agent in the environment
    y: location y
        the location y of the agent in the environment
    """
    def __init__(self,env:des.environment,type:agent_type,location=(0,0),print_actions=False,log=True):
        """
        Creates an new instance for agent.

        Parameters
        ----------
        env:pmpy.environment
            The environment for the agent
        name : string
            Name of the agent
        shape : string
            the shape of agent in matplotlib
        location:(x,y)
            the location of agent in the environment
        print_actions : bool
            If equal to True, the actions of the agent will be printed in console
        log: bool
            If equals True, various statistics will be collected for the agent
        
        """
        super().__init__(env,type.name,print_actions,log)
        
        self.env=env
        self.name=type.name
        self.x=location[0]
        self.y=location[1]
        self.agent_type=type
        self.name=type.name
        self.agent_type.agents.append(self)
    
        if type not in self.env.agents:
            self.env.agents.append(type)

    def _move(self,move_name,speed,vector):
        '''
        move the age using the vecor

        Parameters
        ----------
        move_name: str
            name of the move
        speed: double
            move_amount per simulation time unit
        '''
        initial_x=self.x
        initial_y=self.y
        for point in vector:
            destination=point
            dirx=destination[0]-initial_x
            diry=destination[1]-initial_y
            alpha=((self.x*self.x+self.y*self.y)/(speed*speed))**(.5)
            while  (self.x-destination[0])**2+(self.y-destination[1])**2>(0.5)**2:
                yield self.env.timeout(1)
                self.x+=dirx/alpha
                self.y+=diry/alpha
            self.x=destination[0]
            self.y=destination[1]
            initial_x=self.x
            initial_y=self.y
    
    def move(self,move_name,speed,vector):
        '''
        move the age using the vecor

        Parameters
        ----------
        move_name: str
            name of the move
        speed: double
            move_amount per simulation time unit
        '''
        return self.env.process(self._move(move_name,speed,vector))
    

    def get(self,res,amount=1,priority=1,preempt:bool=False):
        """
        Agent requests to get a resource using this method. 

        Parameters
        ----------
        res : pmpy.resource
            the resource to be captured by the agent
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
        return super().get(res,amount,priority,preempt)

    def add(self,res,amount=1):
        """
        Agent increases the number of resources using this method.

        Parameters
        ----------
        res : pmpy.resource
            the resource to be added by the agent
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
        Agent puts back the resources using this method.

        Parameters
        ----------
        res : pmpy.resource
            the resource to be added by the agent
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
                return self.env.process(res.put(self))
        return self.env.process(res.put(self,request))
    def is_pending(self,res,amount:int=1):
        """

        Parameters:
        -----------
        res : resource
            Resource for which the eneity is waiting for.
        amount: int
            Number of resources that the agent is waiting for.
            If the number of entities is not specified, waiting for any number of resources is ok

        Returns
        --------
        True if agent is waiting for the resource, and False if the agent is not waiting for the resource
        """

        for r in res.request_list:
            if r.agent==self and r.amount==amount:
                return True
        return False

    def not_pending(self,res,amount:int=1):
        """

        Parameters:
        -----------
        res : resource
            Resource for which the eneity is waiting for.
        amount: int
            Number of resources that the agent is waiting for.
            If the number of entities is not specified, waiting for any number of resources is ok

        Returns
        --------
        Flase if the entitiy is not waiting for the resource, and True if the agent is not waiting for the resource
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
            Number of resources that the agent is waiting for.
            If the number of entities is not specified, waiting for any number of resources is ok

  
         """

        for r in res.request_list:
            if r.agent==self and r.amount==amount:
                res.cancel(r)
                return 
        
        self.put(res,amount) #a problem may occur of someone adds to the resouce meanwhile we are canceling
        
                    
    def schedule(self):
        """

        Returns
        -------
        pandas.DataFrame
            The schedule of each agent.
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
            The time the agent started waiting and the time it finished waiting.
            The columns show the resource name for which the agent is waiting for, time when waiting is started, 
            time when waiting is finished, and the number of resources the agent is waiting for
        """
        df=DataFrame(data=self._waiting_log[1: , :],columns=['resource','start_waiting','end_waiting','resource_amount'])
        df['resource']=(df['resource'].map(self.env.resource_names))
        return df


    def waiting_time(self):
        """

        Returns
        -------
        numpy.array
            The waiting durations of the agent each time it waited for a resource
        """
        a=self.waiting_log()
        a=a['end_waiting']-a['start_waiting']
        return a.values
        
    def status_log(self):
        """

        Returns
        -------
        pandas.DataFrame
            shows any change in the status of an agent, the change can be either
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
            The environment for the agent
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
        self.container=simpy.Container(env, capacity,init)
        self.queue_length=0 #number of entities waiting for a resource
        self.request_list=[]
        self.attr={} #attributes for resoruces
        
        #logs
        self._status_log=array([[0,0,0,0]])#time,in-use,idle,queue-length
        self._queue_log=array([[0,0,0,0]])#agentid,startTime,endTime,amount


    def queue_log(self):
        """

        Returns
        -------
        pandas.DataFrame
            All entities waiting for the resource, their start waiting time and
            finish waiting time are stored in this DataFrame
        """
        df=DataFrame(data=self._queue_log[1: , :],columns=['agent','start_time','finish_time','resource_amount'])
        df['agent']=df['agent'].map(self.env.agent_names)
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
        
    def _request(self,agent,amount):
        """
        Calculate needed logs when an agent requests the resource.

        Parameters
        ----------
        agent : pmpy.agent
            The agent requesting the resource 
        amount : int
            The number of requested resouces 
        """
        self.queue_length+=1
        if self.print_actions or agent.print_actions:
            print(agent.name+'('+str(agent.id)+')'
                  +' requested',str(amount),self.name+'(s)'+'('+str(self.id)+')'+', sim_time:',self.env.now)
        if self.log:
            self._status_log=append(self._status_log,[[self.env.now,self.in_use,self.container.level,self.queue_length]],axis=0)
        if agent.log:
            agent._status_log=append(agent._status_log,[[self.env.now,agent._status_codes['wait for'],self.id]],axis=0)

    def _get(self,agent,amount):
        """
        Calculate needed logs when an agent got the resource.

        Parameters
        ----------
        agent : pmpy.agent
            The agent getting the resource 
        amount : int
            The number of taken resouces 
        """
        self.queue_length-=1
        self.in_use+=amount
        if self.print_actions or agent.print_actions:
            print(agent.name+'('+str(agent.id)+')'
                  +' got '+str(amount),self.name+'(s)'+'('+str(self.id)+')'+', sim_time:',self.env.now)
        if self.log:
            self._status_log=append(self._status_log,[[self.env.now,self.in_use,self.container.level,self.queue_length]],axis=0)
        if agent.log:
            agent._status_log=append(agent._status_log,[[self.env.now,agent._status_codes['get'],self.id]],axis=0)
        agent.using_resources[self]=amount

    def _add(self,agent,amount):
        """
        Calculate needed logs when an agent add to the resource.

        Parameters
        ----------
        agent : pmpy.agent
            The agent adding the resource 
        amount : int
            The number of added resouces 
        """
        if self.print_actions or agent.print_actions:
            print(agent.name+'('+str(agent.id)+')'
                  +' added '+str(amount),self.name+'(s)'+'('+str(self.id)+')'+', sim_time:',self.env.now)
        if self.log:
            self._status_log=append(self._status_log,[[self.env.now,self.in_use,self.container.level,self.queue_length]],axis=0)
        if agent.log:
            agent._status_log=append(agent._status_log,[[agent._status_codes['add'],self.id,self.env.now]],axis=0)

    def _put(self,agent,amount):
        """
        Calculate needed logs when an agent add to the resource.

        Parameters
        ----------
        res : pmpy.agent
            The agent putting the resource back
        amount : int
            The number of resouces being put back
        """
        if self not in agent.using_resources:
            raise Warning(agent.name, "did not got ", self.name,"to put it back")
        if self in agent.using_resources and agent.using_resources[self]<amount:
            raise Warning(agent.name, "did not got this many of",self.name, "to put it back")
        agent.using_resources[self]=agent.using_resources[self]-amount
        self.in_use-=amount
        if self.print_actions or agent.print_actions:
            print(agent.name+'('+str(agent.id)+')'
                  +' put back '+str(amount),self.name+'(s)'+'('+str(self.id)+')'+', sim_time:',self.env.now)
        if self.log:
            self._status_log=append(self._status_log,[[self.env.now,self.in_use,self.container.level,self.queue_length]],axis=0)
        if agent.log:
            agent._status_log=append(agent._status_log,[[agent._status_codes['put'],self.id,self.env.now]],axis=0)
        
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
            The average waiting queue length for a resource
        """
        return sum(self.waiting_time())/(self.env.now)

class request():
    """
    A class defining the a priority request for capturing the resources.
    This class allows to keep all the requests in a sorted list of requests.
    """
    def __init__(self,agent,amount):
        self.time=agent.env.now
        self.agent=agent
        self.amount=amount
        self.flag=simpy.Container(agent.env,init=0)#show if the resource is obtained when flag truns 1
        
    

class resource(general_resource):
    def __init__(self,env,name, init=1,capacity=1000,print_actions=False,log=True):
        """
        Defines a resource for which a priority queue is implemented. 

        Parameters
        ----------
        env:pmpy.environment
            The environment for the agent
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
       

    def get(self,agent,amount):
        """
        A method for getting the resource. 

        Parameters
        ----------
        agent : pmpy.agent
            The agent adding the resource 
        amount : int
            The number of resouces to be added
        priority : int
            lower values for this input show higher priority
        """ 
        super()._request(agent,amount)
        pr=request(agent,amount)
        agent.pending_requests.append(pr) #append priority request to the eneity
        self.request_list.append(pr)
        yield self.env.timeout(0) #? why do we need this?
        yield agent.env.process(self._check_all_requests())
        yield pr.flag.get(1) #flag shows that the resource is granted
        
    def _check_all_requests(self):
        """
        Check to see if any rquest for the resource can be granted.
        """
        while len(self.request_list)>0 and self.request_list[0].amount<=self.container.level:
            r=self.request_list.pop(0) #remove the first element from the list
            simpy_request=self.container.get(r.amount)
            yield simpy_request
            r.agent.pending_requests.remove(r)
            r.flag.put(1)
            super()._get(r.agent,r.amount)
            if self.log:
                self._queue_log=append(self._queue_log,[[r.agent.id,r.time,self.env.now,r.amount]],axis=0)
            if r.agent.log:
                r.agent._waiting_log=append(r.agent._waiting_log,[[self.id,r.time,self.env.now,r.amount]],axis=0)

    def cancel(self,priority_request):
        if request in self.request_list:
            self.request_list.remove(priority_request)
        else:
            print("warning: the request can not be cancled as it is not in the request list")


    def add(self,agent,amount):
        """
        A method for adding the resource by the agent.

        Parameters
        ----------
        agent : pmpy.agent
            The agent adding the resource 
        amount : int
            The number of resouces to be added
        """
        yield self.container.put(amount)
        super()._add(agent,amount)
        return agent.env.process(self._check_all_requests())

    def put(self,agent,amount):
        """
        A method for putting back the resource by the agent.

        Parameters
        ----------
        agent : pmpy.agent
            The agent adding the resource 
        amount : int
            The number of resouces to be added
        """
        yield self.container.put(amount)
        super()._put(agent,amount)
        return agent.env.process(self._check_all_requests())

        
class priority_request():
    """
    A class defining the a priority request for capturing the resources.
    This class allows to keep all the requests in a sorted list of requests.
    """
    def __init__(self,agent,amount,priority):
        self.time=agent.env.now
        self.agent=agent
        self.amount=amount
        self.priority=priority
        self.flag=simpy.Container(agent.env,init=0)#show if the resource is obtained
        
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
            The environment for the agent
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
       

    def get(self,agent,amount,priority=1):
        """
        A method for getting the resource. 

        Parameters
        ----------
        agent : pmpy.agent
            The agent adding the resource 
        amount : int
            The number of resouces to be added
        priority : int
            lower values for this input show higher priority
        """ 
        super()._request(agent,amount)
        pr=priority_request(agent,amount,priority)
        agent.pending_requests.append(pr) #append priority request to the eneity
        insort_left(self.request_list,pr)
        yield self.env.timeout(0) #? why do we need this?
        yield agent.env.process(self._check_all_requests())
        yield pr.flag.get(1) #flag shows that the resource is granted
        
    def _check_all_requests(self):
        """
        Check to see if any rquest for the resource can be granted.
        """
        while len(self.request_list)>0 and self.request_list[-1].amount<=self.container.level:
            r=self.request_list.pop()
            yield self.container.get(r.amount)
            r.agent.pending_requests.remove(r)
            r.flag.put(1)
            super()._get(r.agent,r.amount)
            if self.log:
                self._queue_log=append(self._queue_log,[[r.agent.id,r.time,self.env.now,r.amount]],axis=0)
            if r.agent.log:
                r.agent._waiting_log=append(r.agent._waiting_log,[[self.id,r.time,self.env.now,r.amount]],axis=0)

    def cancel(self,priority_request):
        if priority_request in self.request_list:
            self.request_list.remove(priority_request)
        else:
            print("warning: the priority request can not be cancled as it is not in the request list")


    def add(self,agent,amount):
        """
        A method for adding the resource by the agent.

        Parameters
        ----------
        agent : pmpy.agent
            The agent adding the resource 
        amount : int
            The number of resouces to be added
        """
        yield self.container.put(amount)
        super()._add(agent,amount)
        return agent.env.process(self._check_all_requests())

    def put(self,agent,amount):
        """
        A method for putting back the resource by the agent.

        Parameters
        ----------
        agent : pmpy.agent
            The agent adding the resource 
        amount : int
            The number of resouces to be added
        """
        yield self.container.put(amount)
        super()._put(agent,amount)
        return agent.env.process(self._check_all_requests())

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
            The environment for the agent
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
        self.request=None #the request of the agent that is currently using the resource
        self.current_entities=None
        self.suspended_entities=None
        
    def get(self,agent,priority: int,preempt:bool=False):
        super()._request(agent,1)
        while True:
            try:
                r=self.resource.request(priority,preempt)
                return r
            except:
                print("resource is preempted")
            
        self.request=r #the request that is currently using the rsource
        super()._get(agent,1)

    def put(self,agent,request=None):
        #to be added: when waiting to ptu pack soemthing some logs should be calculated
        yield self.resource.release(request)
        super()._put(agent,1)

    
    
"""
*****************************************
*****Environment Class*******************
*****************************************
"""
class environment(des.environment):
    """
    This class defines the simulation environment. 
    All of the processes, entities and resources are defined in this class. 

    Attributes
    ----------
    now : float
        current simulation time
    width: int
        width of the environment
    hight: int
        hight of the environment
    agents:list
        list of all agents created in the environment
    """
    def __init__(self,xrange=(0,100),yrange=(0,100)):
        """
        Creates an instance of the simulation environment
        width: int
            width of the environment
        hight: int
            hight of the environment

        """
        super().__init__()
        self.fig = plt.figure()
        self.ax = plt.axes(xlim=xrange, ylim=yrange)
   
        self.lines=[]
        self.agents=[]
        self.agents_xloc={} #key is the name and value is list of x values of those agents
        self.agents_yloc={} #key is the name and value is list of y values of those agents
 
    def create_agents(self,name,total_number,shape='o',location=(0,0),print_actions=False,log=True):
        """
        Create entities by making instances of class agent and adding them to the environemnt.
        All the entities are created at the current simulation time: env.now

        Parameters
        ----------
        name : string
            Name of the agents
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
            Entities.append(agent(self,name,shape,location,print_actions,log))
        return Entities



    def run(self):
        for a in self.agents:
            line, = self.ax.plot([], [],a.shape,label=a.name)
            self.lines.append(line)
        
        def animate(k:int):
            self.step()
            for i in range (len(self.agents)):
                data=self.agents[i].xy_list()
                self.lines[i].set_data(data[0],data[1])
            return self.lines

        self.anim = animation.FuncAnimation(self.fig, animate,
                               frames=2000, interval=10, blit=True)

        self.ax.legend()
        plt.show(block=True)

        
        '''
# initialization function: plot the background of each frame
def init():
    line.set_data([], [])
    return line,

# animation function.  This is called sequentially
def animate(i:int):
    x = np.linspace(0, 2, 10)
    y = np.sin(2 * np.pi * (x - 0.01 * i))
    line.set_data(x, y)
    return line,

# call the animator.  blit=True means only re-draw the parts that have changed.
anim = animation.FuncAnimation(fig, animate, init_func=init,
                               frames=2000, interval=10, blit=True)

# save the animation as an mp4.  This requires ffmpeg or mencoder to be
# installed.  The extra_args ensure that the x264 codec is used, so that
# the video can be embedded in html5.  You may need to adjust this for
# your system: for more information, see
# http://matplotlib.sourceforge.net/api/animation_api.html
#anim.save('basic_animation.mp4', fps=30, extra_args=['-vcodec', 'libx264'])
'''



        
