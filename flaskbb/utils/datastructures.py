try:
    from types import SimpleNamespace

except ImportError:

    class SimpleNamespace(dict):

        def __getattr__(self, name):
            try:
                return super(SimpleNamespace, self).__getitem__(name)
            except KeyError:
                raise AttributeError('{0} has no attribute {1}'
                                     .format(self.__class__.__name__, name))

        def __setattr__(self, name, value):
            super(SimpleNamespace, self).__setitem__(name, value)
