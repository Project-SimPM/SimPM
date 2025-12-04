import pytest

from simpm import des


def test_get_more_than_capacity_raises_immediately():
    env = des.Environment()
    resource = des.Resource(env, "resource", init=0, capacity=5)
    entity = env.create_entities("entity", 1)[0]

    get_request = resource.get(entity, 10)

    with pytest.raises(ValueError):
        next(get_request)


def test_putting_beyond_capacity_raises_immediately():
    env = des.Environment()
    resource = des.Resource(env, "resource", init=5, capacity=5)
    entity = env.create_entities("entity", 1)[0]

    put_request = resource.put(entity, 1)

    with pytest.raises(ValueError):
        next(put_request)


def test_adding_beyond_capacity_raises_immediately():
    env = des.Environment()
    resource = des.Resource(env, "resource", init=5, capacity=5)
    entity = env.create_entities("entity", 1)[0]

    add_request = resource.add(entity, 1)

    with pytest.raises(ValueError):
        next(add_request)

