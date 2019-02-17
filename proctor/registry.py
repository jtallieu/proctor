import copy
import logging
import warnings
import inspect
from mapping import Mapping
from .exceptions import NotRegistered, BadProctorCondition, DetectorNotRegistered, RectifierNotRegistered

log = logging.getLogger("proctor.registry")
ilog = logging.getLogger('proctor.internal')


class RegisteredCondition(Mapping):
    """
    Registered condition contains a condition and
    the attached rectifiers and detectors and some helper methods
    """

    def __init__(self, condition_class):
        super(RegisteredCondition, self).__init__(condition=condition_class)
        self.detectors = []
        self.rectifiers = []
        self.name = condition_class.name
        self.context = condition_class.context

    def sort_handlers(self):
        """Sort detectors and rectifiers by filter priority"""
        self.detectors.sort(key=lambda x: x._filter_priority, reverse=True)
        self.rectifiers.sort(key=lambda x: x._filter_priority, reverse=True)

    def add_rectifier(self, rectifier_cls):
        """Add a rectifier to the registered condition"""
        if not self.condition.context_name() == rectifier_cls.context_name():
            warnings.warn(
                "Rectifier {} not valid for {}: context mis-match".format(
                    rectifier_cls.context_name(), self.condition.context_name()), NotRegistered)
        else:
            self.rectifiers.append(rectifier_cls)
        self.sort_handlers()

    def add_detector(self, detector_cls):
        """Add a detector to the registered condition"""
        if not detector_cls.context_name() == self.condition.context_name():
            warnings.warn(
                "Detector {} not valid for {}: context mis-match".format(
                    detector_cls.context_name(), self.condition.context_name()), NotRegistered)
        else:
            self.detectors.append(detector_cls)
        self.sort_handlers()

    def get_detector(self, obj):
        """
        Get the applicable detector for this isinstance
        of the context
        """
        for detector in self.detectors:
            if hasattr(detector, "_filter"):
                if detector()._filter(obj):
                    ilog.debug("Detector is {}".format(detector))
                    return detector
        return None

    def get_rectifier(self, obj):
        """Get applicable rectifier checking through the filters"""
        for rectifier in self.rectifiers:
            if hasattr(rectifier, "_filter"):
                if rectifier()._filter(obj):
                    ilog.debug("Rectifier is {}".format(rectifier))
                    return rectifier
        return None


class Registry(object):
    """Base Registry"""

    log = logging.getLogger("proctor.registry")

    def __init__(self):
        self._registry = {}
        self._id_registry = {}

    def register(self, cls):
        raise NotImplemented


