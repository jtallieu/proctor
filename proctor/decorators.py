import logging
from functools import wraps
from . import Condition
ilog = logging.getLogger('proctor.meta')
rlog = logging.getLogger('proctor.rectifier')
dlog = logging.getLogger('proctor.detector')


def detector(func):
    """Marks a function as a detector for a condition"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        """
        Call the detect function.
        Handle the detecctor output to:
           - raise the bound condition if True
           - raise the bound condition with a helpful message if tuple and True
           - re-raise the condition if a condition was thrown
           - remain silent in all other cases
        """
        context = args[1]
        detector = args[0]
        try:
            ret = func(*args, **kwargs)
        except Condition as c:
            # Detector could raise another condition - make sure if it did, the detector class is attached
            if not c.detector:
                c.detector = detector.__class__
            if not c.context:
                c.set_context(context)
            raise c
        except KeyboardInterrupt:
            raise
        except:
            dlog.exception("Detector {} cause unhandled exception - cannot trust detection".format(func.__name__))
            return

        # Examine the return value
        status = ret
        message = func.__doc__ if func.__doc__ else ""
        extra = {}

        if isinstance(ret, tuple):
            status = ret[0]
            try:
                message = ret[1]
                extra = ret[2]
            except:
                pass

        if status:
            message = message.strip()

            # Create the condition specified in the calling object
            # and add the context to the condition
            err = args[0].condition(message, context, detector.__class__, **extra)
            dlog.debug("Done with error - {}".format(detector.__class__, __name__))
            raise err

        dlog.debug("Done clean = {}".format(detector.__class__.__name__))

    # tag the function
    wrapper.is_detector = True
    return wrapper


def rectifier(func):
    """Ensure good order by fixing the condition"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        """ Just tag the function and logs some debug """
        try:
            rlog.debug("Rectifying with {}".format(func.__name__))
            val = func(*args, **kwargs)
            if not val:
                rlog.debug("Rectify Failed")
            else:
                rlog.debug("RECTIFIED")
            return val
        except:
            rlog.exception("Exception when rectifying")
            return False

    # tag the function
    wrapper.is_rectifier = True
    return wrapper


def prefilter(func):
    """Defines a filter for the detector and/or rectifier"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        ilog.debug("Checking {}.prefilter()".format(args[0].__class__))
        return func(*args, **kwargs)

    # tag the function
    wrapper.is_filter = True
    return wrapper
