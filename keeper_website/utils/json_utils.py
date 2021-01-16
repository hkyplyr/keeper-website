def get_value(data, index, key):
    if (key in data[index]):
        return data[index][key]
    elif (key in data[index + 1]):
        return data[index + 1][key]
    elif (key in data[index + 2]):
        return data[index + 2][key]
    elif (key in data[index + 3]):
        return data[index + 3][key]
    elif (key in data[index + 4]):
        return data[index + 4][key]
    elif (key in data[index + 5]):
        return data[index + 5][key]
    else:
        raise Exception("Key '{}' could not be found in '{}' at index '{}'."
                        .format(key, data, index))


def get_ordinal(value):
    """Provides the ordinal value for a given integer
    For example `1` returns 'st', `2` returns 'nd', etc.

    Keyword arguments:
    value -- the integer used to retrieve the ordinal
    """
    value = int(value)
    if value % 100//10 !=1:
        if value % 10 == 1:
            return f'{value}st'
        elif value % 10 == 2:
            return f'{value}nd'
        elif value % 10 == 3:
            return f'{value}rd'
        else:
            return f'{value}th'
    else:
        return f'{value}th'
