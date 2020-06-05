from engine.solvers import S003_solvers
from engine.solvers.grandpa_views import Grandpa_Calc
from engine.forms import CalcExtraDataS002


class S003_EC3(Grandpa_Calc):

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
            ("ULS", "uls", "TIE"),
            ("SLS", "sls", "TIE"),
        ]
        self.profile_strings = [
            # TYPE_LIST=None is all types
            # (USE_STRING, FORM_PREFIX, TYPE_LIST, CAN_BE_ANY),
            ("LANDING", "landing", ["H", "TUB", "PIP"], True),
            ("ARRIVING", "bracing", ["H", "L", "U"], False),
        ]
        self.plate_strings = [
            # FORM_TYPE's -> BOLTED, BOLTED_STIFFENER, WELDED, DUMMY
            # (USE_STRING, FORM_PREFIX, FORM_TYPE),
            ("GUSSET_PLATE", "gusset", "BOLTED"),
        ]
        self.extra_data_strings = [
            # (USE_STRING, FORM_PREFIX, FormClass),
            ("MAIN", "main", CalcExtraDataS002),
        ]
        self.sheetnumber = "S003"
        self.solver = S003_solvers.S003_EC3
