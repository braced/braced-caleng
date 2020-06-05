from engine.solvers import S005_solvers
from engine.solvers.grandpa_views import Grandpa_Calc
from engine.forms import CalcExtraDataS005


class S005_EC3(Grandpa_Calc):

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
            ("LANDING", "landing", ["H", "U"], True),
            ("ARRIVING", "beam", None, False),
        ]
        self.plate_strings = [
            # FORM_TYPE's -> BOLTED, BOLTED_STIFFENER, WELDED, DUMMY
            # (USE_STRING, FORM_PREFIX, FORM_TYPE),
            ("END_PLATE", "end", "BOLTED"),
        ]
        self.extra_data_strings = [
            # (USE_STRING, FORM_PREFIX, FormClass),
            ("MAIN", "main", CalcExtraDataS005),
        ]
        self.cover_plates_selection_strings = [
            # (USE_STRING, FORM_PREFIX),
            # ("MAIN", "main"),
        ]
        self.position_strings = [
            # (USE_STRING, FORM_PREFIX, PROFILE_PREFIX),
            ("MAIN", "main", "beam"),
        ]
        self.sheetnumber = "S005"
        self.solver = S005_solvers.S005_EC3

    def form_tweaks(self):
        self.forms["main_position_form"].convert_to_plate_and_profile_pos()
