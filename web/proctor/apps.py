# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.apps import AppConfig
from proctor_lib import Proctor


class ProctorConfig(AppConfig):
    name = 'proctor'

    def ready(self):
        p = Proctor()
        p.load_plugins()