import simpm.des as des
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
    usage = data["resources"][0]["usage"]
    assert any(event["action"] == "acquired" for event in usage)


def test_run_function_without_dashboard():
    env, _, _ = _build_simple_environment()
    result = simpm.run(env, dashboard="none")
    assert result is None
