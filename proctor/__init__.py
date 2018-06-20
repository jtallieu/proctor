"""
Proctor (Audit) System.

A stand-alone library that provides a pluggable framework to simplify
coding functions that detect/fix data conditions.  The objective
is to abstract the boilerplate code necessary to expose such functions
to the front-end and re-use them throughout the application.

Sometimes when we find an issue, we write a function that will
tell us the extent of the issue. And we keep running that function
over time until that condition goes away.  That functions serves as a 'detector'
for us to see if we are solving the issue.

The Proctor system attempts to put some structure around that workflow,
to allow us to specify functions that can be added/removed without impact
to the core code base.

At some point we could slap a GUI on the Proctor to code a condition on
the fly so that we can add custom reporting without a deployment.
"""
import sys
import hashlib
import logging
import warnings
from mapping import Mapping
from .registry import ConditionRegistry
from .exceptions import NotRegistered, BadProctorCondition
import plugin_support as plugins

log = logging.getLogger("proctor")
ilog = logging.getLogger('proctor.meta')
clog = logging.getLogger('proctor.condition')


def warnFormatter(message, category, filename, lineno, line=None):
    return "{}: {}".format(category.__name__, message)
warnings.formatwarning = warnFormatter


def get_property(obj, key):
    """Get the value of a related property - however deep"""
    _keys = key.split(".")

    # dotted keys "x.y.z"
    if len(_keys) > 1:
        # Could raise KeyError
        return get_property(getattr(obj, _keys[0]), _keys[1])
    else:
        return getattr(obj, _keys[0])


class ProctorSingleton(type):
    """
    The first instance created will load the plugins, if
    provided some paths.  see Proctor.__init__
    """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            inst = super(ProctorSingleton, cls).__call__(*args, **kwargs)
            cls._instances[cls] = inst
            inst.load_plugins()
        return cls._instances[cls]


class Proctor(object):

    """
    Manages conditions, detectors, and rectifiers collected as a registry
    """
    __metaclass__ = ProctorSingleton

    def __init__(self, extpaths=None):
        self._conditions = ConditionRegistry()
        self.plugin_dirs = extpaths if extpaths else []

    """
    Methods that deal with loading conditions, detectors, and
    rectifiers.
    """

    def load_plugins(self):
        """Load all the directories"""
        for path in self.plugin_dirs:
            self.load_plugins_from(path)

    def load_plugins_from(self, dirname):
        """Loads plugins from a directory"""
        try:
            if plugins.load(dirname):
                log.info(u"Successfully loaded plugins from {}".format(dirname))
        except Exception as e:
            log.exception(u"Failed to load extensions at {}. {}".format(dirname, e.message))

    def add_module(self, name):
        """Load a module that contains conditions and detectors"""
        log.debug(u"Adding module {}".format(name))
        plugins.load_module(name)

    def add_paths(self, paths):
        """Appends the plugin path after loading"""
        for path in paths:
            if path not in self.plugin_dirs:
                self.load_plugins_from(path)
            self.plugin_dirs.append(path)

    @property
    def condition_list(self):
        """Get a listing of condition names"""
        return self._conditions.condition_list()

    def register(self, cls):
        """
        Registers both Conditions and ProctorObjects
        """
        log.debug("Registering {}".format(cls.__name__))
        logging.captureWarnings(True)
        self._conditions.register(cls)
        logging.captureWarnings(False)

    def get_registry(self):
        """Returns the registry (a copy)"""
        return self._conditions.get_registry()

    def show_registry(self):
        """shows the content of the registry"""
        return self._conditions.show()

    def __get_conditions(self, context):
        """
        Get the conditions registered to the context,
        where context is class object
        """
        return self._conditions.get_registered_conditions(context)

    def find_condition(self, condition, klass):
        """
        find a specific (registered) condition - will contain all associated detectors and rectifiers

        condition(str or condition instance) text for look up for
        klass(class) to find the conditions for
        """
        name = condition if isinstance(condition, basestring) else condition.name
        for _condition in self.__get_conditions(klass):
            if _condition.name == name:
                return _condition
        return None

    def conditions(self, obj, min_level=1, exposed=None):
        """
        get contextual condition objects - aka conditions that can be called to detect and
        rectify on the given object
        """
        conditions = []
        for cond in self._conditions.get_registered_conditions(obj.__class__):
            if cond.condition.level >= min_level:
                if exposed is None:
                    conditions.append(ContextualCondition(obj, cond))
                else:
                    if exposed == cond.condition.exposed:
                        conditions.append(ContextualCondition(obj, cond))
        return conditions

    def detect_conditions(self, obj, min_level=1, exposed=None):
        """
        Executes the detector on contextualConditions
        """
        for condition in self.conditions(obj, min_level, exposed):
            condition.detect()
            yield condition

    def get_rectifier(self, condition, obj):
        """
        gets a condition rectifier for an obj
        """
        try:
            return self.find_condition(condition, obj.__class__).get_rectifier(obj)
        except:
            return None

    def get_contextual_condition(self, condition, obj):
        """
        Get the contextualCondition for this object
        """
        try:
            return ContextualCondition(obj, self.find_condition(condition, obj.__class__))
        except:
            return None

    def detect_condition(self, condition, obj):
        _condition = self.get_contextual_condition(condition, obj)
        if _condition:
            _condition.detect()
        return _condition

    def clear_registry(self):
        log.critical("Clearing condition registry")
        self._conditions.reset()
        self.plugin_dirs = []


