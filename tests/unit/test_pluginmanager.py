# some tests have been taking from
# https://github.com/pytest-dev/pluggy/blob/master/testing/test_pluginmanager.py
# and are licensed under the MIT License.
import pytest


def test_pluginmanager(plugin_manager):
    """Tests basic pluggy plugin registration."""
    class A(object):
        pass

    a1, a2 = A(), A()
    plugin_manager.register(a1)
    assert plugin_manager.is_registered(a1)
    plugin_manager.register(a2, "hello")
    assert plugin_manager.is_registered(a2)

    with pytest.raises(ValueError):
        assert plugin_manager.register(a1, internal=True)

    out = plugin_manager.get_plugins()
    assert a1 in out
    assert a2 in out
    assert plugin_manager.get_plugin('hello') == a2
    assert plugin_manager.unregister(a1) == a1
    assert not plugin_manager.is_registered(a1)

    out = plugin_manager.list_name_plugin()
    assert len(out) == 1
    assert out == [("hello", a2)]
    assert plugin_manager.list_name() == ["hello"]


def test_register_internal(plugin_manager):
    """Tests registration of internal flaskbb plugins."""
    class A(object):
        pass

    a1, a2 = A(), A()
    plugin_manager.register(a1, "notinternal")
    plugin_manager.register(a2, "internal", internal=True)
    assert plugin_manager.is_registered(a2)

    out = plugin_manager.list_name_plugin()
    assert ('notinternal', a1) in out
    assert ('internal', a2) not in out

    out_internal = plugin_manager.list_internal_name_plugin()
    assert ('notinternal', a1) not in out_internal
    assert ('internal', a2) in out_internal

    assert plugin_manager.unregister(a2) == a2
    assert not plugin_manager.list_internal_name_plugin()  # should be empty


def test_set_blocked(plugin_manager):
    class A(object):
        pass

    a1 = A()
    name = plugin_manager.register(a1)
    assert plugin_manager.is_registered(a1)
    assert not plugin_manager.is_blocked(name)
    plugin_manager.set_blocked(name)
    assert plugin_manager.is_blocked(name)
    assert not plugin_manager.is_registered(a1)

    plugin_manager.set_blocked("somename")
    assert plugin_manager.is_blocked("somename")
    assert not plugin_manager.register(A(), "somename")
    plugin_manager.unregister(name="somename")
    assert plugin_manager.is_blocked("somename")


def test_set_blocked_internal(plugin_manager):
    class A(object):
        pass

    a1 = A()
    name = plugin_manager.register(a1, internal=True)
    assert plugin_manager.is_registered(a1)
    assert not plugin_manager.is_blocked(name)
    plugin_manager.set_blocked(name)
    assert plugin_manager.is_blocked(name)
    assert not plugin_manager.is_registered(a1)


def test_get_internal_plugin(plugin_manager):
    class A(object):
        pass

    a1, a2 = A(), A()
    plugin_manager.register(a1, "notinternal")
    plugin_manager.register(a2, "internal", internal=True)
    assert plugin_manager.get_plugin('notinternal') == a1
    assert plugin_manager.get_plugin('internal') == a2


def test_get_internal_name(plugin_manager):
    class A(object):
        pass

    a1, a2 = A(), A()
    plugin_manager.register(a1, "notinternal")
    plugin_manager.register(a2, "internal", internal=True)

    assert plugin_manager.get_name(a1) == "notinternal"
    assert plugin_manager.get_name(a2) == "internal"
