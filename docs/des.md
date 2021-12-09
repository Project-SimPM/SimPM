# des




Discrete Event Simulation for Project Management in Python.
*****************************************
*****entity class*******************
*****************************************

#### Classes

 Class  | Doc
-----|-----
 entity |
 general_resource() |
 request() |
 resource(general_resource) |
 priority_request() |
 priority_resource(general_resource) |
 preemptive_resource(general_resource) |
 environment(simpy.Environment) |

#### Functions

 Function  | Doc
-----|-----
 _switch_dic |




### _switch_dic

```python
def _switch_dic(dic)
```




siwtch key and value in a dictionary






## entity

```python
class entity
```




A class that defines an entity. Entities are virtual objects essential to useful for modeling dynamic systems. 
Some examples of entities can be: a customer, communication message, or any resource requiring service.

...

#### Attributes

 Attribute  | Type  | Doc
-----|----------|-----
 name |  str | Name of the entity
 id |  int | A unique id for the entity in the environment
 env |  pmpy.environment | The environemnt in which the entity is defined in
 attr |  dict | a dictionay containting all the special attributes defined for the entity.

#### Methods

 Method  | Doc
-----|-----
 _activity |
 do |
 get |
 add |
 put |
 is_pending |
 not_pending |
 cancel |
 schedule |
 waiting_log |
 waiting_time |
 status_log |




### __init__

```python
def __init__(self,env,name,print_actions=False,log=True)
```




Creates an new instance for entity.


#### Parameters

 Parameter  | Type  | Doc
-----|----------|-----
 env | pmpy.environment | The environment for the entity
 name  |  string | Name of the entity
 print_actions  |  bool | If equal to True, the actions of the entity will be printed in console
 log |  bool | If equals True, various statistics will be collected for the entity





### _activity

```python
def _activity(self,name,duration)
```




This method defines the activity that the entity is doing.


#### Parameters

 Parameter  | Type  | Doc
-----|----------|-----
 name  |  string | Name of the activty
 Duration  |  float, int, or distribution | The duration of that activity





### do

```python
def do(self,name,dur)
```




Defines the activity that the entity is doing.


#### Parameters

 Parameter  | Type  | Doc
-----|----------|-----
 name  |  string | Name of the activity
 duration  |  float , int, or distribution | The duration of that activity

#### Returns

 Return Variable  | Type  | Doc
-----|----------|-----
 Unknown | Environment.process | the process for the activity





### get

```python
def get(self,res,amount=1,priority=1,preempt:bool=False)
```




Entity requests to get a resource using this method. 


#### Parameters

 Parameter  | Type  | Doc
-----|----------|-----
 res  |  pmpy.resource | the resource to be captured by the entity
 amount  |   int | The number of resouces to be captured
 priority  |  int | The priority of the request for getting the resource
 preempt  |  bool | Preemptive resources are not yet implemented

#### Returns

 Return Variable  | Type  | Doc
-----|----------|-----
 Unknown | pmpy.environment.process | The process for the request





### add

```python
def add(self,res,amount=1)
```




Entity increases the number of resources using this method.


#### Parameters

 Parameter  | Type  | Doc
-----|----------|-----
 res  |  pmpy.resource | the resource to be added by the entity
 amount  |   int | The number of resouces to be added

#### Returns

 Return Variable  | Type  | Doc
-----|----------|-----
 Unknown | pmpy.environment.process | The process for adding resources





### put

```python
def put(self,res,amount=1)
```




Entity puts back the resources using this method.


#### Parameters

 Parameter  | Type  | Doc
-----|----------|-----
 res  |  pmpy.resource | the resource to be added by the entity
 amount  |   int | The number of resouces to be put back

#### Returns

 Return Variable  | Type  | Doc
-----|----------|-----
 Unknown | pmpy.environment.process | The process for putting back the resources





### is_pending

```python
def is_pending(self,res,amount:int=1)
```





Parameters:
-----------
res : resource
Resource for which the eneity is waiting for.
amount: int
Number of resources that the entity is waiting for.
If the number of entities is not specified, waiting for any number of resources is ok


#### Returns

 Return Variable  | Type  | Doc
-----|----------|-----
 Unknown | True if entity is waiting for the resource, and False if the entity is not waiting for the resource | Unknown





