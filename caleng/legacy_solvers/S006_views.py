from engine.solvers import S006_solvers
from engine.solvers.grandpa_views import Grandpa_Calc
from engine.forms import CalcExtraDataS006
from django import forms


class S006_EC3(Grandpa_Calc):

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
            ("LANDING", "landing", ["H", "U"], True),
            ("ARRIVING", "beam", ["H", "L", "U"], False),
            ("CLIP_ANGLE", "clip", ["L"], False),
        ]
        self.extra_data_strings = [
            # (USE_STRING, FORM_PREFIX, FormClass),
            ("MAIN", "main", CalcExtraDataS006),
        ]
        self.plate_strings = [
            # (USE_STRING, FORM_PREFIX, FORM_TYPE),
            ("DUMMY_PLATE", "ang_bolts", "DUMMY"),
            ("BOLTED_STIFFENER", "stiff", "BOLTED_STIFFENER"),
        ]
        self.sheetnumber = "S006"
        self.solver = S006_solvers.S006_EC3

    def form_tweaks(self):
        self.forms["ang_bolts_plate_form"].\
            fields['width'].widget = forms.HiddenInput()
        self.forms["ang_bolts_plate_form"].\
            fields['length'].widget = forms.HiddenInput()
