from django.core.cache import cache


# THIS MODULE CONTAINING USEFULL CLASES FOR REPORTING AND OTHER TOOLS
TYPE_CODE = {
    100: "info",
    101: "info-title",
    200: "checked",
    300: "warning",
    500: "fail",
}

SECTION_CODES = {
    0: "info and project",
    10: "setups",
    20: "bolt calcs",
    30: "plate calcs",
    40: "profile calcs",
    50: "final results",
}


# REPORT CLASS
class Report:
    def __init__(self, calc):
        self.ASCII_banner = "" + \
            "  |                                  |    _)        \n" + \
            "  __ \    __|  _` |   __|   _ \   _` |     |   _ \  \n" + \
            "  |   |  |    (   |  (      __/  (   |     |  (   | \n" + \
            " _.__/  _|   \__,_| \___| \___| \__,_| _) _| \___/  \n"

        self.lines = []
        self.calc = calc
        self.report = None  # <- ESTO PUEDE QUE HAGA QUE BORRARLO NO?
        self.fillInfo()

    def getLines(self):
        return self.lines

    def getBanner(self):
        return self.ASCII_banner

    def addLine(self, type_code, sect_code, desc_string, calc_string):
        stuff = {
            'type_code': type_code,
            'sect_code': sect_code,
            'desc_string': desc_string,
            'calc_string': calc_string,
        }
        self.lines.append(stuff)

    def set_safe(self):
        self.calc.is_structural_safe = True
        self.calc.save()

    def set_unsafe(self):
        self.calc.is_structural_safe = False
        self.calc.save()

    def to_cache(self):
        # Saving report to cache to alow downloads
        cache_pk = 'calc' + str(self.calc.id)
        cache.set(cache_pk, self)
        return cache_pk

    def to_cache_by_uuid(self):
        # Saving report to cache to alow downloads
        cache_pk = self.calc.uuid
        cache.set(cache_pk, self)
        return cache_pk

    def fillInfo(self):
        self.addLine(101, 0, "PROJECT: ", str(self.calc.project))
        self.addLine(100, 0, "STRUCTURE: ", str(self.calc.structure))
        self.addLine(100, 0, "SHEETNUMBER: ", str(self.calc.enginesheet))
        self.addLine(100, 0, "CALCULATION: ", str(self.calc.name))
        self.addLine(100, 0, "UUID: ", str(self.calc.uuid))
        self.addLine(100, 0, "DATE AND TIME: ", str(self.calc.created))
        self.addLine(100, 0, "ENGINEER: ", str(self.calc.user.get_full_name()))
        self.addLine(100, 0, "COMPANY: ", str(
            self.calc.user.profile.team.company))
        self.addLine(100, 0, "TEAM: ", str(self.calc.user.profile.team))
