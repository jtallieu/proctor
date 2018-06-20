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
import os.path
from pprint import pformat
from models import vehicles as veh

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
    print "Get the conditions by ID"
    print "/proctor/conditions/710D80B5A3"
    log.debug(pformat(putils.search_conditions({
        'pid': '710D80B5A3'
    })))

    print
    print "_" * 40
    print "Find conditions below a certain level"
    print "/proctor/conditions?level__lt=20"
    log.debug(pformat(putils.search_conditions({
        'level__lt': '20',
    })))

    print
    print "_" * 40
    print "Find conditions above level 20 and exposed"
    print "/proctor/conditions?level__lt=20&exposed=True"
    log.debug(pformat(putils.search_conditions({
        'level__ge': '20',
        'exposed': 'True'
    })))

    print
    print "_" * 40
    print "Find conditions where name is like 'Oil'"
    print "/proctor/conditions?name__like=Oil"
    log.debug(pformat(putils.search_conditions({
        'name__like': 'Oil'
    })))

    print
    print "_" * 40
    print "Find conditions that apply to Coupes"
    print "/proctor/conditions?context=Coupe"
    log.debug(pformat(putils.search_conditions({}, veh.Coupe)))

    print
    print "_" * 40
    print "Find conditions that apply to Vehicles"
    print "/proctor/conditions?context=Vehicle"
    log.debug(pformat(putils.search_conditions({}, veh.Vehicle)))
