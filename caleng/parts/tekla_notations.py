from caleng.parts.unit_registry import *
from decimal import Decimal as D
from caleng.parts.exceptions import CalengCrash
# This module parses tekla notations to magnitudes
# Magnitudes are represented as pint objects
# Group of magnitudes as lists


def get_dist_list(string):
    try:
        elements = string.split()
        dist_list = []
        for index, element in enumerate(elements):
            if "*" in element:
                times = element.split("*")[0]
                dist = element.split("*")[1]
                li = [dist] * int(times)
                dist_list.extend(li)
            else:
                dist_list.append(element)

        # Now we need to verify all data. A evil user can fuck us here
        # If something crashes we raise a message
        return_list = []
        for item in dist_list:
            return_list.append(Q(D(item), "mm"))
    except Exception as e:
        raise CalengCrash("Crashed when parsing tekla notation distances: " +
                          str(e))
    return return_list
