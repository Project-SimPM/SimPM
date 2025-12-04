import pytest

import simpm.des as des


def test_resource_lifecycle_logging():
    env = des.Environment()
    worker = env.create_entities("worker", 1, print_actions=False, log=True)[0]
    machine = des.Resource(env, "machine", init=1, capacity=1, log=True)

    def job(entity, resource):
        yield entity.get(resource, 1)
        yield entity.do("work", 5)
        yield entity.put(resource, 1)

    env.process(job(worker, machine))
    env.run()

    schedule = worker.schedule()
    assert schedule["activity"].tolist() == ["work"]
    assert schedule["start_time"].iloc[0] == 0
    assert schedule["finish_time"].iloc[0] == 5

    waiting = worker.waiting_time()
    assert waiting.size == 1
    assert waiting[0] == 0

    resource_log = machine.status_log()
    assert resource_log.iloc[-1]["time"] == pytest.approx(5)
    assert machine.average_utilization() == pytest.approx(1.0)
    assert machine.average_idleness() == pytest.approx(0.0)
