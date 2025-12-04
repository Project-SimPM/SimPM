"""Tests for recorder behavior."""

from simpm import des
from simpm.recorder import StreamingRunRecorder


def test_streaming_recorder_emits_final_snapshot():
    env = des.Environment()
    loader = des.Resource(env, "loader", capacity=1, init=1)
    first, second = env.create_entities("truck", 2)

    def trip(entity):
        yield entity.get(loader, 1)
        yield entity.do("load", 1)
        yield entity.put(loader, 1)

    env.process(trip(first))
    env.process(trip(second))

    recorder = StreamingRunRecorder()
    env.register_observer(recorder)
    env.run()

    event = recorder.event_queue.get_nowait()
    assert event["event"] == "run_finished"
    data = event["run_data"]
    assert len(data["entities"]) == 2
    assert len(data["resources"]) == 1
    assert any(ent.get("schedule_log") for ent in data["entities"])
