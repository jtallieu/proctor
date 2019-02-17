import logging

log = logging.getLogger('proctor.util')


class ObjectProvider(object):
    def __init__(self, model):
        log.info("ObjectProvider for {}".format(model))
        self.model_class = model

    def get(self, id, **kwargs):
        raise NotImplementedError()

    def all(self):
        raise NotImplementedError()

    def filter(self, **kwargs):
        raise NotImplementedError()

    def ids(self, **kwargs):
        raise NotImplementedError()


class ProctorProviderMeta(type):
    def __init__(cls, name, bases, attrs):
        if hasattr(cls, 'provider'):
            if not isinstance(cls.provider, ObjectProvider):
                if issubclass(cls.provider, ObjectProvider):
                    cls.provider = cls.provider(cls)
            else:
                cls.provider = cls.provider.__class__(cls)


class ProctorMixin(object):
    __metaclass__ = ProctorProviderMeta
