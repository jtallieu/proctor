
def registered_condition(reg):
    data = reg.condition.class_info()
    data.detectors = len(reg.detectors)
    data.rectifiers = len(reg.rectifiers)
    data.detectable = True if data.detectors else False
    data.rectifiable = True if data.rectifiers else False
    return data


def context_condition(cond):
    data = cond.dict()
    data.name = data.check_key
    del data['check_key']

    data.ctxt_class = cond.context.__class__.__name__
    data.ctxt_id = cond.context.id
    data.exposed = cond.exposed
    return data
