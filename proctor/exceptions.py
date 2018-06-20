class ProctorException(Exception):
    pass


class ProctorWarning(Warning):
    pass


class InvalidProctor(ProctorWarning):
    pass


class BadProctorCondition(ProctorWarning):
    pass


class ProctorObjectNotRegistered(ProctorWarning):
    pass


class NotRegistered(ProctorWarning):
    pass


class RectifierNotRegistered(NotRegistered):
    pass


class DetectorNotRegistered(NotRegistered):
    pass


class ConditionNotRegistered(NotRegistered):
    pass
