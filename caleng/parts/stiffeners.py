# This module extends the steel.py module.


from decimal import Decimal as D
from caleng.parts.exceptions import CalengCrash
from caleng.parts.unit_registry import *
from caleng.parts.steel import BoltedPlate, Plate
import numpy as np


class Stiffener(Plate):
    """ Basic stiffener in a H Shape profile """

    #     | Fp_Ed
    #     v
    # ==================
    # |       ||
    # |       ||
    # |       ||
    # |       ||
    # |       ||
    # |       ||
    # ==================

    def __init__(self, plate_model, host_profile, report):
        # Plate model and profile object are passed
        # Modify plate_model and set dimensions
        # Informing report
        desc_string = "STIFFENER"
        report.addLine(101, 10, desc_string, "")
        self.set_stiffener_dimensions(self, plate_model, host_profile)
        Plate.__init__(self, plate_model, report)

    def set_stiffener_dimensions(self, plate_model, host_profile):
        pro_b = host_profile.mat_db_profile.b
        pro_h = host_profile.mat_db_profile.h
        pro_tw = host_profile.mat_db_profile.tw
        pro_tf = host_profile.mat_db_profile.tf
        plate_model.width = pro_b / 2 - pro_tw
        plate_model.length = pro_h - 2 * pro_tf
        plate_model.save()
        self.pro_hw = Q(D(plate_model.length), 'mm')
        self.pro_tw = Q(D(host_profile.mat_db_profile.tw), 'mm')

    def check(self, Fp_Ed, report):
        """ check stiffener against point load. Using docs parameters """
        a = Q(D(1000), 'mm')  # 1 meter as standard (distance btw stiffeners)
        alpha = a / self.pro_hw
        if alpha < Q(D(np.sqrt(2))):
            I_st_min = (D(1.5) * self.pro_hw ** 3 * self.pro_tw ** 3) / a ** 2
        else:
            I_st_min = D(0.75) * self.pro_hw ** 3 * self.pro_tw ** 3 / a ** 2
        epsilon = np.sqrt(Q(D(275), 'MPa') / self.fy)
        I_st = D(1 / 12) * self.pro_tw ** 3 * 2 * 15 * epsilon * self.pro_tw +\
            D(1 / 12) * self.thickness * (2 * self.width + self.pro_tw) ** 3

        desc_string = "CHECKING STIFFENER"
        report.addLine(101, 30, desc_string, "")

        if I_st > I_st_min:
            desc_string = "Ultrastiff | OK"
            calc_string = "I_st = {} > I_st_min = {}".format(I_st, I_st_min)
            report.addLine(200, 30, desc_string, calc_string)
            return True
        else:
            desc_string = "Ultrastiff | FAIL"
            calc_string = "I_st = {} < I_st_min = {}".format(I_st, I_st_min)
            report.addLine(500, 30, desc_string, calc_string)
            return False


class BoltedStiffener(Stiffener, BoltedPlate):
    """ Bolted stiffener in a H Shape profile """

    #     | Fp_Ed = V2  (safety side)
    #     v
    # ==================
    # |       ||
    # |   +   ||
    # | 2 ^   ||
    # |   |   ||
    # |   |-> ||
    # |      1||
    # |   +   ||
    # |       ||
    # ==================

    def __init__(self, plate_model, host_profile, bolt_array, report):
        # Plate model and profile object, and bolt array object are passed
        desc_string = "BOLTED STIFFENER"
        report.addLine(101, 10, desc_string, "")
        if host_profile.mat_db_profile.is_any_reference:
            report.addLine(100, 10, "Stiffener for any profile",
                           "Setting a 5.5 mm profile web thickness")
            report.addLine(100, 10, "Stiffener for any profile",
                           "Setting dimensions from bolt settings")
            self.set_stiffener_dimensions_from_bolts(plate_model, bolt_array)
        else:
            Stiffener.set_stiffener_dimensions(self, plate_model, host_profile)
        BoltedPlate.__init__(self, plate_model, report)

    def set_stiffener_dimensions_from_bolts(self, plate_model, bolt_array):
        plate_model.width = plate_model.e1_main + \
            plate_model.e1_other + bolt_array.p1_sum().magnitude
        plate_model.length = plate_model.e2_main + \
            plate_model.e2_other + bolt_array.p2_sum().magnitude
        plate_model.save()
        self.pro_hw = Q(D(plate_model.length), 'mm')
        self.pro_tw = Q(D(5), 'mm')

    def check(self, bolt_array, uls_forces, report):
        desc_string = "CHECKING BOLTED STIFFENER"
        report.addLine(101, 30, desc_string, "")
        sf_ok = Stiffener.check(self, uls_forces.V2, report)
        bp_ok = BoltedPlate.check(self, bolt_array, uls_forces, report)
        return sf_ok and bp_ok
