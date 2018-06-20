import uuid

class Vehicle(object):
    def __init__(self, year, make, model, color, doors):
        self.id = str(uuid.uuid4()).split("-")[-1]
        self.color = color
        self.make = make
        self.doors = doors
        self.model = model
        self.year = year

        self.gas_level = 50
        self.has_flat = False

    def __repr__(self):
        return "{} - {} {} {} {} {}dr({}) gas:{}% flat:{}".format(
            self.id,
            self.year,
            self.make,
            self.model,
            self.color,
            self.doors,
            self.__class__.__name__,
            self.gas_level,
            self.has_flat)


class Sedan(Vehicle):
    pass


class Coupe(Vehicle):
    pass


class Motorcycle(Vehicle):
    pass


class Truck(Vehicle):
    pass
