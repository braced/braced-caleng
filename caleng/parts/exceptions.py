# NOW THIS IS NOT USED!!
# THIS FILE CAN BE DELTED


class BracedError(Exception):
    pass


class CalengCrash(BracedError):
    def __init__(self, message):
        super().__init__(message)
