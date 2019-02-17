from base import VehicleCondition, VehicleProctor
from proctor_lib.decorators import detector, rectifier


# Define a condition on the model that we want to check for
class InvalidDoors(VehicleCondition):
    name = "Wrong number of doors"
    symptom = "Will not pass inspection"
    solution = "Re-manufacture the vehicle"
    level = 1


class CoupDoors(VehicleProctor):
    condition = InvalidDoors

    applies_to = {
        '__class__.__name__': ['Coupe']
    }
    excludes = {
        'make': ['Toyota', 'Nissan']
    }

    @detector
    def check_doors(self, car):
        if car.doors != 2:
            return True
        return False

    @rectifier
    def fix_doors(self, car, condition=None):
        car.doors = 2
        return True

class JapCoupDoors(VehicleProctor):
    condition = InvalidDoors

    applies_to = {
        '__class__.__name__': ['Coupe'],
        'make': ['Toyota', 'Nissan']
    }

    @detector
    def check_doors(self, car):
        if car.doors != 2:
            return True


class NoGas(VehicleCondition):
    name = "No fuel"
    symptom = "Will not start"
    solution = "Fill up the gas tank"
    level = 1


class NoGasProctor(VehicleProctor):
    condition = NoGas

    @detector
    def check_gas(self, car):
        if car.gas_level <= 0:
            return True