### not_pending

```python
def not_pending(self,res,amount:int=1)
```





Parameters:
-----------
res : resource
Resource for which the eneity is waiting for.
amount: int
Number of resources that the entity is waiting for.
If the number of entities is not specified, waiting for any number of resources is ok


#### Returns

 Return Variable  | Type  | Doc
-----|----------|-----
 Unknown | Flase if the entitiy is not waiting for the resource, and True if the entity is not waiting for the resource | Unknown





### cancel

```python
def cancel(self,res,amount:int=1)
```




cancels a resource request if it is pending, and put it back if it is already granted.


#### Parameters

 Parameter  | Type  | Doc
-----|----------|-----
 res  |  resource | Resource for which the eneity is waiting for.
 amount |  int | Number of resources that the entity is waiting for.
 Unknown | If the number of entities is not specified, waiting for any number of resources is ok |





### schedule

```python
def schedule(self)
```






#### Returns

 Return Variable  | Type  | Doc
-----|----------|-----
 Unknown | pandas.DataFrame | The schedule of each entity.
 Unknown | The columns are activity name, and start time and finish time of that activity | Unknown





### waiting_log

```python
def waiting_log(self)
```






#### Returns

 Return Variable  | Type  | Doc
-----|----------|-----
 Unknown | pandas.DataFrame | The time the entity started waiting and the time it finished waiting.
 Unknown | The columns show the resource name for which the entity is waiting for, time when waiting is started, | time when waiting is finished, and the number of resources the entity is waiting for





### waiting_time

```python
def waiting_time(self)
```






#### Returns

 Return Variable  | Type  | Doc
-----|----------|-----
 Unknown | numpy.array | The waiting durations of the entity each time it waited for a resource





### status_log

```python
def status_log(self)
```





*****************************************
*****Resource Class*******************
*****************************************

#### Returns

 Return Variable  | Type  | Doc
-----|----------|-----
 Unknown | pandas.DataFrame | shows any change in the status of an entity, the change can be either
 Unknown | waiting for a resourcing, getting a resources, putting a resource back, or adding to a resouce, | or it can be starting or finishing an activity








## general_resource()

```python
class general_resource()
```




The parent class for all of pmpy.resources

#### Methods

 Method  | Doc
-----|-----
 queue_log |
 status_log |
 waiting_time |
 _request |
 _get |
 _add |
 _put |
 level |
 idle |
 in_use |
 capacity |
 average_queue_length |




### __init__

```python
def __init__(self,env,name,capacity,init,print_actions=False,log=True)
```




Creates an intstance of a pmpy general resource.


#### Parameters

 Parameter  | Type  | Doc
-----|----------|-----
 env | pmpy.environment | The environment for the entity
 name  |  string | Name of the resource
 id  |  int | A unique id for the resource in the environment
 capacity |  | Maximum capacity for the resource
 init  |  int | Initial number of resources
 print_actions  |  bool | If equal to True, the changes in the resource will be printed in console
 log |  bool | If equals True, various statistics will be collected for the resource





### queue_log

```python
def queue_log(self)
```






#### Returns

 Return Variable  | Type  | Doc
-----|----------|-----
 Unknown | pandas.DataFrame | All entities waiting for the resource, their start waiting time and
 Unknown | finish waiting time are stored in this DataFrame | Unknown





### status_log

```python
def status_log(self)
```






#### Returns

 Return Variable  | Type  | Doc
-----|----------|-----
 Unknown | pandas.DataFrame | Any changes in the status of the resource and the time of the change is presented
 Unknown | in this DataFrame. The recorded statuses are number of in-use resources , | number of idle resources, and number of entities waiting for the resource.





### waiting_time

```python
def waiting_time(self)
```






#### Returns

 Return Variable  | Type  | Doc
-----|----------|-----
 Unknown | numpy.array | The waiting durations for a resource





### _request

```python
def _request(self,entity,amount)
```




Calculate needed logs when an entity requests the resource.


#### Parameters

 Parameter  | Type  | Doc
-----|----------|-----
 entity  |  pmpy.entity | The entity requesting the resource
 amount  |  int | The number of requested resouces





### _get

```python
def _get(self,entity,amount)
```