class ProctorObjectMeta(type):

    """
    Handles the registration and checking ProctorObjects
    """

    def __init__(cls, name, bases, attrs):
        """
        Called when a derived class is imported.
        Classifies the ProctorObject as a detector, rectifier or condition.
        """
        rectifier = False
        detector = False

        _cls = {}
        ilog.debug("Building class {} {} {} {}".format(cls, name, bases, attrs))

        # Check methods for a rectifier and a detector,
        # as determined (see: decorators)
        for _name, method in cls.__dict__.iteritems():
            ilog.debug("Checking {} {}".format(_name, method))

            # Has a decorated rectifier?
            if hasattr(method, "is_rectifier"):
                _cls["_is_rectifier"] = True
                _cls["_rectify"] = method
                rectifier = True

            # Has a decorated detector?
            if hasattr(method, "is_detector"):
                _cls["_is_detector"] = True
                _cls["_detector"] = method
                detector = True

            # Has a decorated filter method?
            # If a method is specified as a filter,
            # it takes prescendence over 'applies_to'
            # and 'excludes' properties.
            if hasattr(method, "is_filter"):
                ilog.debug("{} has prefilter".format(name))
                _cls['_has_filter'] = True
                _cls['_filter'] = method
                # Make it the hightest priority
                _cls['_filter_priority'] = sys.maxint

        # Inject the things we set above into the class
        for k, v in _cls.items():
            setattr(cls, k, v)

        # If there is no filter in this class - make one that will
        # understand about 'applies_to' and 'exclude' class properties of
        # - NOTE: This purposley breaks inheritence of the _filter property.
        if not hasattr(cls.__dict__, "_filter") and "_filter" not in _cls:

            # Declare the filter method that will honor 'applied_to' and 'excludes'.
            def _filter(self, obj):
                ilog.debug("Checking {}.filter()".format(cls.__name__))

                for k, v in cls.applies_to.items():
                    # try to get the value for the key
                    try:
                        value = get_property(obj, k)
                    except:
                        ilog.exception(u"Cannot get value for {}".format(k))
                        return False
                    ilog.debug("Value of {} {}".format(k, value))
                    if value not in v:
                        ilog.debug("{} {} not in {}".format(k, value, v))
                        return False

                for k, v in cls.excludes.items():
                    # try to get the value for the key
                    try:
                        value = get_property(obj, k)
                    except:
                        ilog.exception(u"Cannot get value for {}".format(k))
                        return True
                    ilog.debug("Value of {} {}".format(k, value))
                    if value in v:
                        ilog.debug("{} excluded {}".format(k, v))
                        return False
                return True

            """
            ProctorObject Priority:

            It is possible that there exists more than one Detector/Rectifier
            for a Condition-Context. Each Detector/Rectifier (ProctorObject) is
            bound to a filter and the filter has a priority, therefore the ProctorObject
            has that priority.

            When trying to find the Detector function for a given Condition-Context pair, the
            Proctor will check the Context against each filter in priority order.  The first
            filter that passes, identifies the Detector/Rectifier to use.

            Priority calculation:
            Priority is based on 'applies_to' and 'excludes' dictionaries.  Remember those dictionaries
            are of the form { 'prop1.prop2.prop3' : [val1, val2,..] }.

            The formula is sum of each item's weight, where the weight is:
               30 X len(properties in key) + len(values)

            Longer hierarchies are viewed as more specific, therefore weighted higher, and ties are
            broken by the length of the values that apply to each key.

            """
            # Compute the priority of the filter based on
            priority = 0

            try:
                priority += sum(
                    map(lambda x: 30 ** (len(x.split('.'))) + len(cls.applies_to[x]), cls.applies_to.keys()))
                priority += sum(
                    map(lambda x: 30 ** (len(x.split('.'))) + len(cls.excludes[x]), cls.excludes.keys()))

                ilog.debug("{} priority {}".format(cls.__name__, priority))

                cls._filter_priority = priority
                cls._filter = _filter
            except:
                warnings.warn("{} NOT REGISTERED: Cannot determine filter priority".format(name), NotRegistered)
                return

        # Not really used, the thought was if a rectifier and detector are in the
        # same class, they should be presented together
        if rectifier and detector:
            cls._bonded = True

        if rectifier or detector:
            cls.pid = hashlib.sha1(cls.__name__).hexdigest()[:10].upper()
            Proctor().register(cls)
        else:
            log.warn("{} NOT REGISTERED: no detector or rectifier function".format(name))


