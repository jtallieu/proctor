# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import logging
from django.apps import AppConfig
from proctor_lib import Proctor

log = logging.getLogger('cars')


class CarsConfig(AppConfig):
    name = 'cars'

    def ready(self):
        module_path = os.path.dirname(os.path.abspath(__file__))
        log.critical('Cars is ready {}'.format(module_path))
        proctor = Proctor()
        proctor.add_paths([os.path.join(module_path, "proctor_plugins")])
        from cars.models import vehicles
        for v in vehicles.values():
            log.info("{}".format(v))
