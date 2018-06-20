import operator


class Filter(object):
    """
    Filter class to filter on properties of a dict.

    Arguments: property, op, value

    Will type the existing value of the dictionary
    property and attempt to coerce the compare value
    to the property's value type.
    """

    COMP_FUNCS = {
        'like': lambda x, y: y in x,  # Sub string
        'in': lambda x, y: x in y  # mostly for item in list
    }

    def __init__(self, prop, op, value):
        self.property = prop
        self.op = op
        self.value = value
        self.__func = self.generate_function(self.op)

    def generate_function(self, op):
        """
        Makes the function that tests for equality.

        If it's not in the predefined functions, use the
        'op' as the function
        """
        return Filter.COMP_FUNCS.get(
            op,
            lambda x, y: getattr(operator, op)(x, y)
        )

    def __call__(self, item):
        """Tests the value of the property against the compare function"""
        item_value = item.get(self.property)
        typed_value = self.value

        # Coerce boolean compare value
        if isinstance(item_value, bool):
            if self.value not in ['False', 'True', False, True]:
                raise TypeError("Wrong type - expected bool for {}".format(self.property))
            typed_value = False if self.value in ['False', False] else True

        # Coerce strings - leave everything else alone
        elif isinstance(self.value, basestring):
            typed_value = type(item_value)(self.value)

        return self.__func(item_value, typed_value)


class FilterSet(object):
    """
    A set of filters to apply to a dictionary.

    Initialized from a dict of:

        {<key>__<op>: <value>}

        ex: { "name__like": "Error", "level__lt": 20}

    to create a set of Filters

    Where op is a function defined in either the operator
    module or by Filter.COMP_FUNCS
    """

    def __init__(self, filter_spec):
        self.__filters = []
        self.__filter_spec = None
        self.init(filter_spec)

    def init(self, filter_spec):
        self.__filters = []
        for key, value in filter_spec.iteritems():
            parts = key.split("__")
            prop_name = key

            _func = "eq"
            if len(parts) == 2:
                _func = parts[1]
                prop_name = parts[0]

            self.__filters.append(Filter(prop_name, _func, value))

    def filter(self, item):
        for check in self.__filters:
            if not check(item):
                return False
        return True


if __name__ == "__main__":
    from pprint import pprint
    family = [
        dict(age=44, first_name="Joey", last_name="Tallieu III", male=True),
        dict(age=13, first_name="Vincent", last_name="Tallieu", male=True),
        dict(age=34, first_name="Andrea", last_name="Mueller", male=False),
        dict(age=14, first_name="Kirstin", last_name="Mueller", male=False)
    ]

    print
    print "The Tallieu's"
    filter_set = FilterSet({
        'last_name__like': "Tallieu"
    })
    tallieus = filter(filter_set.filter, family)
    pprint(tallieus)

    print
    print "Girls:"
    girls = filter(FilterSet({'male': "False"}).filter, family)
    pprint(girls)

    print
    print "Women over 30"
    fil = FilterSet({'age__gt': 30, 'male': False})
    pprint(filter(fil.filter, family))
