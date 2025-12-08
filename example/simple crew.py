import simpm
from simpm.des import Environment, Resource,Entity
from simpm.dist import norm

# 1) Create the simulation environment
env = Environment("Single activity")

# 2) Define resources (e.g., one crew)
machine = Resource(env, name="Machine", capacity=1)

# 3) Create an entity to perform the activity
crew = Entity(env,"Crew", print_actions=False, log=True)

# 4) Define the activity process
def activity(entity, resource):
    # Request one unit of the crew resource and wait until it is available
    yield entity.get(resource, 1)

    # Perform the work
    yield entity.do("work", norm(10, 2))

    # Release the crew
    yield entity.put(resource, 1)

    print(f"{entity.env.now:.2f}: {entity} finished.")

env.process(activity(crew, machine))

# 5) Run the simulation
simpm.run(env)

print(f"Project finished at t={env.now:.2f}")
print(crew.schedule())