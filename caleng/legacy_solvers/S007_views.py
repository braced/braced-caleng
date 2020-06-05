from engine.solvers import S007_solvers
from engine.solvers.grandpa_views import Grandpa_Calc


class S007_EC3(Grandpa_Calc):

    def fill_meta(self):
        self.bolt_array_strings = [
            # (USE_STRING, FORM_PREFIX, BOLT_FORM_PREFIX),
            ("MAIN", "main", "main"),
        ]
        self.bolt_strings = [
            # (USE_STRING, FORM_PREFIX),
            ("MAIN", "main"),
        ]
        self.force_strings = [
            # (USE_STRING, FORM_PREFIX, FORM_TYPE),
            ("ULS", "uls", "FULL"),
            ("SLS", "sls", "FULL"),
        ]
        self.profile_strings = [
            # TYPE_LIST=None is all types
            # (USE_STRING, FORM_PREFIX, TYPE_LIST, CAN_BE_ANY),
            ("LANDING", "bottom_column", None, True),
            ("ARRIVING", "top_column", None, True),
        ]
        self.plate_strings = [
            # (USE_STRING, FORM_PREFIX, FORM_TYPE),
            ("END_PLATE", "end", "BOLTED"),
        ]
        self.position_strings = [
            # (USE_STRING, FORM_PREFIX, PROFILE_PREFIX),
            ("MAIN", "main", "top_column"),
        ]
        self.sheetnumber = "S007"
        self.solver = S007_solvers.S007_EC3

    def form_tweaks(self):
        self.forms["main_position_form"].convert_to_plate_and_profile_pos()