class ConditionRegistry(Registry):
    """
    Maintains a list of RegisteredCondition objects hashed by
    name and context.
    """

    def __init__(self):
        super(ConditionRegistry, self).__init__()
        self._contexts = {}
        self._proctorClasses = {}

    def register_rectifier(self, cls):
        """Check the rectifier properties before adding it to the registry"""
        name = cls.__name__
        valid = True
        if not hasattr(cls, "_rectify"):
            warnings.warn("{} does not have a rectify method".format(name), BadProctorCondition)
            valid = False
        if not hasattr(cls, "condition"):
            warnings.warn("{} does not specify a condition".format(name), BadProctorCondition)
            valid = False
        if not hasattr(cls, "context"):
            warnings.warn("{} does not specify a context".format(name), BadProctorCondition)
            valid = False

        if valid:
            log.debug("{} rectifier registered as {}".format(name, cls.pid))

            # get the registered condition class and bind it to the PO.condition
            # PO.condition may be specified as a string
            condition = self.get_condition(cls.condition_name())
            if condition:
                cls.condition = condition
                condition.add_rectifier(cls)
            else:
                warnings.warn("{} [{}] condition not defined".format(name, cls.condition), RectifierNotRegistered)
        else:
            warnings.warn("{} not registerd as a rectifier".format(name), RectifierNotRegistered)

    def register_detector(self, cls):
        """Check the detector properties before adding it to the registry"""
        name = cls.__name__
        valid = True
        if not hasattr(cls, "_detector"):
            warnings.warn("{} does not have a detect method".format(name), BadProctorCondition)
            valid = False
        if not hasattr(cls, "condition"):
            warnings.warn("{} does not specify a condition".format(name), BadProctorCondition)
            valid = False
        if not hasattr(cls, "context"):
            warnings.warn("{} does not specify a context".format(name), BadProctorCondition)
            valid = False

        if valid:
            log.debug("{} detector registered as {}".format(name, cls.pid))

            # get the registered condition class and bind it to the PO.condition
            # PO.condition may be specified as a string
            condition = self.get_condition(cls.condition_name())
            if condition:
                cls.condition = condition.condition
                condition.add_detector(cls)
            else:
                warnings.warn("{} {} condition not defined".format(name, cls.condition), DetectorNotRegistered)
        else:
            warnings.warn("{} not registerd as a detector".format(name), DetectorNotRegistered)

    def register_condition(self, cls):
        """Register the condition"""
        if not self.get_condition(cls.name):
            condition_desc = RegisteredCondition(cls)
            context_key = cls.context_name()

            # Add to the registry by condition.class_name
            self._registry[cls.name] = condition_desc
            self._id_registry[cls.pid] = condition_desc
            if context_key not in self._contexts:
                self._contexts[context_key] = []

            # Add the condition to the list of conditions for the context (which is a class name string)
            self._contexts[context_key].append(condition_desc)

            log.debug("Registered {}:[{}] on ({}) PID:{}".format(cls.__name__, cls.name, context_key, cls.pid))

        else:
            warnings.warn("{} already registered".format(cls.__name__), RuntimeWarning)

    def is_proctor_registered(self, cls):
        """Did we know about this proctor object already"""
        name = "{}.{}".format(cls.__module__, cls.__name__)
        if name in self._proctorClasses:
            return True
        else:
            return False

    def register_proctor_class(self, cls):
        """
        Track every proctor class that we found so we don't
        re-peat ourselves if we have to reload our plugins
        """
        name = "{}.{}".format(cls.__module__, cls.__name__)
        self._proctorClasses[name] = cls

    def register(self, cls):
        """Register a ProctorObject or a Condition"""
        if self.is_proctor_registered(cls):
            ilog.info("Already registered proctor {}".format(cls))
            return

        if hasattr(cls, "_is_rectifier"):
            self.register_rectifier(cls)

        if hasattr(cls, "_is_detector"):
            self.register_detector(cls)

        if hasattr(cls, "_is_condition"):
            self.register_condition(cls)
        else:
            # track what ProctorsObjects we know about - good or bad
            self.register_proctor_class(cls)

    def get_condition(self, condition):
        """Get a RegisteredCondition by name or class or pid"""
        return self._registry.get(condition, self._id_registry.get(condition, None))

    def show(self):
        """Show the registry (lame!)"""
        for c, desc in self._registry.items():
            ctx_name = desc.context if isinstance(desc.context, basestring) else desc.context.__name__
            print("condition: '{}'\n\tcontext: {}\n\tclass: {}".format(c, ctx_name, desc.condition))
            print("\tDetectors:")
            for d in desc.detectors:
                print("\t\t{}.{} ({})".format(d.__module__, d.__name__, d._filter_priority))

            print("\tRectifiers:")
            for r in desc.rectifiers:
                print("\t\t{}.{} ({})".format(r.__module__, r.__name__, d._filter_priority))
            print

    def get_registered_conditions(self, klass):
        """Get registeredConditions for a context"""
        return self.__find_context(klass)

    def __find_context(self, klass):
        """
        Find the context that is lowest in the MRO.
        Handles finding a condition defined for a subclass of the given object.
        Will return the conditions for the earliest in the MRO.

        ex: context's Store
        class structure:
            class InternalStore(Store):
                pass
            class MyStore(Mixin, InternalStore):
                pass

        If we have conditions defined for both Store and InternalStore,
        when finding the conditions for an instance of MyStore - it will properly
        return the conditions for Store but not InternalStore.  If however,
        MyStore has conditions defined, Store's won't be returned.  This should
        be changed to give back all in the heirarchy that match.
        """
        classes = [x.__name__ for x in inspect.getmro(klass)]

        # keep a tuple of (conditions to return, index of the class in the MRO)
        conditions = [([], len(classes))]

        for (key, ctxt_conditions) in self._contexts.items():
            if key in classes:
                conditions.append((ctxt_conditions, classes.index(key)))

        # Return the first set of conditions that match the class, which is
        # like saying give me the conditions that are most specific to
        # this klass
        return min(conditions, key=lambda i: i[1])[0]

    def condition_list(self):
        return self._registry.keys()

    def reset(self):
        self._contexts = {}
        self._proctorClasses = {}
        self._registry = {}

    def get_registry(self):
        """Return a deepcopy of the registry"""
        return copy.deepcopy(self._registry)
