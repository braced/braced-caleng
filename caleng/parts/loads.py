from caleng.parts.unit_registry import *
from caleng.parts.exceptions import CalengCrash
from caleng.parts import steel
from copy import copy
import numpy as np
from decimal import Decimal as D
import math


##################################################
# ____ SAP2000 EQUIVALENT FRAME FORCES SET _____ #
##################################################
class ForcesSet():
    def __init__(self, forces_model, report, pinted=False):
        # You can do this in 5 lines. But this is readable. Deal with it ¬¬,
        try:
            if isinstance(forces_model, dict):
                self.use = forces_model['use']
                if pinted:
                    self.P = forces_model['P']
                    self.V2 = forces_model['V2']
                    self.V3 = forces_model['V3']
                    self.M2 = forces_model['M2']
                    self.M3 = forces_model['M3']
                    self.T = forces_model['T']
                else:
                    self.P = Q(D(forces_model['P']), 'kN')
                    self.V2 = Q(D(forces_model['V2']), 'kN')
                    self.V3 = Q(D(forces_model['V3']), 'kN')
                    self.M2 = Q(D(forces_model['M2']), 'kN*m')
                    self.M3 = Q(D(forces_model['M3']), 'kN*m')
                    self.T = Q(D(forces_model['T']), 'kN*m')
            else:
                self.use = forces_model.use
                self.P = Q(forces_model.P, "kN")
                self.V2 = Q(forces_model.V2, "kN")
                self.V3 = Q(forces_model.V3, "kN")
                self.M2 = Q(forces_model.M2, "kN*m")
                self.M3 = Q(forces_model.M3, "kN*m")
                self.T = Q(forces_model.T, "kN*m")
            self.V = self.getV()
            self.M = self.getM()
            if report:
                self.reportSetup(report)
        except Exception as e:
            raise CalengCrash("Not a valid ForcesSet: " + str(e))

    def reportSetup(self, report):
        # Informing report

        report.addLine(101, 10, "FORCES SET", self.use)
        for name, force in [("P", self.P), ("V2", self.V2), ("V3", self.V3),
                            ("T", self.T), ("M2", self.M2), ("M3", self.M3)]:
            report.addLine(100, 10, "", name + " = " + str(force))

        desc_string = "Max Shear and Moment"
        calc_string = "Vmax = " + str(self.V) + " | Mmax = " + str(self.M)
        report.addLine(100, 10, desc_string, calc_string)

    def getV(self):
        return np.sqrt(self.V2 ** 2 + self.V3 ** 2)

    def getM(self):
        return np.sqrt(self.M2 ** 2 + self.M3 ** 2)

    def __str__(self):
        s1 = self.use + " | P = " + str(self.P) + " | V2 = " + \
            str(self.V2) + " | V3 = " + str(self.V3) + " | T = " + \
            str(self.T) + " | M2 = " + str(self.M2) + " | M3 = " + str(self.M3)

        return s1

    def rot90(self, axis, times, use, report):
        """ axis is an integer 1,2,3. Times is an integer representing
            the number of times to 90 degree rotate in the direction of
            the axis. The comboname is a string to represent this new
            forces set """
        forces = [self.P, self.V2, self.V3]
        moments = [self.T, self.M2, self.M3]

        for i in range(0, times):
            if axis == 1:
                forces = [forces[0], - forces[2], forces[1]]
                moments = [moments[0], - moments[2], moments[1]]
            elif axis == 2:
                forces = [forces[2], forces[1], - forces[0]]
                moments = [moments[2], moments[1], - moments[0]]
            elif axis == 3:
                forces = [- forces[1], forces[0], forces[2]]
                moments = [- moments[1], moments[0], moments[2]]
            else:
                forces = forces
                moments = moments
                raise CalengCrash("ForcesSet.rot90() needs an integer"
                                  " 1, 2 or 3.")

        if report:
            desc_string = "Generating rotated forces"
            report.addLine(100, 10, desc_string, use)

        # return rotated new object (all copied to avoid cagadas!)
        new_forces_set = copy(self)
        new_forces_set.P = copy(forces[0])
        new_forces_set.V2 = copy(forces[1])
        new_forces_set.V3 = copy(forces[2])
        new_forces_set.T = copy(moments[0])
        new_forces_set.M2 = copy(moments[1])
        new_forces_set.M3 = copy(moments[2])
        new_forces_set.V = new_forces_set.getV()
        new_forces_set.M = new_forces_set.getM()
        new_forces_set.use = use
        if report:
            new_forces_set.reportSetup(report)

        return new_forces_set

    def from_eccentricity(self, ec1, ec2, ec3, use, report):
        """ You give eccentricity in mm, axis 1, 2 and 3. Also a combo name
            and a optional report to be filled """

        forces = [self.P, self.V2, self.V3]
        moments = [
            self.T + ec2 * self.V3 - ec3 * self.V2,
            self.M2 + ec3 * self.P - ec1 * self.V3,
            self.M3 + ec1 * self.V2 - ec2 * self.P,
        ]

        if report:
            desc_string = "Generating eccentric forces"
            report.addLine(100, 10, desc_string, use)

        # return new forces object (all copied to avoid cagadas!)
        new_forces_set = copy(self)
        new_forces_set.P = copy(forces[0])
        new_forces_set.V2 = copy(forces[1])
        new_forces_set.V3 = copy(forces[2])
        new_forces_set.T = copy(moments[0])
        new_forces_set.M2 = copy(moments[1])
        new_forces_set.M3 = copy(moments[2])
        new_forces_set.V = new_forces_set.getV()
        new_forces_set.M = new_forces_set.getM()
        new_forces_set.use = use if use else self.use
        if report:
            new_forces_set.reportSetup(report)

        return new_forces_set

    def from_factor(self, factor, use, report):
        forces = [self.P * factor, self.V2 * factor, self.V3 * factor]
        moments = [self.T * factor, self.M2 * factor, self.M3 * factor]
        # return new forces object (all copied to avoid cagadas!)
        new_forces_set = copy(self)
        new_forces_set.P = copy(forces[0])
        new_forces_set.V2 = copy(forces[1])
        new_forces_set.V3 = copy(forces[2])
        new_forces_set.T = copy(moments[0])
        new_forces_set.M2 = copy(moments[1])
        new_forces_set.M3 = copy(moments[2])
        new_forces_set.V = new_forces_set.getV()
        new_forces_set.M = new_forces_set.getM()
        new_forces_set.use = use
        if report:
            new_forces_set.reportSetup(report)

        return new_forces_set

    def get_flange_and_web_tuple(self, distance_or_profile, report):
        """ This method returns a tuple. The first element will be a
            force object obtained from moment+axial related to the dist given.
            Just like V2 = P + M / distance (pair of forces in a profile) AND
            V3 = V2.
            The second elmnt is anoter force object. This object carrying only
            shear forces. Be careful using this, because it's purpose is ONLY
            intended for profile cover plates.

            This is applied assuming centroid of bolts in the same plane as
            profile section forces, virtually. Meaning that you may need to
            apply an eccentricity modification """

        if isinstance(distance_or_profile, steel.Profile):
            distance = Q(distance_or_profile.mat_db_profile.h, 'mm')
        else:
            distance = Q(distance_or_profile, 'mm')

        flange_force = copy(self)
        flange_force.P = Q(D(0), 'kN')
        flange_force.V2 = self.P / Q(D(2)) + self.M3 / distance
        flange_force.V3 = self.V3
        flange_force.T = self.M2 / Q(D(2))
        flange_force.M2 = Q(D(0), 'kN*m')
        flange_force.M3 = Q(D(0), 'kN*m')
        flange_force.V = flange_force.getV()
        flange_force.M = flange_force.getM()
        flange_force.use = self.use + " FLANGE"
        if report:
            flange_force.reportSetup(report)

        web_force = copy(self)
        web_force.P = Q(D(0), 'kN')
        web_force.V2 = Q(D(0), 'kN')
        web_force.V3 = self.V2
        web_force.T = Q(D(0), 'kN*m')
        web_force.M2 = Q(D(0), 'kN*m')
        web_force.M3 = Q(D(0), 'kN*m')
        web_force.V = web_force.getV()
        web_force.M = web_force.getM()
        web_force.use = self.use + " WEB"
        if report:
            web_force.reportSetup(report)

        return flange_force, web_force


