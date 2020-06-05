from pint import UnitRegistry
ureg = UnitRegistry()
Q = ureg.Quantity
ureg.default_format = '.2f~P'
