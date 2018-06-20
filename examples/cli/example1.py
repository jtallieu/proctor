import logging
import settings
import logging.config
logging.config.dictConfig(settings.LOGGING_CONF)
log = logging.getLogger("main")

import os
import os.path
from pprint import pprint
from models import generator
from proctor import Proctor

proctor_dir = "../proctor_plugins"

abs_pluginpath = os.path.abspath(os.path.join(os.path.dirname(__file__), proctor_dir))
Proctor([abs_pluginpath]).load_plugins()

p = Proctor()

if __name__ == "__main__":
    pprint(generator.vehicles.values())
    p.show_registry()

    
    print "Checking Cars"
    print "=" * 60
    print
    for car in generator.vehicles.values():
        print car
        print "-" * 60
        cs = [x.dict() for x in p.detect_conditions(car) if x.detected]

        for c in cs:
            print "\t- {} : {}".format(c.check_key, "Can Fix" if c.rectifiable else "No fix available")
            print "\t\tFix: {}".format(c.solution)

        if cs:
            pprint(cs)
        print
    