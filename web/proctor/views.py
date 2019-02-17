# -*- coding: utf-8 -*-
from __future__ import unicode_literals

# Create your views here.
import json
import logging
import gevent.pool
import gevent.event
from django import http
from django.conf import settings
from django.views.generic import View
from django.template import RequestContext
from django.template.loader import render_to_string
from django.shortcuts import render_to_response, render

from proctor_lib import Proctor
import proctor_lib.utils as putils
from django.apps import apps

log = logging.getLogger('proctor.web')
p = Proctor()


def prep_condition(condition):
    # Set the level name
    condition['level_name'] = "trivial"
    if condition['level'] < 15:
        condition['level_name'] = 'urgent'
    if condition['level'] >= 15:
        condition['level_name'] = 'serious'
    if condition['level'] >= 30:
        condition['level_name'] = 'trivial'
    return condition


def prep_registered_condition(condition):
    return prep_condition(condition)


def get_model_class(class_name):
    """Look up class models"""
    # Try to find the class using the Django apps
    try:
        return apps.get_model(class_name)
    except Exception:
        pass

    # Search for the model in each app's models_module, if the 
    # app label is provided like app.ModelClass 
    app_name = None
    model_name = class_name.split(".", 1)
    if len(model_name) == 2:
        app_name, model_name = model_name
    else:
        model_name = class_name

    if app_name:
        config = apps.get_app_config(app_name)
        if config.models_module:
            klass = getattr(config.models_module, model_name)
            klass.manager = getattr(config.models_module, 'manager')
            return klass

    for config in apps.get_app_configs():
        try:
            log.debug("Checking {} {} for {}".format(config.label, config.models_module, model_name))
            klass = getattr(config.models_module, model_name)
            klass.manager = getattr(config.models_module, 'manager')
            return klass
        except Exception:
            pass
    raise Exception("Unable to find {}".format(class_name))


def get_model_instance(model, id):
    """Get a single instance of a model given an id"""
    if hasattr(model, "objects"):
        return model.objects.get(id=id)
    if hasattr(model, "manager"):
        return model.manager.get(id=id)
    raise Exception("No model instance")


class ItemView(View):
    """Display the instance with the list of conditions that can be checked"""

    template_name = 'proctor/single_context.html'

    def get_context_data(self, **kwargs):
        log.info("{} id {}".format(kwargs.get('model_name'), kwargs.get('model_id')))

        context = {}
        context_class = get_model_class(kwargs.get('model_name'))
        instance = get_model_instance(context_class, kwargs.get('model_id'))

        context['conditions'] = putils.get_context_conditions(instance)
        context['conditions'] = sorted(context['conditions'], key=lambda x: x['level'])
        context['ctxt_klass'] = kwargs.get('model_name')
        context['ctxt_id'] = kwargs.get('model_id')
        return context

    def get(self, request, model_name, model_id):
        ctxt = {}
        ctxt.update(self.get_context_data(model_name=model_name, model_id=model_id))
        map(prep_condition, ctxt['conditions'])
        return render(request, self.template_name, ctxt)


class APIConditionList(View):

    def get(self, request):
        ctxt = RequestContext(request)
        query_params = request.GET.dict()
        model_name = query_params.get('model')
        model_id = query_params.get('model_id')

        if not model_id:
            # Give back all the conditions that apply to the model
            context_class = get_model_class(model_name)
            ctxt['conditions'] = map(prep_registered_condition, putils.search_conditions({}, klass=context_class))
            ctxt['conditions'] = sorted(ctxt['conditions'], key=lambda x: x['level'])
            ctxt['ctxt_klass'] = model_name

        else:
            # Give back contextual conditions based on what actually applies to the instance
            instance = get_model_instance(get_model_class(model_name), model_id)
            ctxt['conditions'] = putils.get_context_conditions(instance)
            ctxt['conditions'] = sorted(ctxt['conditions'], key=lambda x: x['level'])
            ctxt['ctxt_klass'] = model_name
            ctxt['ctxt_id'] = model_id
        return http.HttpResponse(json.dumps(ctxt['conditions']), content_type='application/json')


class ConditionList(View):
    """Handles displaying the condition list without a context instance"""

    def get(self, request, model_name):
        ctxt = {}
        context_class = get_model_class(model_name)
        ctxt['conditions'] = map(prep_registered_condition, putils.search_conditions({}, klass=context_class))
        ctxt['conditions'] = sorted(ctxt['conditions'], key=lambda x: x['level'])
        ctxt['ctxt_klass'] = model_name
        return render(request, 'proctor/no_context.html', ctxt)