Calculate needed logs when an entity got the resource.


#### Parameters

 Parameter  | Type  | Doc
-----|----------|-----
 entity  |  pmpy.entity | The entity getting the resource
 amount  |  int | The number of taken resouces





### _add

```python
def _add(self,entity,amount)
```




Calculate needed logs when an entity add to the resource.


#### Parameters

 Parameter  | Type  | Doc
-----|----------|-----
 entity  |  pmpy.entity | The entity adding the resource
 amount  |  int | The number of added resouces





### _put

```python
def _put(self,entity,amount)
```




Calculate needed logs when an entity add to the resource.


#### Parameters

 Parameter  | Type  | Doc
-----|----------|-----
 res  |  pmpy.entity | The entity putting the resource back
 amount  |  int | The number of resouces being put back





### level

```python
def level(self)
```






#### Returns

 Return Variable  | Type  | Doc
-----|----------|-----
 Unknown | int | The number of resources that are currently available





### idle

```python
def idle(self)
```






#### Returns

 Return Variable  | Type  | Doc
-----|----------|-----
 Unknown | int | The number of resources that are currently available





### in_use

```python
def in_use(self)
```






#### Returns

 Return Variable  | Type  | Doc
-----|----------|-----
 Unknown | int | The number of resources that are currently in-use





### capacity

```python
def capacity(self)
```






#### Returns

 Return Variable  | Type  | Doc
-----|----------|-----
 Unknown | int | The maximum capacity for the resource





### average_queue_length

```python
def average_queue_length(self)
```





#### Returns

 Return Variable  | Type  | Doc
-----|----------|-----
 Unknown | float | The average waiting queue length for a resource








## request()

```python
class request()
```




A class defining the a priority request for capturing the resources.
This class allows to keep all the requests in a sorted list of requests.




### __init__

```python
def __init__(self,entity,amount)
```












## resource(general_resource)

```python
class resource(general_resource)
```





#### Methods

 Method  | Doc
-----|-----
 get |
 _check_all_requests |
 cancel |
 add |
 put |




### __init__

```python
def __init__(self,env,name, init=1,capacity=1000,print_actions=False,log=True)
```




Defines a resource for which a priority queue is implemented. 


#### Parameters

 Parameter  | Type  | Doc
-----|----------|-----
 env | pmpy.environment | The environment for the entity
 name  |  string | Name of the resource
 capacity |  int | Maximum capacity for the resource, defualt value is 1000.
 init |  int | Initial number of resources, defualt value is 1.
 print_actions  |  bool | If equal to True, the changes in the resource will be printed in console.
 Unknown | defualt value is False | log: bool
 Unknown | If equals True, various statistics will be collected for the resource. | defualt value is True.





### get

```python
def get(self,entity,amount)
```




A method for getting the resource. 


#### Parameters

 Parameter  | Type  | Doc
-----|----------|-----
 entity  |  pmpy.entity | The entity adding the resource
 amount  |  int | The number of resouces to be added
 priority  |  int | lower values for this input show higher priority





### _check_all_requests

```python
def _check_all_requests(self)
```




Check to see if any rquest for the resource can be granted.





### cancel

```python
def cancel(self,priority_request)
```









### add

```python
def add(self,entity,amount)
```




A method for adding the resource by the entity.


#### Parameters

 Parameter  | Type  | Doc
-----|----------|-----
 entity  |  pmpy.entity | The entity adding the resource
 amount  |  int | The number of resouces to be added





### put

```python
def put(self,entity,amount)
```




A method for putting back the resource by the entity.


#### Parameters

 Parameter  | Type  | Doc
-----|----------|-----
 entity  |  pmpy.entity | The entity adding the resource
 amount  |  int | The number of resouces to be added








## priority_request()

```python
class priority_request()
```




A class defining the a priority request for capturing the resources.
This class allows to keep all the requests in a sorted list of requests.

#### Methods

 Method  | Doc
-----|-----
 __gt__ |
 __eq__ |
 __ge__ |




### __init__

```python
def __init__(self,entity,amount,priority)
```









### __gt__

```python
def __gt__(self,other_request)
```




