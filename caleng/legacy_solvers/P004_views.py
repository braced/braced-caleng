from engine.solvers import P004_solvers
from engine.solvers.grandpa_views import Grandpa_Calc


class P004_EC3(Grandpa_Calc):

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
        self.profile_strings = [
            # TYPE_LIST=None is all types
            # (USE_STRING, FORM_PREFIX, TYPE_LIST, CAN_BE_ANY),
            ("MAIN", "main", None, True),
        ]
        self.plate_strings = [
            # FORM_TYPE's -> BOLTED, BOLTED_STIFFENER, WELDED, DUMMY
            # (USE_STRING, FORM_PREFIX, FORM_TYPE),
            ("END_PLATE", "end", "DUMMY"),
        ]
        self.position_strings = [
            # (USE_STRING, FORM_PREFIX, PROFILE_PREFIX),
            ("MAIN", "main", "main"),
        ]
        self.sheetnumber = "P004"
        self.solver = P004_solvers.P004_EC3

    def form_tweaks(self):
        self.forms["main_position_form"].convert_to_plate_and_profile_pos()
