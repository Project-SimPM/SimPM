import simpm.des as des
from simpm import des
from simpm.recorder import RunRecorder
import simpm


def _build_simple_environment():
    env = des.Environment()
    worker = env.create_entities("worker", 1, log=True)[0]
    machine = des.Resource(env, "machine", init=1, capacity=1, log=True)

    def job(entity, resource):
        yield entity.get(resource, 1)
        yield entity.do("work", 2)
        yield entity.put(resource, 1)

    env.process(job(worker, machine))
    return env, worker, machine


def test_run_recorder_collects_basic_data():
    env, worker, machine = _build_simple_environment()
    recorder = RunRecorder()
    env.register_observer(recorder)
    env.run()

    data = recorder.run_data
    assert data["environment"]["name"] == env.name
    assert len(data["entities"]) == 1
    assert len(data["resources"]) == 1
    activities = data["entities"][0]["activities"]
    assert activities and activities[0]["duration"] == 2
    status = data["resources"][0]["status_log"]
    assert status, "resource status log should be captured from the environment"


def test_run_function_without_dashboard():
    env, _, _ = _build_simple_environment()
    result = simpm.run(env, dashboard=False)
    assert result is env


def test_resources_recorded_without_usage():
    env = des.Environment()
    unused = des.Resource(env, "unused", init=1, capacity=1, log=False)
    recorder = RunRecorder()
    env.register_observer(recorder)

    env.run(until=1)

    resources = recorder.run_data["resources"]
    assert len(resources) == 1
    assert resources[0]["id"] == unused.id
    assert resources[0]["capacity"] == 1