Decides if a resource request has a higher priority than antothe resource request
Lower priority values show higher priority!
If the priority of two requests is equal and are made at the same time,
the request with lower number of needed resources will have a higher priority.





### __eq__

```python
def __eq__(self,other_request)
```









### __ge__

```python
def __ge__(self,other_request)
```












## priority_resource(general_resource)

```python
class priority_resource(general_resource)
```





#### Methods

 Method  | Doc
-----|-----
 get |
 _check_all_requests |
 cancel |
 add |
 put |




### __init__

```python
def __init__(self,env,name, init=1,capacity=1000,print_actions=False,log=True)
```




Defines a resource for which a priority queue is implemented. 


#### Parameters

 Parameter  | Type  | Doc
-----|----------|-----
 env | pmpy.environment | The environment for the entity
 name  |  string | Name of the resource
 capacity |  int | Maximum capacity for the resource, defualt value is 1000.
 init |  int | Initial number of resources, defualt value is 1.
 print_actions  |  bool | If equal to True, the changes in the resource will be printed in console.
 Unknown | defualt value is False | log: bool
 Unknown | If equals True, various statistics will be collected for the resource. | defualt value is True.





### get

```python
def get(self,entity,amount,priority=1)
```




A method for getting the resource. 


#### Parameters

 Parameter  | Type  | Doc
-----|----------|-----
 entity  |  pmpy.entity | The entity adding the resource
 amount  |  int | The number of resouces to be added
 priority  |  int | lower values for this input show higher priority





### _check_all_requests

```python
def _check_all_requests(self)
```




Check to see if any rquest for the resource can be granted.





### cancel

```python
def cancel(self,priority_request)
```









### add

```python
def add(self,entity,amount)
```




A method for adding the resource by the entity.


#### Parameters

 Parameter  | Type  | Doc
-----|----------|-----
 entity  |  pmpy.entity | The entity adding the resource
 amount  |  int | The number of resouces to be added





### put

```python
def put(self,entity,amount)
```




A method for putting back the resource by the entity.


#### Parameters

 Parameter  | Type  | Doc
-----|----------|-----
 entity  |  pmpy.entity | The entity adding the resource
 amount  |  int | The number of resouces to be added








## preemptive_resource(general_resource)

```python
class preemptive_resource(general_resource)
```




this class is under construction.

#### Methods

 Method  | Doc
-----|-----
 get |
 put |




### __init__

```python
def __init__(self,env,name, print_actions=False,log=True)
```




Defines a resource for which a priority queue is implemented. 


#### Parameters

 Parameter  | Type  | Doc
-----|----------|-----
 env | pmpy.environment | The environment for the entity
 name  |  string | Name of the resource
 capacity |  int | Maximum capacity for the resource, defualt value is 1000.
 init |  int | Initial number of resources, defualt value is 1.
 print_actions  |  bool | If equal to True, the changes in the resource will be printed in console.
 Unknown | defualt value is False | log: bool
 Unknown | If equals True, various statistics will be collected for the resource. | defualt value is True.





### get

```python
def get(self,entity,priority: int,preempt:bool=False)
```









### put

```python
def put(self,entity)
```




*****************************************
*****Environment Class*******************
*****************************************








## environment(simpy.Environment)

```python
class environment(simpy.Environment)
```




This class defines the simulation environment. 
All of the processes, entities and resources are defined in this class. 


#### Attributes

 Attribute  | Type  | Doc
-----|----------|-----
 now  |  float | current simulation time

#### Methods

 Method  | Doc
-----|-----
 create_entities |




### __init__

```python
def __init__(self)
```




Creates an instance of the simulation environment





### create_entities

```python
def create_entities(self,name,total_number,print_actions=False,log=True)
```




Create entities by making instances of class entity and adding them to the environemnt.
All the entities are created at the current simulation time: env.now

*****************************
********future works*********
*****************************

#### Parameters

 Parameter  | Type  | Doc
-----|----------|-----
 name  |  string | Name of the entities, the name of each entity would be name_0, name_1, ...
 print_actions  |  bool | If equal to True, the actions of the entities will be printed in console
 log |  bool | If equals True, various statistics will be collected for the entities

#### Returns

 Return Variable  | Type  | Doc
-----|----------|-----
 Unknown | list of entitiy | A list containing all the created entities








