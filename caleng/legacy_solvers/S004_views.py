from engine.solvers import S004_solvers
from engine.solvers.grandpa_views import Grandpa_Calc
from engine.forms import CalcExtraDataS001


class S004_EC3(Grandpa_Calc):
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
            ("ULS", "uls", "FULL"),
            ("SLS", "sls", "FULL"),
        ]
        self.profile_strings = [
            # TYPE_LIST=None is all types
            # (USE_STRING, FORM_PREFIX, TYPE_LIST, CAN_BE_ANY),
            ("LANDING", "column", ["H"], True),
            ("ARRIVING", "beam", None, False),
        ]
        self.plate_strings = [
            # FORM_TYPE's -> BOLTED, BOLTED_STIFFENER, WELDED, DUMMY
            # (USE_STRING, FORM_PREFIX, FORM_TYPE),
            ("END_PLATE", "end", "BOLTED"),
        ]
        self.extra_data_strings = [
            # (USE_STRING, FORM_PREFIX, FormClass),
            ("MAIN", "main", CalcExtraDataS001),
        ]
        self.position_strings = [
            # (USE_STRING, FORM_PREFIX, PROFILE_PREFIX),
            ("MAIN", "main", "beam"),
        ]
        self.extra_bracing_strings = [
            # (USE_STRING, FORM_PREFIX),
            ("MAIN", "main"),
        ]
        self.sheetnumber = "S004"
        self.solver = S004_solvers.S004_EC3

    def form_tweaks(self):
        self.forms["main_position_form"].convert_to_plate_and_profile_pos()
        self.forms["main_position_form"].\
            dropdown_rotation(["0", "90", "180", "270"])
