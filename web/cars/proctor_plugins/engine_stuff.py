from base import VehicleCondition


class OilLow(VehicleCondition):
    name = "Oil level is low"
    symptom = "Risk locking up engine"
    solution = "Fill oil and check for leaks"
    level = 1
    exposed = True


class IgnitionCoilRecall(VehicleCondition):
    """
    Checks the engine coil for recall

    written: engineering dept.
    """
    name = "Coil recalled"
    symptom = "Hard and sluggish starting"
    solution = "Replace at the dealer"
    level = 40
    exposed = True
