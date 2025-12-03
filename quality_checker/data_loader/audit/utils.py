DISTRIBUTION = 'http://www.w3.org/ns/dcat#distribution'
ID = '@id'


def get_distributions(dataset):
    return dataset[DISTRIBUTION] if DISTRIBUTION in dataset else []


def is_defined(dictionary, _property):
    """ Verif if a property is defined. return a boolean. """
    return (
        _property in dictionary
        and any(_list := dictionary[_property])
        and any(any(_dict.values()) for _dict in _list)
    )


def count_defined(distributions, _property):
    return sum(is_defined(distribution, _property) for distribution in distributions)


def percent_defined(distributions, _property):
    """ Return the percent of distributions which properly define the property. """
    defined, total = count_defined(distributions, _property), len(distributions)
    return round(defined / total, 2) if total > 0 else 0


def is_vocabulary_used(dictionary, _property, vocabulary):
    """ Check if a property is using a controlled vocabulary.
        Return false if the property cannot be found. 
    """
    return (
        _property in dictionary
        and any(_list := dictionary[_property])
        and any(_dict[ID] in vocabulary for _dict in _list if ID in _dict)
    )


def count_vocabulary_use(distributions, _property, vocabulary):
    """ Count the number of distributions using a controlled vocabulary for their keys. """
    truth_table = [
        is_vocabulary_used(distribution, _property, vocabulary)
        for distribution in distributions
    ]

    return sum(truth_table)


def percent_vocabulary_use(distributions, _property, vocabulary):
    """ Return the percent of distributions which properly use a controlled vocabulary. """
    total = len(distributions)
    defined = count_vocabulary_use(distributions, _property, vocabulary)
    return round(defined / total, 2) if total > 0 else 0


def join_dict(dictionaries):
    """ Take multiple dictionaries with the same keys
        and return a single dictionary with value-lists.
        Used to assemble scores.

        Exemple: 
            
            join_dict([{'a': 10}{'a': 10}]) 
            > return {'a': [10, 10]} 
    """
    new_dict = dict()
    keys = dictionaries[0].keys()
    values = (d.values() for d in dictionaries)
    for key, value in zip(keys, zip(*values)):
        new_dict[key] = list(value)

    return new_dict
