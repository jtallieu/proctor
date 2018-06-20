from models import vehicles
from proctor import Condition, ProctorObject


class VehicleCondition(Condition):
    context = vehicles.Vehicle


class VehicleProctor(ProctorObject):
    context = vehicles.Vehicle