class ProctorObject(object):

    """Base Proctor Object"""
    __metaclass__ = ProctorObjectMeta
    context = None
    applies_to = {}
    excludes = {}

    @classmethod
    def context_name(cls):
        return cls.context if isinstance(cls.context, basestring) else cls.context.__name__

    @classmethod
    def condition_name(cls):
        if cls.condition:
            return cls.condition if isinstance(cls.condition, basestring) else cls.condition.name


class ConditionMeta(type):

    """
    Handles the registration and checking of a condition
    """

    def __init__(cls, name, bases, attrs):
        """
        Called when a derived class is imported.
        Verifies that a condition has a name and a context
        """
        log.debug("Registering Condition {}".format(name))
        if hasattr(cls, 'name') and hasattr(cls, 'context'):
            cls.pid = hashlib.sha1(cls.name).hexdigest()[:10].upper()
            Proctor().register(cls)
        else:
            log.warn("Cannot register {}".format(cls.__name__))


class ContextualCondition(Mapping):

    """
    Represents a condition checker that contains a context.
    Will contain the detector and the rectifier for the object
    being checked.  Pretty much a RegisteredCondition Proxy
    """

    def __init__(self, context, registered_condition):
        super(ContextualCondition, self).__init__()
        self.__reg_condition = registered_condition
        self.level = registered_condition.condition.level
        self.exposed = registered_condition.condition.exposed
        self.context = context
        self.name = self.__reg_condition.name
        self.rectifier = self.__reg_condition.get_rectifier(context)
        self.detector = self.__reg_condition.get_detector(context)
        self.detected = None
        self.rectified = None
        self.pid = self.__reg_condition.condition.pid
        self.detector_tried = False
        self.rectifier_tried = False

    @property
    def detectable(self):
        return self.detector is not None

    @property
    def rectifiable(self):
        if self.detected:
            return self.detected.rectifiable
        else:
            return self.rectifier is not None

    def context_name(cls):
        return cls.context if isinstance(cls.context, basestring) else cls.context.__class__.__name__

    def rectify(self):
        """rectify the detected condition"""
        if self.rectifiable and self.detected:
            self.rectifier_tried = True
            self.rectified = self.detected.rectify()
            return self.rectified

    def detect(self):
        """Where the magic happens"""
        if self.detectable:
            self.detector_tried = True
            try:
                self.detector()._detector(self.context)
                self.detected = None
            except Condition as c:
                self.detected = c
        return self.detected is not None

    def dict(self):
        """Serialize the condition"""
        data = Mapping()
        data['type'] = self.__reg_condition.condition.__name__
        data.check_key = self.__reg_condition.condition.name
        data.level = self.level
        data.pid = self.pid
        if self.detectable:
            data.detector = self.detector.__name__

        data.symptom = self.__reg_condition.condition.symptom
        data.solution = self.__reg_condition.condition.solution
        data.rectifier_tried = self.rectifier_tried
        data.detector_tried = self.detector_tried
        data.error_code = 1
        data.msg = ""
        data.rectifiable = False
        if self.rectifier:
            data.rectifiable = True
            try:
                data.rectifier = self.rectifier.__name__
            except:
                pass
        data.detectable = self.detectable
        data.rectified = self.rectified

        if self.detected:
            data.update(self.detected.dict())

        data.detected = self.detected is not None
        data.error_code_string = self.context_name()

        return data


