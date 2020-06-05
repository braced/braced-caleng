from engine.solvers import S008_solvers
from engine.solvers.grandpa_views import Grandpa_Calc
from engine.forms import CalcExtraDataS008


class S008_EC3(Grandpa_Calc):

    def fill_meta(self):
        self.bolt_array_strings = [
            # (USE_STRING, FORM_PREFIX, BOLT_FORM_PREFIX),
            ("FLANGE", "flange", "flange"),
            ("WEB", "web", "web"),
        ]
        self.bolt_strings = [
            # (USE_STRING, FORM_PREFIX),
            ("FLANGE", "flange"),
            ("WEB", "web"),
        ]
        self.force_strings = [
            # (USE_STRING, FORM_PREFIX, FORM_TYPE),
            ("ULS", "uls", "FULL"),
            ("SLS", "sls", "FULL"),
        ]
        self.profile_strings = [
            # TYPE_LIST=None is all types
            # (USE_STRING, FORM_PREFIX, TYPE_LIST, CAN_BE_ANY),
            ("LANDING", "bottom_column", ["H", "U"], False),
            ("ARRIVING", "top_column", ["H", "U"], False),
        ]
        self.plate_strings = [
            # (USE_STRING, FORM_PREFIX, FORM_TYPE),
            ("FLANGE_COVER_PLATE", "flange_cover", "BOLTED"),
            ("WEB_COVER_PLATE", "web_cover", "BOLTED"),
        ]
        self.cover_plates_selection_strings = [
            # (USE_STRING, FORM_PREFIX),
            ("MAIN", "main"),
        ]
        self.extra_data_strings = [
            # (USE_STRING, FORM_PREFIX, FormClass),
            ("MAIN", "main", CalcExtraDataS008),
        ]
        self.sheetnumber = "S008"
        self.solver = S008_solvers.S008_EC3