# EXTRA BRACING FORCES (4 SIDES)
class ExtraBracingForces():

    def report_setup(self, report):

        # Main
        desc_string = "EXTRA BRACINGS"
        report.addLine(101, 10, desc_string, "")

        # Left
        if not self.left_bracing:
            calc_string = "---"
        else:
            calc_string = "SLS P = {} | ULS P = {}".format(
                self.left_sls, self.left_uls
            )
        report.addLine(100, 10, "Left Bracing", calc_string)

        # Right
        if not self.right_bracing:
            calc_string = "---"
        else:
            calc_string = "SLS P = {} | ULS P = {}".format(
                self.right_sls, self.right_uls
            )
        report.addLine(100, 10, "Right Bracing", calc_string)

        # Top
        if not self.top_bracing:
            calc_string = "---"
        else:
            calc_string = "SLS P = {} | ULS P = {}".format(
                self.top_sls, self.top_uls
            )
        report.addLine(100, 10, "Top Bracing", calc_string)

        # Bottom
        if not self.bottom_bracing:
            calc_string = "---"
        else:
            calc_string = "SLS P = {} | ULS P = {}".format(
                self.bottom_sls, self.bottom_uls
            )
        report.addLine(100, 10, "Bottom Bracing", calc_string)

    def __init__(self, model, report):
        try:
            if isinstance(model, dict):
                self.left_bracing = model['left_bracing']
                self.right_bracing = model['right_bracing']
                self.top_bracing = model['top_bracing']
                self.bottom_bracing = model['bottom_bracing']
                self.left_uls = Q(D(model['left_uls']), "kN")
                self.right_uls = Q(D(model['right_uls']), "kN")
                self.top_uls = Q(D(model['top_uls']), "kN")
                self.bottom_uls = Q(D(model['bottom_uls']), "kN")
                self.left_sls = Q(D(model['left_sls']), "kN")
                self.right_sls = Q(D(model['right_sls']), "kN")
                self.top_sls = Q(D(model['top_sls']), "kN")
                self.bottom_sls = Q(D(model['bottom_sls']), "kN")
                self.left_ang = Q(D(model['left_ang']), "degrees")
                self.right_ang = Q(D(model['right_ang']), "degrees")
                self.top_ang = Q(D(model['top_ang']), "degrees")
                self.bottom_ang = Q(D(model['bottom_ang']), "degrees")
            else:
                self.left_bracing = model.left_bracing
                self.right_bracing = model.right_bracing
                self.top_bracing = model.top_bracing
                self.bottom_bracing = model.bottom_bracing
                self.left_uls = Q(D(model.left_uls), "kN")
                self.right_uls = Q(D(model.right_uls), "kN")
                self.top_uls = Q(D(model.top_uls), "kN")
                self.bottom_uls = Q(D(model.bottom_uls), "kN")
                self.left_sls = Q(D(model.left_sls), "kN")
                self.right_sls = Q(D(model.right_sls), "kN")
                self.top_sls = Q(D(model.top_sls), "kN")
                self.bottom_sls = Q(D(model.bottom_sls), "kN")
                self.left_ang = Q(D(model.left_ang), "degrees")
                self.right_ang = Q(D(model.right_ang), "degrees")
                self.top_ang = Q(D(model.top_ang), "degrees")
                self.bottom_ang = Q(D(model.bottom_ang), "degrees")
            self.report_setup(report)
        except Exception as e:
            raise CalengCrash("Not a valid ExtraBracingForces: " + str(e))

    def sum_to_this_sls(self, forces, report):
        """ This method returns resultant forces, suming self.sls_forces
            with the given as positional argument """
        try:
            top_V2 = self.top_sls * D(math.sin(self.top_ang))
            top_P = self.top_sls * D(math.cos(self.top_ang))
            bottom_V2 = - self.bottom_sls * D(math.sin(self.bottom_ang))
            bottom_P = self.bottom_sls * D(math.cos(self.top_ang))
            left_V3 = - self.left_sls * D(math.sin(self.left_ang))
            left_P = self.left_sls * D(math.cos(self.left_ang))
            right_V3 = self.right_sls * D(math.sin(self.right_ang))
            right_P = self.right_sls * D(math.cos(self.right_ang))

            P = forces.P + top_P + bottom_P + left_P + right_P
            V2 = forces.V2 + top_V2 + bottom_V2
            V3 = forces.V3 + left_V3 + right_V3
            # Future development: eccentricity in bracings. Will be needed to
            # update M2, M3 and T. For now this is enough.
            M2 = forces.M2
            M3 = forces.M3
            T = forces.T
            forces_dict = {
                'use': "TOTAL SLS",
                'P': P,
                'V2': V2,
                'V3': V3,
                'M2': M2,
                'M3': M3,
                'T': T,
            }
            sls_forces = ForcesSet(forces_dict, report, pinted=True)
        except Exception as e:
            raise CalengCrash("Can't compute composed SLS resultant forces: " +
                              str(e))
        return sls_forces

    def sum_to_this_uls(self, forces, report):
        """ This method returns resultant forces, suming self.uls_forces
            with the given as positional argument """
        try:
            top_V2 = self.top_uls * D(math.sin(self.top_ang))
            top_P = self.top_uls * D(math.cos(self.top_ang))
            bottom_V2 = - self.bottom_uls * D(math.sin(self.bottom_ang))
            bottom_P = self.bottom_uls * D(math.cos(self.top_ang))
            left_V3 = - self.left_uls * D(math.sin(self.left_ang))
            left_P = self.left_uls * D(math.cos(self.left_ang))
            right_V3 = self.right_uls * D(math.sin(self.right_ang))
            right_P = self.right_uls * D(math.cos(self.right_ang))

            P = forces.P + top_P + bottom_P + left_P + right_P
            V2 = forces.V2 + top_V2 + bottom_V2
            V3 = forces.V3 + left_V3 + right_V3
            # Future development: eccentricity in bracings. Will be needed to
            # update M2, M3 and T. For now this is enough.
            M2 = forces.M2
            M3 = forces.M3
            T = forces.T
            forces_dict = {
                'use': "TOTAL ULS",
                'P': P,
                'V2': V2,
                'V3': V3,
                'M2': M2,
                'M3': M3,
                'T': T,
            }
            uls_forces = ForcesSet(forces_dict, report, pinted=True)
        except Exception as e:
            raise CalengCrash("Can't compute composed ULS resultant forces: " +
                              str(e))
        return uls_forces
