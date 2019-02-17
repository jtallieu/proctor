"""
Module that provides access to the Proctor registry
or conditions.

The utility functions here could conceivably be wrapped
and exposed via a web endpoint.

All output from these utils should be json format.
"""

import logging
import serializers
from filter_set import FilterSet
from proctor import Proctor, ContextualCondition

log = logging.getLogger("proctor.utils")


def list_conditions():
    """List all the conditions"""
    _proctor = Proctor()
    return map(serializers.registered_condition, _proctor._conditions._registry.values())


def search_conditions(filters, klass=None):
    """
    Search the condition registry

    filters: FilterSet spec
    klass: Class to prefilter results - will observe inheritence
    """
    _proctor = Proctor()
    condition_list = []
    filter_set = FilterSet(filters)
    # Get a dict of conditions
    if klass:
        conditions = _proctor._conditions.get_registered_conditions(klass)
    else:
        conditions = _proctor._conditions._registry.values()

    condition_list = map(serializers.registered_condition, conditions)
    return filter(filter_set.filter, condition_list)


def get_context_condition(condition_id, obj):
    """Get a condition with a context loaded"""
    _proctor = Proctor()
    condition = _proctor._conditions.get_condition(condition_id)
    if not condition:
        raise Exception("Conditions does not exist {}".format(condition_id))
    return serializers.context_condition(ContextualCondition(obj, condition))


def check_condition(condition_id, obj):
    """Get the result of checking a condition on an object"""
    _proctor = Proctor()
    condition = _proctor._conditions.get_condition(condition_id)
    if not condition:
        raise Exception("Conditions does not exist {}".format(condition_id))
    cond = ContextualCondition(obj, condition)
    cond.detect()
    return serializers.context_condition(cond)


def fix_condition(condition_id, obj):
    """Get the result of fixing a condition on an object"""
    _proctor = Proctor()
    condition = _proctor._conditions.get_condition(condition_id)
    if not condition:
        raise Exception("Conditions does not exist {}".format(condition_id))
    cond = ContextualCondition(obj, condition)
    cond.detect()
    if cond.detected:
        cond.rectify()
    return serializers.context_condition(cond)


def get_context_conditions(obj, condition_filters=None):
    """
    Get all conditions for an object
    See search_conditions.
    """
    _proctor = Proctor()
    _filters = condition_filters or {}

    # Get the contextual conditions
    conditions = map(
        lambda x: ContextualCondition(obj, _proctor._conditions.get_condition(x.pid)),
        search_conditions(_filters, obj.__class__)
    )
    # serialize it
    return map(serializers.context_condition, conditions)


def check_conditions(obj, condition_filters=None):
    """
    Get the results of checking all conditions on an object

    Checks only the conditions that match the condition_filters.
    See search_conditions.
    """
    _proctor = Proctor()
    _filters = condition_filters or {}

    # Get the contextual conditions
    conditions = map(
        lambda x: ContextualCondition(obj, _proctor._conditions.get_condition(x.pid)),
        search_conditions(_filters, obj.__class__)
    )

    # Now go run the detector on all the conditions
    for cond in conditions:
        cond.detect()

    # serialize it
    return map(serializers.context_condition, conditions)


def fix_conditions(obj, condition_filters=None):
    """
    Get the results of fixing all detected conditions on an object

    Checks only the conditions that match the condition_filters.
    See search_conditions.
    """
    _proctor = Proctor()
    _filters = condition_filters or {}

    # Get the contextual conditions
    conditions = map(
        lambda x: ContextualCondition(obj, _proctor._conditions.get_condition(x.pid)),
        search_conditions(_filters, obj.__class__)
    )

    # Now go run the detector on all the conditions
    for cond in conditions:
        cond.detect()
        if cond.detected:
            cond.rectify()

    # serialize it
    return map(serializers.context_condition, conditions)
