import simpm
from simpm.des import Environment, Entity, PreemptiveResource


def test_preemptive_resource_interrupts_lower_priority_holder():
    env = Environment()
    R = PreemptiveResource(env, "Truck")
    e1 = Entity(env, "e1")
    e2 = Entity(env, "e2")

    events = []  # (label, time)

    def p1(a, R):
        events.append(("e1_created", env.now))
        # lower priority (0), non-preemptive holder
        yield a.get(R, 1, False)
        events.append(("e1_got", env.now))

        yield a.interruptive_do("something", 10)
        events.append(("e1_finished_something", env.now))

        yield a.put(R)
        events.append(("e1_put", env.now))

    def p2(b, R):
        events.append(("e2_created", env.now))
        yield b.do("b_act", 5)
        events.append(("e2_finished_b_act", env.now))

        # higher priority (-1) and preemptive
        yield b.get(R, 1, priority=-1, preempt=True)
        events.append(("e2_got", env.now))

        yield b.do("b_act2", 5)
        events.append(("e2_finished_b_act2", env.now))

        yield b.put(R)
        events.append(("e2_put", env.now))

    env.process(p1(e1, R))
    env.process(p2(e2, R))

    simpm.run(env, dashboard=False)

    # --- Assertions ---
    # e1's task must be cut at t=5 (not 10!)
    assert ("e1_finished_something", 5) in events
    assert ("e1_put", 5) in events

    # e2 gets the Truck at t=5 and finishes at t=10
    assert ("e2_got", 5) in events
    assert ("e2_finished_b_act2", 10) in events

    # Ordering: e1 must finish & put before e2 gets the Truck
    idx_e1_finish = events.index(("e1_finished_something", 5))
    idx_e1_put = events.index(("e1_put", 5))
    idx_e2_got = events.index(("e2_got", 5))
    assert idx_e1_finish <= idx_e1_put < idx_e2_got


def test_preemptive_resource_no_preemption_for_lower_priority():
    env = Environment()
    R = PreemptiveResource(env, "Truck")
    e1 = Entity(env, "e1")
    e2 = Entity(env, "e2")

    events = []

    def p1(a, R):
        yield a.get(R, 1, False)  # priority=0 holder
        events.append(("e1_got", env.now))

        yield a.interruptive_do("something", 10)
        events.append(("e1_finished_something", env.now))

        yield a.put(R)
        events.append(("e1_put", env.now))

    def p2(b, R):
        yield b.do("b_act", 5)
        events.append(("e2_finished_b_act", env.now))

        # Worse priority (+1), even though preempt=True
        yield b.get(R, 1, priority=+1, preempt=True)
        events.append(("e2_got", env.now))

        yield b.do("b_act2", 5)
        events.append(("e2_finished_b_act2", env.now))

        yield b.put(R)
        events.append(("e2_put", env.now))

    env.process(p1(e1, R))
    env.process(p2(e2, R))
    simpm.run(env, dashboard=False)

    # e1 not preempted: finishes at 10
    assert ("e1_finished_something", 10) in events
    assert ("e1_put", 10) in events

    # e2 can only get Truck after that
    assert ("e2_got", 10) in events
    assert ("e2_finished_b_act2", 15) in events

    idx_e1_put = events.index(("e1_put", 10))
    idx_e2_got = events.index(("e2_got", 10))
    assert idx_e1_put < idx_e2_got


def test_preemptive_resource_respects_preempt_flag():
    env = Environment()
    R = PreemptiveResource(env, "Truck")
    e1 = Entity(env, "e1")
    e2 = Entity(env, "e2")

    events = []

    def p1(a, R):
        yield a.get(R, 1, False)  # priority=0
        events.append(("e1_got", env.now))

        yield a.interruptive_do("something", 10)
        events.append(("e1_finished_something", env.now))

        yield a.put(R)
        events.append(("e1_put", env.now))

    def p2(b, R):
        yield b.do("b_act", 5)
        events.append(("e2_finished_b_act", env.now))

        # preempt=False, even though priority is "better"
        yield b.get(R, 1, priority=-1, preempt=False)
        events.append(("e2_got", env.now))

        yield b.do("b_act2", 5)
        events.append(("e2_finished_b_act2", env.now))

        yield b.put(R)
        events.append(("e2_put", env.now))

    env.process(p1(e1, R))
    env.process(p2(e2, R))
    simpm.run(env, dashboard=False)

    # e1 not preempted: still finishes at 10
    assert ("e1_finished_something", 10) in events
    assert ("e1_put", 10) in events

    # e2 has to wait until e1 releases
    assert ("e2_got", 10) in events
    assert ("e2_finished_b_act2", 15) in events
