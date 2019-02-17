# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

# Create your models here.

import uuid
ID = 1

class Vehicle(object):
    def __init__(self, year, make, model, color, doors):
        #self.id = str(uuid.uuid4()).split("-")[-1]
        global ID
        self.id = str(ID)
        ID = ID + 1
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

vehicles = {}


def make_models():
    _ = Sedan(2017, "Toyota", "Camary", "white", 4)
    vehicles[_.id] = _

    _ = Sedan(2017, "Toyota", "Camary", "red", 4)
    _.gas_level = 20
    vehicles[_.id] = _

    _ = Sedan(1999, "Toyota", "Camary", "green", 4)
    vehicles[_.id] = _

    _ = Sedan(2006, "Ford", "Fusion", "white", 3)
    _.has_flat = True
    vehicles[_.id] = _

    _ = Sedan(2006, "Nissan", "Altima", "gray", 4)
    vehicles[_.id] = _

    _ = Coupe(2009, "Ford", "Mustang", "red", 2)
    vehicles[_.id] = _

    _ = Coupe(2017, "Dodge", "Mustang", "white", 4)
    vehicles[_.id] = _

    _ = Coupe(2014, "Chevy", "Camaro", "white", 4)
    _.has_flat = True
    vehicles[_.id] = _

    _ = Coupe(2016, "Toyota", "86", "red", 3)
    vehicles[_.id] = _

    _ = Truck(2016, "Toyota", "Tacoma", "red", 4)
    vehicles[_.id] = _

    _ = Truck(2016, "Ford", "F150", "gray", 2)
    _.has_flat = True
    _.gas_level = 0
    vehicles[_.id] = _


class ModelManager(object):
    def get(self, id=id):
        global vehicles
        return vehicles[id]

    def all(self):
        global vehicles
        for val in vehicles.itervalues():
            yield val

    def ids(self):
        global vehicles
        for _id in vehicles.iterkeys():
            yield _id

manager = ModelManager()

make_models()
