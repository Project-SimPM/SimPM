"""Tests for recorder behavior."""

from simpm import des
from simpm.recorder import StreamingRunRecorder


def test_entity_snapshots_include_logs_during_run():
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

    snapshots: dict[int, dict] = {}
    while not recorder.event_queue.empty():
        event = recorder.event_queue.get_nowait()
        if event.get("event") == "entity_snapshot":
            entity = event.get("entity", {})
            snapshots[entity.get("id")] = entity

    assert snapshots, "expected entity snapshots to be published"
    assert snapshots[first.id]["schedule_log"], "first entity should record schedule entries"
    assert snapshots[second.id]["status_log"], "waiting entity should record status changes"
    assert snapshots[second.id]["waiting_log"], "waiting entity should report waiting episodes"
