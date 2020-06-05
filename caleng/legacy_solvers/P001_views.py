from engine.solvers import P001_solvers
from engine.solvers.grandpa_views import Grandpa_Calc
from django.views import View
from django.shortcuts import render
from caleng.parts.settings import *


class P001_EC3(Grandpa_Calc):

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
            ("ULS", "uls", "SHEAR"),
            ("SLS", "sls", "SHEAR"),
        ]
        self.sheetnumber = "P001"
        self.solver = P001_solvers.P001_EC3


class P001_AISC11(View):

    def get(self, request):
        context = {
            'calcs': CALCULATION_LINKS,
            'calc_names': CALCULATION_NAMES,
        }
        return render(request, "enginesheets/base_engine.html", context)
