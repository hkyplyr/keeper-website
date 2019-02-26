def get_value(data, index, key):
    if (key in data[index]):
        return data[index][key]
    elif (key in data[index + 1]):
        return data[index + 1][key]
    elif (key in data[index + 2]):
        return data[index + 2][key]
    else:
        raise Exception("Key '{}' could not be found in '{}'.".format(key, data))