from engine.solvers import S002_solvers
from engine.solvers.grandpa_views import Grandpa_Calc
from engine.forms import CalcExtraDataS002


class S002_EC3(Grandpa_Calc):

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
            ("ARRIVING", "bracing", ["TUB", "PIP"], False),
        ]
        self.plate_strings = [
            # FORM_TYPE's -> BOLTED, BOLTED_STIFFENER, WELDED, DUMMY
            # (USE_STRING, FORM_PREFIX, FORM_TYPE),
            ("COVER_PLATE", "cover", "BOLTED"),
            ("INPIPE_PLATE", "inpipe", "WELDED"),
            ("PIPE_STIFFENER", "stiffener", "WELDED"),
        ]
        self.extra_data_strings = [
            # (USE_STRING, FORM_PREFIX, FormClass),
            ("MAIN", "main", CalcExtraDataS002),
        ]
        self.sheetnumber = "S002"
        self.solver = S002_solvers.S002_EC3

    def form_tweaks(self):
        self.forms["stiffener_plate_form"].fields["width"].initial = 40
        self.forms["stiffener_plate_form"].fields["length"].initial = 150

        # if not self.forms["inpipe_plate_form"].is_bound:
        #     print("IS NOT BOUND")
        #     self.forms["inpipe_plate_form"].\
        #         initial = {'width': 40, 'length': 150}
        # else:
        #     print("IS BOUND")
