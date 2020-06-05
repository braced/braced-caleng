from engine.solvers import P002_solvers
from engine.solvers.grandpa_views import Grandpa_Calc


class P002_EC3(Grandpa_Calc):

    def fill_meta(self):
        self.bolt_array_strings = [
            # (USE_STRING, FORM_PREFIX, BOLT_FORM_PREFIX),
            ("MAIN", "main", "main"),
        ]
        self.bolt_strings = [
            # (USE_STRING, FORM_PREFIX),
            ("MAIN", "main")
        ]
        self.force_strings = [
            # (USE_STRING, FORM_PREFIX, FORM_TYPE),
            ("ULS", "uls", "AXIAL"),
            ("SLS", "sls", "AXIAL"),
        ]
        self.plate_strings = [
            # FORM_TYPE's -> BOLTED, BOLTED_STIFFENER, WELDED, DUMMY
            # (USE_STRING, FORM_PREFIX, FORM_TYPE),
            ("END_PLATE", "end", "DUMMY"),
        ]
        self.sheetnumber = "P002"
        self.solver = P002_solvers.P002_EC3
