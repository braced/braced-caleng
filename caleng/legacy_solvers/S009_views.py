from engine.solvers import S009_solvers
from engine.solvers.grandpa_views import Grandpa_Calc
from engine.forms import CalcExtraDataS009
from django import forms


class S009_EC3(Grandpa_Calc):

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
            ("LANDING", "beam_1", ["H", "U"], True),
            ("ARRIVING", "beam_2", ["H", "U"], True),
        ]
        self.plate_strings = [
            # (USE_STRING, FORM_PREFIX, FORM_TYPE),
            ("END_PLATE", "end", "BOLTED"),
            ("STIFFENER", "stiffener", "WELDED"),
        ]
        self.position_strings = [
            # (USE_STRING, FORM_PREFIX, PROFILE_PREFIX),
            # ("MAIN", "main", "beam_1"),
        ]
        self.extra_data_strings = [
            # (USE_STRING, FORM_PREFIX, FormClass),
            ("MAIN", "main", CalcExtraDataS009),
        ]
        self.sheetnumber = "S009"
        self.solver = S009_solvers.S009_EC3

    def form_tweaks(self):
        self.forms["stiffener_plate_form"].fields["width"].initial = 40
        self.forms["stiffener_plate_form"].fields["length"].initial = 150
        self.forms["stiffener_plate_form"].\
            fields['weld_length'].widget = forms.HiddenInput()
        self.forms["stiffener_plate_form"].\
            fields['weld_throat'].widget = forms.HiddenInput()
