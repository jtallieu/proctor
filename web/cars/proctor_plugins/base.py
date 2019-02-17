from cars.models import Vehicle
from proctor_lib import Condition, ProctorObject


class VehicleCondition(Condition):
    context = Vehicle


class VehicleProctor(ProctorObject):
    context = Vehicle