class Condition(Exception):

    """
    Represents a condition.
    When raised, the ConditionObject will contain the
    Proctor functions - rectifier and detector to work on the
    condition.

    Here is what's cool, the condition (an exception really), when
    caught in the code, can be checked to see if it has a rectifier
    and it can attempt to fix the condition before really failing.
    """
    __metaclass__ = ConditionMeta
    context = None
    detector = None
    rectifier = None
    symptom = ""
    solution = ""
    exposed = False
    level = 1

    # HACK because I cannot figure out code structure to check the type
    _is_condition = True

    def __init__(self, message, context_instance=None, detector=None, inner_condition=None):
        """
        Called when condition is raised - Will attempt to find a rectifier
        """
        self.context_id = None
        self.context_instance = None
        self.detector = detector
        self.data = ""

        super(Condition, self).__init__(message)
        self.set_context(context_instance)

    def rectify(self):
        """Rectify the condition - do the damn thang"""
        if self.rectifiable:
            return self.rectifier()._rectify(self.context_instance, condition=self)
        return False

    def set_context(self, new_context):
        """
        Set the context - will trigger getting the recitifer.
        Necessary because a detector COULD throw a different condition (maybe).
        So reload the rectifier.
        """
        self.context_instance = new_context
        if isinstance(self.context_instance, object) and hasattr(self.context_instance, "id"):
            self.context_id = self.context_instance.id
        elif isinstance(self.context_instance, basestring):
            self.context_id = ""
        self._get_rectifier()

    def _get_rectifier(self):
        try:
            self.rectifier = Proctor().get_rectifier(self, self.context_instance)
        except:
            self.rectifier = None

    def dict(self):
        """cast to serializable dict"""
        data = Mapping()
        data.check_key = self.name
        data.error_code = 1
        data.error_code_string = self.__class__.context_name()
        data.msg = self.message
        data.ctxt_class = self.context_instance.__class__.__name__
        data.ctxt_id = self.context_id

        data.symptom = self.symptom
        data.solution = self.solution
        data.rectifiable = self.rectifiable
        data.level = self.level
        data.exposed = self.exposed
        data.pid = self.pid
        if self.rectifiable:
            data.rectifiable = True
            data.rectifier = self.rectifier.__name__
        else:
            data.rectifiable = False
            data.rectifier = None
        return data

    def serialize(self):
        return {'data': str(self.context_instance)}

    @property
    def rectifiable(self):
        return not (self.rectifier is None)

    @classmethod
    def context_name(cls):
        return cls.context if isinstance(cls.context, basestring) else cls.context.__name__

    @classmethod
    def class_info(cls):
        data = Mapping(cls.__dict__)
        data.context = cls.context_name()
        data.exposed = cls.exposed
        data.level = cls.level
        return data

    def __repr__(self):
        try:
            return "{}:{}".format(self.name, self.message)
        except AttributeError:
            return super(Condition, self).__repr__()

    def __str__(self):
        try:
            return "{}:{}".format(self.name, self.message)
        except AttributeError:
            return super(Condition, self).__str__()

    def __unicode__(self):
        try:
            return "{}:{}".format(self.name, self.message)
        except AttributeError:
            return super(Condition, self).__unicode__()
