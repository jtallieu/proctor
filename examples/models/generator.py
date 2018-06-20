import vehicles as models

vehicles = {}


def make_models():
    _ = models.Sedan(2017, "Toyota", "Camary", "white", 4)
    vehicles[_.id] = _

    _ = models.Sedan(2017, "Toyota", "Camary", "red", 4)
    _.gas_level = 20
    vehicles[_.id] = _

    _ = models.Sedan(1999, "Toyota", "Camary", "green", 4)
    vehicles[_.id] = _

    _ = models.Sedan(2006, "Ford", "Fusion", "white", 3)
    _.has_flat = True
    vehicles[_.id] = _

    _ = models.Sedan(2006, "Nissan", "Altima", "gray", 4)
    vehicles[_.id] = _


    _ = models.Coupe(2009, "Ford", "Mustang", "red", 2)
    vehicles[_.id] = _

    _ = models.Coupe(2017, "Dodge", "Mustang", "white", 4)
    vehicles[_.id] = _

    _ = models.Coupe(2014, "Chevy", "Camaro", "white", 4)
    _.has_flat = True
    vehicles[_.id] = _

    _ = models.Coupe(2016, "Toyota", "86", "red", 3)
    vehicles[_.id] = _


    _ = models.Truck(2016, "Toyota", "Tacoma", "red", 4)
    vehicles[_.id] = _

    _ = models.Truck(2016, "Ford", "F150", "gray", 2)
    _.has_flat = True
    _.gas_level = 0
    vehicles[_.id] = _

make_models()