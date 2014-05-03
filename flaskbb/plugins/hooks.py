#import hooks
# inspired fromhttp://stackoverflow.com/questions/932069/building-a-minimal-plugin-architecture-in-python
#hooks.registered.beforeIndex.append(hello_world)
#hooks.runHook(hooks.registered.beforeIndex)


class HookError(Exception):
    pass


class registered(object):
    beforeIndex = []
    afterIndex = []


def runHook(hook):
    for h in hook:
        try:
            h()
        except Exception as e:
            raise HookError("An error occured %s", e)