class CheckItem(View):
    """Check a specific condition given a context"""

    def get(self, request, pid, fix=False):
        context_class = request.GET.get('model')
        context_id = request.GET.get('model_id')
        log.info("Checking condition {} on {} {}".format(pid, context_class, context_id))

        context_class = get_model_class(context_class)
        instance = get_model_instance(context_class, context_id)

        ctxt = {}
        if fix:
            # The fix_condition method here will internally check if the condition exists
            # before running any fixes.
            ctxt['condition'] = prep_condition(putils.fix_condition(pid, instance))
            log.info("{} attempted fix {}:[{}] on {} {}".format(
                request.user.id,
                pid,
                ctxt['condition'].name,
                request.GET.get('model'),
                context_id))

            # Get a fresh instance and check it again for re-presenting to the user.
            # Ideally this would show that the condition is no longer detected.
            instance = get_model_instance(context_class, context_id)

            # TODO: don't lose the "ran the rectifier" flag from fixing it.
            # Right now, that flag does not get reflected to the user.
            checked_condition = prep_condition(putils.check_condition(pid, instance))
            checked_condition['rectified'] = ctxt['condition']['rectified']
            checked_condition['rectifier_tried'] = ctxt['condition']['rectifier_tried']
            ctxt['condition'] = checked_condition

        else:
            ctxt['condition'] = prep_condition(putils.check_condition(pid, instance))
            if ctxt['condition']['detected']:
                log.info("{} detected {}:[{}] on {} {}".format(
                    request.user.id,
                    pid,
                    ctxt['condition'].name,
                    request.GET.get('model'),
                    context_id))

        # We can return the JSON data or serve up rendered context conditions
        log.info("Sending data as {}".format(request.META['HTTP_ACCEPT']))
        if 'application/fragment' in request.META['HTTP_ACCEPT']:
            ctxt['context_obj'] = instance
            return render(request, 'proctor/fragments/condition_ctxt.html', ctxt)
        else:
            return http.HttpResponse(json.dumps(ctxt['condition']), content_type='application/json')


class CheckAll(View):
    """Check and stream the list of conditions"""

    def post(self, request, model_name):
        context_class = get_model_class(model_name)

        options = json.loads(request.body)
        log.info("check {} on {}".format(model_name, options))

        collect_results = gevent.event.Event()  # a signal to begin waiting for async results

        def check_conditions(item, pids):
            """Greenlet: Runs the conditions on the item"""
            try:
                ctxt = {}
                ctxt['ctxt_klass'] = item.__class__.__name__
                ctxt['ctxt_id'] = item.id
                ctxt['conditions'] = []
                for pid in options['pids']:
                    condition = putils.check_condition(pid, item)
                    ctxt['conditions'].append(condition)
                return ctxt
            except gevent.GreenletExit:
                log.error("GreenletExit in check condition")
                raise Exception("Pre-empted")

        def data_generator(model_class, pids, results):
            """
            Greenlet: Launches and manages a pool of workers that check
            conditions on all the items.
            """
            try:
                pool = gevent.pool.Pool(10)

                collect_results.set()  # Tell the generator to start waiting on results

                # Get the list of id's only first
                # TODO: Checking across all instances is only supported on LDAP models
                #ids = model_class.objects.all().values_list('id', flat=True)
                ids = model_class.manager.ids()

                for dev_id in ids:
                    try:
                        #item = model_class.objects.get(id=dev_id)
                        item = model_class.manager.get(id=dev_id)
                    except (model_class.DoesNotExist, Exception):
                        continue

                    async = gevent.event.AsyncResult()
                    pool.spawn(check_conditions, item, pids).link(async)
                    results.append(async)

                pool.join()
            except gevent.GreenletExit:
                log.info("GreenletExit - clean up pool")
            except:
                log.exception("unexpected death")
            finally:
                log.error("Killing pools")
                pool.kill()  # The socket being written to may go away, so cleanup

        def generator():
            yield "Starting to crunch\n"
            results = []  # Hold asynchronous results from the workers launched by the generator
            manager = gevent.spawn(data_generator, context_class, options['pids'], results)

            collect_results.wait()
            done = False
            yield "Ready for results\n"
            while not done:

                # Wait some results to be ready from the check_conditions workers
                ready_results = gevent.wait(results, timeout=4)
                try:
                    yield "."  # Periodically send some bits so the connections stays open
                    for res in ready_results:
                        results.remove(res)
                        try:
                            # Provide html fragments to the generator
                            ctxt = res.get()
                            ctxt['conditions'] = map(prep_condition, ctxt['conditions'])
                            html = render_to_string('proctor/fragments/context_frag.html', ctxt)
                            log.info('yielding for {}'.format(ctxt['ctxt_id']))
                            yield "+++{}---".format(html)

                        except GeneratorExit:
                            raise
                        except:
                            # Continue checking items
                            log.exception("unexpected exception from greenlet")

                except GeneratorExit:
                    # No one is listening for data - kill the threads and exit clean
                    log.info("Proctor Generator pre-empted - killing pools (outside loop)")
                    manager.kill()
                    log.info("Sent the kill command to manager")

                try:
                    # Die when the pool is done AND the results are empty
                    manager.get(block=False)
                    if not results:
                        log.info("Exiting")
                        done = True
                except gevent.Timeout:
                    pass  # The manager is still working - wait for more results
                gevent.sleep(2)

        if context_class:
            try:
                # TODO: stream json based on same params as individual checks
                response = http.HttpResponse(generator())
                response['X-Accel-Buffering'] = "no"
            except:
                log.exception("unexpected exception")
        else:
            response = http.HttpResponse(
                "Unable to check all {}s - You must perform checks for each {}".format(
                    model_name,
                    model_name),
                status=400)
        return response
