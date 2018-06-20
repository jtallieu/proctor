"""
Example usage of the Proctor utility functions.

This is pseudo modeling for REST exposure.
"""

import logging
import settings
import logging.config
logging.config.dictConfig(settings.LOGGING_CONF)
log = logging.getLogger("main")

import os
import sys
import os.path
from pprint import pprint, pformat
from models import generator, vehicles

import proctor
import proctor.utils as putils

# Tell proctor where to load plugins
proctor_dir = "../proctor_plugins"
abs_pluginpath = os.path.abspath(os.path.join(os.path.dirname(__file__), proctor_dir))
p = proctor.Proctor()
p.add_paths([abs_pluginpath])


if __name__ == "__main__":
    p.show_registry()

    print
    print "_" * 40
    print "/proctor/conditions:"
    print "List all the conditions in the registry\n"
    conds = putils.list_conditions()
    log.debug(pformat(conds))

    car = vehicles.Coupe(2009, "Ford", "Mustang", "red", 5)

    print
    print "_" * 40
    print "/proctor/conditions/710D80B5A3/context?class=Vehicle&ctx_id={}".format(car.id)
    print "Get the conditions within the context of each car"
    print car, "\n"
    condition = putils.get_context_condition("710D80B5A3", car)
    log.debug("ContextCondition:\n{}".format(pformat(condition)))
    print "_" * 40

    print
    print "_" * 40
    print "/proctor/conditions/710D80B5A3/check?class=Vehicle&ctx_id={}".format(car.id)
    print "Check that condition on a car\n"
    condition = putils.check_condition("710D80B5A3", car)
    log.debug("ContextCondition:\n{}".format(pformat(condition)))
    print "_" * 40

    print
    print "_" * 40
    print "/proctor/conditions/710D80B5A3/fix?class=Vehicle&ctx_id={}\n".format(car.id)
    print "Check and fix that condition on a car"
    condition = putils.fix_condition("710D80B5A3", car)
    log.debug("ContextCondition:\n{}".format(pformat(condition)))
    print car
    print "_" * 40

    car = vehicles.Sedan(2012, "Ford", "Camaro", "red", 2)
    car.gas_level = 0
    print
    print "_" * 40
    print "/proctor/check?class=Vehicle&ctxt_id={}".format(car.id)
    print "Check all the conditions on a car"
    print car, "\n"
    conditions = putils.check_conditions(car)
    log.debug("ContextualConditions:\n{}".format(pformat(conditions)))
    print "_" * 40

    print
    print "_" * 40
    print "/proctor/check?class=Vehicle&ctxt_id={}&fix=True".format(car.id)
    print "Fix all the conditions on a car"
    print car, "\n"
    conditions = putils.fix_conditions(car)
    log.debug("ContextualConditions:\n{}".format(pformat(conditions)))
    print car
    print "_" * 40

    car = vehicles.Coupe(2009, "Ford", "Mustang", "red", 5)
    car.gas_level = 0
    print
    print "_" * 40
    print "/proctor/check?class=Vehicle&ctxt_id={}&exposed=False".format(car.id)
    print "Check all the conditions on a car that are NOT exposed"
    print car, "\n"
    conditions = putils.fix_conditions(car, {'exposed': False})
    log.debug("ContextualConditions:\n{}".format(pformat(conditions)))
    print "_" * 40

    print
    print "_" * 40
    print "/proctor/check?class=Vehicle&ctxt_id={}&level__ge=10&fix=True".format(car.id)
    print "Check all the conditions on a car that are >= level 10 and fix them"
    conditions = putils.fix_conditions(car, {'exposed': True, 'level__ge': '10'})
    log.debug("ContextualConditions:\n{}".format(pformat(conditions)))
    print "_" * 40
