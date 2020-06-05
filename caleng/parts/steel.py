from decimal import Decimal as D
from caleng.parts.exceptions import CalengCrash
from caleng.parts.unit_registry import *
import numpy as np
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
from shapely import affinity
from caleng.parts import tstubs
from materials.models import SteelMaterialList, ProfileSectionList
from django.db.models import Q as Q_obj
# from caleng.parts.dev_plotter import plot

# HARDCODED DISTANCE TO PLATE FACTOR
M_DIST_TO_PLATE = 2


# Material properties solver (like a method for all classes)
def solve_from_steel_mat(self, mat, report=None):
    try:
        if isinstance(mat, str):
            team = report.calc.user.profile.team
            q_object = Q_obj(team=team) | Q_obj(braced_builtin=True)
            steelmat = SteelMaterialList.objects.filter(q_object).get(name=mat)
        else:
            steelmat = mat
        self.fu = Q(D(steelmat.fu), "MPa")
        self.fy = Q(D(steelmat.fy), "MPa")
        self.Ym0 = D(1)  # TO FIX MAYBE FROM DB I DONT KNOW
        self.Ym1 = D(1)  # TO FIX MAYBE FROM DB I DONT KNOW
        self.Ym2 = D(1.25)  # SAME
        self.E = Q(D(steelmat.E), "MPa")
        self.G = Q(D(steelmat.E), "MPa")
        self.material_name = steelmat.name
    except Exception as e:
        raise CalengCrash("Something happened when solving steel materials"
                          " from provided material object. Exc: " + str(e))


# Plate class
class Plate:
    def __init__(self, plate_model, report):
        if isinstance(plate_model, dict):
            solve_from_steel_mat(self, plate_model['material'], report)
        else:
            solve_from_steel_mat(self, plate_model.material)
        self.set_dimensions(plate_model)

        # Informing report
        desc_string = "PLATE DATA: " + str(self.material_name) +\
                      " " + str(self.use)
        calc_string = "t = {}".format(self.thickness)
        report.addLine(101, 10, desc_string, calc_string)
        calc_string = "length = {}".format(self.length)
        report.addLine(100, 10, "", calc_string)
        calc_string = "width = {}".format(self.width)
        report.addLine(100, 10, "", calc_string)

    def set_dimensions(self, plate_model):
        if isinstance(plate_model, dict):
            self.width = Q(D(plate_model['width']), 'mm')
            self.length = Q(D(plate_model['length']), 'mm')
            self.use = plate_model['use']
            self.thickness = Q(D(plate_model['thickness']), 'mm')
        else:
            self.width = Q(plate_model.width, 'mm')
            self.length = Q(plate_model.length, 'mm')
            self.use = plate_model.use
            self.thickness = Q(plate_model.thickness, 'mm')

    def get_polygon(self, report):
        """ Returns a shapely poligon centered on cdg """

        half_h = self.length.magnitude / 2
        half_b = self.width.magnitude / 2
        square = Polygon((
            (half_b, half_h), (half_b, -half_h),
            (-half_b, -half_h), (-half_b, half_h),
        ))
        return square


class WeldedPlate(Plate):
    def __init__(self, plate_model, report):
        Plate.__init__(self, plate_model, report)
        if isinstance(plate_model, dict):
            self.weld_length = Q(D(plate_model['weld_length']), 'mm')
            self.weld_throat = Q(D(plate_model['weld_throat']), 'mm')
            self.weld_number = Q(D(plate_model['weld_throat']), '')
        else:
            self.weld_length = Q(plate_model.weld_length, 'mm')
            self.weld_throat = Q(plate_model.weld_throat, 'mm')
            self.weld_number = Q(plate_model.weld_throat, '')

        # Informing report
        calc_string = "weld_length = " + str(self.weld_length) + \
                      " | weld_throat = " + str(self.weld_throat)
        report.addLine(100, 10, "", calc_string)

    def check(self, forces, report):
        desc_string = "WELDED PLATE: CHECKING WELDING"
        report.addLine(101, 30, desc_string, self.use)

        # EC3 PARAMETERS
        leff = self.weld_length
        a = self.weld_throat
        beta_w = Q(D(0.8))
        fvw_d = self.fu / np.sqrt(D(3)) / beta_w / self.Ym2
        report.addLine(100, 30, "", "leff = {}".format(leff))
        report.addLine(100, 30, "", "a = {}".format(a))
        report.addLine(100, 30, "", "beta_w = {}".format(beta_w))
        report.addLine(100, 30, "", "fvw_d = {}".format(fvw_d))

        # WELDING STRESSES
        Fw_Ed = abs(forces.V3) / self.weld_number
        Fw_Rd = (a * leff * fvw_d).to("kN")

        # CHECKING AND REPORTING
        if Fw_Ed <= Fw_Rd:
            desc_string = "Resistance of fillet weld | OK"
            calc_string = "Fw_Ed = {} < Fw_Rd = {}"\
                .format(Fw_Ed, Fw_Rd)
            report.addLine(200, 30, desc_string, calc_string)
            return True
        else:
            desc_string = "Resistance of fillet weld | FAIL"
            calc_string = "Fw_Ed = {} > Fw_Rd = {}"\
                .format(Fw_Ed, Fw_Rd)
            report.addLine(500, 30, desc_string, calc_string)
            return False


class BoltedPlate(Plate):
    def __init__(self, plate_model, report):
        Plate.__init__(self, plate_model, report)
        self.setup_e(plate_model, report)

    def setup_e(self, plate_model, report):
        """ This is part of the constructor, SPLITED to
            fix a diamond problem with WeldedBoltedPlate! """
        if isinstance(plate_model, dict):
            self.locked_edges = []  # edges not to be checked
            self.is_e1_sym = plate_model['is_e1_sym']
            self.is_e2_sym = plate_model['is_e2_sym']
            self.e1_main = Q(D(plate_model['e1_main']), "mm")
            self.e2_main = Q(D(plate_model['e2_main']), "mm")
            self.e1_other = Q(D(plate_model['e1_other']), "mm")
            self.e2_other = Q(D(plate_model['e2_other']), "mm")
            self.g1 = Q(D(plate_model.get('g1', 0)), 'mm')
            self.g2 = Q(D(plate_model.get('g2', 0)), 'mm')
        else:
            self.locked_edges = []  # edges not to be checked
            self.is_e1_sym = plate_model.is_e1_sym
            self.is_e2_sym = plate_model.is_e2_sym
            self.e1_main = Q(plate_model.e1_main, "mm")
            self.e2_main = Q(plate_model.e2_main, "mm")
            self.e1_other = Q(plate_model.e1_other, "mm")
            self.e2_other = Q(plate_model.e2_other, "mm")

        # Informing report
        if report:
            calc_string = "e1_main = " + str(self.e1_main) + \
                          " | e1_other = " + str(self.e1_other) + \
                          " | e2_main = " + str(self.e2_main)
            report.addLine(100, 10, "", calc_string)

    def check_dimensions(self, bolt_array, forces, report):
        # WARNING. TO DO. ASSUMING NORMAL HOLES!!
        # WE NEED TO TAKE INTO ACCOUNT EN 1090-2
        # ALSO ASSUMING STEEL EN 10025
        # ALSO ASSUMING P1 ALIGNED WITH LOAD. (MAY BE NOT)

        desc_string = "BOLTED PLATE: SOLVING SPACINGS AND EDGE DISTANCES"
        report.addLine(101, 30, desc_string, self.use)
        report.addLine(100, 30, "Info:", "Assuming EN 10025 Steel")

        d0 = bolt_array.bolt.d0
        EX_MIN = D(1.2) * d0
        EX_MAX = D(4) * self.thickness + Q(40, "mm")
        P1_MIN = D(2.2) * d0
        P2_MIN = D(2.4) * d0
        PX_MAX = min(D(14) * self.thickness, Q(200, "mm"))

        t1 = True
        t2 = True
        for p1 in bolt_array.p1:
            if not P1_MIN < p1 < PX_MAX:
                t1 = False
        for p2 in bolt_array.p2:
            if not P2_MIN < p2 < PX_MAX:
                t2 = False

        if t1 and t2:
            desc_string = "Bolt spacing check | OK"
            status_code = 200
        else:
            desc_string = "Bolt spacing check | FAIL"
            status_code = 500

        report.addLine(status_code, 30, desc_string,
                       "p1: {}".format(str(bolt_array.p1.magnitude)))
        report.addLine(100, 30, "",
                       "p2: {}".format(str(bolt_array.p2.magnitude)))
        report.addLine(100, 30, "",
                       "p1,min = {}".format(str(P1_MIN)))
        report.addLine(100, 30, "",
                       "p2,min = {}".format(str(P2_MIN)))
        report.addLine(100, 30, "",
                       "p1,2,max = {}".format(str(PX_MAX)))

        es = [self.e1_main, self.e1_other, self.e2_main, self.e2_other]
        # don't check locked edges
        if 'e1_main' in self.locked_edges:
            es.pop(0)
        if 'e1_other' in self.locked_edges:
            es.pop(1)
        if 'e2_main' in self.locked_edges:
            es.pop(2)
        if 'e2_other' in self.locked_edges:
            es.pop(3)

        te = True
        for e in es:
            if not EX_MIN < e < EX_MAX:
                te = False

        if te:
            desc_string = "Checking edge distance"
            calc_string = "OK"
            status_code = 200
        else:
            desc_string = "Checking edge distance"
            calc_string = "FAIL"
            status_code = 500
        report.addLine(status_code, 30, desc_string, calc_string)
        if 'e1_main' not in self.locked_edges:
            report.addLine(100, 30, "",
                           "e1 = {}".format(str(self.e1_main)))
        if 'e1_other' not in self.locked_edges:
            report.addLine(100, 30, "",
                           "e1* = {}".format(str(self.e1_other)))
        if 'e2_main' not in self.locked_edges:
            report.addLine(100, 30, "",
                           "e2 = {}".format(str(self.e2_main)))
        if 'e2_other' not in self.locked_edges:
            report.addLine(100, 30, "",
                           "e2* = {}".format(str(self.e1_other)))
        report.addLine(100, 30, "",
                       "e1,2,min = {}".format(str(EX_MIN)))
        report.addLine(100, 30, "",
                       "e1,2,max = {}".format(str(EX_MAX)))

        ret = t1 and t2 and te
        return ret

    def check_bearing(self, bolt_array, forces, report):
        # WARNING. TO DO. ASSUMING NORMAL HOLES!!
        # WE NNED TO TAKE INTO ACCOUNT EN 1090-2
        desc_string = "BOLTED PLATE: CHECKING BOLTS BEARING"
        report.addLine(101, 30, desc_string, self.use)
        report.addLine(100, 30, "Info", "Assuming normal holes")

        # Setting up parameters OJO! PARECE Q EL EC3 ESTA MAL. DICE
        # ALFA D DONDE DEBERIA DECIR K1. K1 HAY PARA DOS DIRECCIONES
        blt = bolt_array.bolt
        d0 = blt.d0
        if 'e1_main' in self.locked_edges:
            e1 = self.e1_other
        elif 'e1_other' in self.locked_edges:
            e1 = self.e1_main
        else:
            e1 = min(self.e1_main, self.e1_other)
        if 'e2_main' in self.locked_edges:
            e2 = self.e2_other
        elif 'e2_other' in self.locked_edges:
            e2 = self.e2_main
        else:
            e2 = min(self.e2_main, self.e2_other)
        p1_min = np.min(bolt_array.p1)
        alfa_d = min(
            (e1 / D(3.0) / d0),
            (p1_min / D(3.0) / d0 - D(0.25)),
        )
        alfa_b = min(D(1), (alfa_d * blt.fub / self.fu))
        k1 = min(
            (D(2.8) * e2 / d0 - D(1.7)),
            (D(1.4) * np.min(bolt_array.p2) / d0 - D(1.7)),
            (D(2.5)),
        )

        report.addLine(100, 30, "", "d0 = {}".format(d0))
        report.addLine(100, 30, "", "alfa_d = {}".format(alfa_d))
        report.addLine(100, 30, "", "alfa_b = {}".format(alfa_b))
        report.addLine(100, 30, "", "k1 = {}".format(k1))

        Fb_Rd = (k1 * alfa_b * self.fu * blt.diameter *
                 self.thickness / blt.Ym2).to("kN")
        Fv_Ed = bolt_array.getFv_Ed_max(forces, report)

        if Fv_Ed < Fb_Rd:
            desc_string = "Checking plate bearing | OK"
            calc_string = "Fv_Ed = {} < Fb_Rd = {}".format(Fv_Ed, Fb_Rd)
            report.addLine(200, 30, desc_string, calc_string)
            return True
        else:
            desc_string = "Checking plate bearing | OVERLOAD"
            calc_string = "Fv_Ed = {} > Fb_Rd = {}".format(Fv_Ed, Fb_Rd)
            report.addLine(500, 30, desc_string, calc_string)
            return False

    def check_block_tearing(self, ba, forces, report):
        im_safe = True
        desc_string = "BOLTED PLATE: CHECKING BLOCK TEARING"
        report.addLine(101, 30, desc_string, self.use)

        t = self.thickness
        fu = self.fu
        fy = self.fy
        Ym2 = ba.bolt.Ym2
        Ym0 = self.Ym0
        e1 = min(self.e1_main, self.e1_other)
        e2 = min(self.e2_main, self.e2_other)

        # #############
        # Direction 2 #
        # #############
        centered_2 = self.is_e2_sym and forces.T == 0
        Veff_Ed_V2 = abs(forces.V2)
        An2_tuples = []

        # We create a list with posible failures (area tuples)
        # Central block
        Ant = (ba.p1_sum() - ba.bolt.d0 * len(ba.p1)) * t
        Anv = (ba.p2_sum() + e1 - ba.bolt.d0 * (len(ba.p2) + D(0.5))) * t
        An2_tuples.append((Ant, Anv, "central block"))

        # Lateral block (1 column)
        if ba.n1 == 1:
            Ant = (e1 - ba.bolt.d0 * D(0.5)) * t
            # Anv is the same
            An2_tuples.append((Ant, Anv, "one side block"))

        # Lateral blocks (2 or more columns)
        else:
            psum = ba.p1_sum()
            d0rest = ba.bolt.d0 * len(ba.p1)
            Ant = (self.e1_main + self.e1_other + psum - d0rest) * t
            # Anv is the same
            An2_tuples.append((Ant, Anv, "two side blocks"))

        desc_string = "Block tearing. <2> direction"
        report.addLine(101, 30, desc_string, "")

        # Here we check every possible block tearing in dir 2
        for An_tuple in An2_tuples:
            Ant = An_tuple[0]
            Anv = An_tuple[1]
            title = An_tuple[2]
            tension = fu * Ant / Ym2
            shear = D(1 / np.sqrt(3)) * fy * Anv / Ym0
            ds_ok = "Block tearing | {} | OK".format(title)
            ds_fail = "Block tearing | {} | FAIL".format(title)
            ds_areas = "(Ant = {} | Anv = {})".format(Ant, Anv)

            # Load centered or not. Veff_1 or reduced Veff_2.
            if centered_2:
                Veff_1_Rd = (tension + shear).to("kN")
                if Veff_Ed_V2 < Veff_1_Rd:
                    calc_string = "Veff_Ed_V2 = {} < Veff_1_Rd = {}"\
                        .format(Veff_Ed_V2, Veff_1_Rd)
                    report.addLine(200, 30, ds_ok, ds_areas)
                    report.addLine(200, 30, "", calc_string)
                else:
                    calc_string = "Veff_Ed_V2 = {} > Veff_1_Rd = {}"\
                        .format(Veff_Ed_V2, Veff_1_Rd)
                    report.addLine(500, 30, ds_fail, ds_areas)
                    report.addLine(500, 30, "", calc_string)
                    im_safe = False
            else:
                Veff_2_Rd = (D(0.5) * tension + shear).to("kN")
                if Veff_Ed_V2 < Veff_2_Rd:
                    calc_string = "Veff_Ed_V2 = {} < Veff_2_Rd = {}"\
                        .format(Veff_Ed_V2, Veff_2_Rd)
                    report.addLine(200, 30, ds_ok, ds_areas)
                    report.addLine(200, 30, "", calc_string)
                else:
                    calc_string = "Veff_Ed_V2 = {} > Veff_2_Rd = {}"\
                        .format(Veff_Ed_V2, Veff_2_Rd)
                    report.addLine(500, 30, ds_fail, ds_areas)
                    report.addLine(500, 30, "", calc_string)
                    im_safe = False

        # #############
        # Direction 3 #
        # #############
        centered_3 = self.is_e1_sym and forces.T == 0
        Veff_Ed_V3 = abs(forces.V3)
        An3_tuples = []

        # We create a list with posible failures (area tuples)
        # Central block
        Ant = (ba.p2_sum() - ba.bolt.d0 * len(ba.p2)) * t
        Anv = (ba.p1_sum() + e2 - ba.bolt.d0 * (len(ba.p1) + D(0.5))) * t
        An3_tuples.append((Ant, Anv, "central block"))

        # Lateral block (1 column)
        if ba.n2 == 1:
            Ant = (e2 - ba.bolt.d0 * D(0.5)) * t
            # Anv is the same
            An3_tuples.append((Ant, Anv, "one side block"))

        # Lateral blocks (2 or more columns)
        else:
            psum = ba.p2_sum()
            d0rest = ba.bolt.d0 * len(ba.p2)
            Ant = (self.e2_main + self.e2_other + psum - d0rest) * t
            # Anv is the same
            An3_tuples.append((Ant, Anv, "two side blocks"))

        desc_string = "Block tearing. <3> direction"
        report.addLine(101, 30, desc_string, "")

        # Checking every block in dir 3
        for An_tuple in An3_tuples:
            Ant = An_tuple[0]
            Anv = An_tuple[1]
            title = An_tuple[2]
            tension = fu * Ant / Ym2
            shear = D(1 / np.sqrt(3)) * fy * Anv / Ym0
            ds_ok = "Block tearing | {} | OK".format(title)
            ds_fail = "Block tearing | {} | FAIL".format(title)
            ds_areas = "(Ant = {} | Anv = {})".format(Ant, Anv)
            # Load centered or not. Veff_1 or reduced Veff_2.
            if centered_3:
                Veff_1_Rd = (tension + shear).to("kN")
                if Veff_Ed_V3 < Veff_1_Rd:
                    calc_string = "Veff_Ed_V3 = {} < Veff_1_Rd = {}"\
                        .format(Veff_Ed_V3, Veff_1_Rd)
                    report.addLine(200, 30, ds_ok, ds_areas)
                    report.addLine(200, 30, "", calc_string)
                else:
                    calc_string = "Veff_Ed_V3 = {} > Veff_1_Rd = {}"\
                        .format(Veff_Ed_V3, Veff_1_Rd)
                    report.addLine(500, 30, ds_fail, ds_areas)
                    report.addLine(500, 30, "", calc_string)
                    im_safe = False
            else:
                Veff_2_Rd = (D(0.5) * tension + shear).to("kN")
                if Veff_Ed_V3 < Veff_2_Rd:
                    calc_string = "Veff_Ed_V3 = {} < Veff_2_Rd = {}"\
                        .format(Veff_Ed_V3, Veff_2_Rd)
                    report.addLine(200, 30, ds_ok, ds_areas)
                    report.addLine(200, 30, "", calc_string)
                else:
                    calc_string = "Veff_Ed_V3 = {} > Veff_2_Rd = {}"\
                        .format(Veff_Ed_V3, Veff_2_Rd)
                    report.addLine(500, 30, ds_fail, ds_areas)
                    report.addLine(500, 30, "", calc_string)
                    im_safe = False

        return im_safe

    def check_t_stubs(self, bolt_array, forces, profile, report):
        desc_string = "BOLTED PLATE: CHECKING T-STUBS"
        report.addLine(101, 30, desc_string, self.use)
        tstub_list = tstubs.solve_from_polygons(self, profile,
                                                bolt_array, report)

        if len(tstub_list) < 1:
            report.addLine(200, 30, "No T-Stubs to solve", "")
            return True
        else:
            desc_string = "INFO: solving as a end-plate"\
                          " T-Stub according to EC3 6.2.6.5"
            report.addLine(100, 30, desc_string, "")
        Ft_Ed = bolt_array.getFt_Ed_max(forces, report)
        Ft_Rd = bolt_array.bolt.getFt_Rd(report)
        # Returning
        for ts in tstub_list:
            if not ts.check(Ft_Ed, Ft_Rd, report):
                return False
        return True

    def check_t_stubs_legacy(
        self, bolt_array, forces, profile, position, report
    ):
        desc_string = "BOLTED PLATE: CHECKING T-STUBS"
        report.addLine(101, 30, desc_string, self.use)
        tstub_list = tstubs.solve_from_polygons_legacy(
            self, profile, position, bolt_array, report)

        if len(tstub_list) < 1:
            report.addLine(200, 30, "No T-Stubs to solve", "")
            return True
        else:
            desc_string = "INFO: solving as a end-plate"\
                          " T-Stub according to EC3 6.2.6.5"
            report.addLine(100, 30, desc_string, "")
        Ft_Ed = bolt_array.getFt_Ed_max(forces, report)
        Ft_Rd = bolt_array.bolt.getFt_Rd(report)
        # Returning
        for ts in tstub_list:
            if not ts.check(Ft_Ed, Ft_Rd, report):
                return False
        return True

    def check_punching(self, bolt_array, forces, report):
        # WARNING. TO DO. ASSUMING NORMAL HOLES!!
        # WE NNED TO TAKE INTO ACCOUNT EN 1090-2
        desc_string = "BOLTED PLATE: CHECKING HOLES PUNCHING SHEAR"
        report.addLine(101, 30, desc_string, self.use)
        report.addLine(100, 30, "Info", "Assuming normal holes")

        dm = bolt_array.bolt.dm
        tp = self.thickness
        pi = Q(D(np.pi))
        report.addLine(100, 30, "", "dm = {}".format(dm))
        Bp_Rd = (Q(D(0.6)) * pi * dm * tp * self.fu / self.Ym2).to("kN")
        Ft_Ed = bolt_array.getFt_Ed_max(forces, report)

        if Ft_Ed < Bp_Rd:
            desc_string = "Checking plate bearing | OK"
            calc_string = "Ft_Ed = {} < Bp_Rd = {}".format(Ft_Ed, Bp_Rd)
            report.addLine(200, 30, desc_string, calc_string)
            return True
        else:
            desc_string = "Checking plate bearing | OVERLOAD"
            calc_string = "Ft_Ed = {} > Bp_Rd = {}".format(Ft_Ed, Bp_Rd)
            report.addLine(500, 30, desc_string, calc_string)
            return False

    def check_collisions(self, bolt_array, profile, report):
        """ This method checks for collissions between the profile and
            the bolts. Must be called independently from check(). Why?
            I think its better not to pass extra args to check(). If you
            need it you call it from the solver. It's easy. """

        desc_string = "BOLTED PLATE: CHECKING BOLT COLLISIONS"
        report.addLine(101, 30, desc_string, self.use)

        # Start creating a flag. Below we loop over bolts and kill it
        im_safe = True

        # HARDCODED!! max distance to plate "m". Must be configurable by user!
        m_max = M_DIST_TO_PLATE * bolt_array.bolt.diameter
        desc_string = "Max distance to plate/profile"
        report.addLine(100, 30, desc_string, "m = " + str(m_max))

        # Get the positioned protected polygon
        rotated_pol = profile.get_protected_polygon(m_max, report)

        # This rotation is done into the profile get_polygon method (NOW)
        # center_point = Point(0, 0)
        # rotated_pol = affinity.rotate(
        #     protected_pol,
        #     float(profile.rotation.magnitude),
        #     origin=center_point)
        positioned_protected_pol = affinity.translate(
            rotated_pol,
            xoff=-float(self.g1.magnitude),
            yoff=float(self.g2.magnitude))
        # Watch out the last translation. Only g1 is negative. It works...

        bolt_matrix = bolt_array.get_bolt_matrix()

        for b in bolt_matrix:
            b_point = Point(b[3].magnitude, b[4].magnitude)  # x1 and x2
            dclash = Q(D(b_point.distance(positioned_protected_pol)), "mm")
            if positioned_protected_pol.contains(b_point):
                im_safe = False
                calc_string = "Clash!"
            else:
                calc_string = "OK"
            desc_string = "Bolt {} | {}: dclash = {}"\
                .format(b[0], b_point, dclash)
            report.addLine(100, 30, desc_string, calc_string)

        if im_safe:
            report.addLine(200, 30, "Bolt and plate clashing | OK", "")
        else:
            report.addLine(500, 30, "Bolt and plate clashing | FAIL", "")
        return im_safe

    def check_collisions_legacy(self, bolt_array, profile, position, report):
        """ This method checks for collissions between the profile and
            the bolts. Must be called independently from check(). Why?
            I think its better not to pass extra args to check(). If you
            need it you call it from the solver. It's easy. """

        desc_string = "BOLTED PLATE: CHECKING BOLT COLLISIONS"
        report.addLine(101, 30, desc_string, self.use)

        # Start creating a flag. Below we loop over bolts and kill it
        im_safe = True

        # HARDCODED!! max distance to plate "m". Must be configurable by user!
        m_max = M_DIST_TO_PLATE * bolt_array.bolt.diameter
        desc_string = "Max distance to plate/profile"
        report.addLine(100, 30, desc_string, "m = " + str(m_max))

        # Get the positioned protected polygon
        protected_pol = profile.get_protected_polygon(m_max, report)
        center_point = Point(0, 0)
        rotated_pol = affinity.rotate(
            protected_pol,
            float(position.rotation.magnitude),
            origin=center_point)
        positioned_protected_pol = affinity.translate(
            rotated_pol,
            xoff=position.g1.magnitude,
            yoff=position.g2.magnitude)

        bolt_matrix = bolt_array.get_bolt_matrix()

        for b in bolt_matrix:
            b_point = Point(b[3].magnitude, b[4].magnitude)  # x1 and x2
            dclash = Q(D(b_point.distance(positioned_protected_pol)), "mm")
            if positioned_protected_pol.contains(b_point):
                im_safe = False
                calc_string = "Clash!"
            else:
                calc_string = "OK"
            desc_string = "Bolt {}: Margin to clash: dclash = {}"\
                .format(b[0], dclash)
            report.addLine(100, 30, desc_string, calc_string)

        if im_safe:
            report.addLine(200, 30, "Bolt and plate clashing | OK", "")
        else:
            report.addLine(500, 30, "Bolt and plate clashing | FAIL", "")
        return im_safe

    def check(self, bolt_array, forces, report):
        """ This method checks the typical plate failures. Be carefull,
            specific checks like check_collisions_legacy and check_t_stub
            must be checked if needed """

        dim = self.check_dimensions(bolt_array, forces, report)
        if forces.V.magnitude != 0 or forces.T.magnitude != 0:
            bea = self.check_bearing(bolt_array, forces, report)
            blo = self.check_block_tearing(bolt_array, forces, report)
        else:
            bea = True
            blo = True

        if forces.P.magnitude != 0 or forces.M.magnitude != 0:
            pun = self.check_punching(bolt_array, forces, report)
        else:
            pun = True
        return all([dim, bea, blo, pun])


class WeldedBoltedPlate(WeldedPlate, BoltedPlate):

    # THIS CONSTRUCTOR GETS THE WELDED PLATE AND e_dict
    # e_dict may be either A DICT or A MODEL
    def __init__(self, plate, report, e_dict="no_dict"):
        WeldedPlate.__init__(self, plate, report)
        if e_dict == "no_dict":
            BoltedPlate.setup_e(self, plate, report)
        else:
            self.setup_e_dict(e_dict, report)

    def setup_e_dict(self, e_dict, report):
        self.e1_main = e_dict['e1_main']
        self.e1_other = e_dict['e1_other']
        self.e2_main = e_dict['e2_main']
        self.e2_other = e_dict['e2_other']
        self.is_e1_sym = self.e1_main.magnitude == self.e1_other.magnitude
        self.is_e2_sym = self.e2_main.magnitude == self.e2_other.magnitude

        # Informing report
        calc_string = "e1_main = " + str(self.e1_main) + \
                      " | e1_other = " + str(self.e1_other) + \
                      " | e2_main = " + str(self.e2_main)
        report.addLine(100, 10, "", calc_string)

    def check(self, bolt_array, uls_forces, report):
        a = BoltedPlate.check(self, bolt_array, uls_forces, report)
        b = WeldedPlate.check(self, uls_forces, report)
        return a & b


# Dummy ultrastiff bolted plate. Only want several methods
class DummyBoltedPlate(BoltedPlate):

    # Overriding __init__ with  less stuff.
    def __init__(self, plate_model, report):
        if isinstance(plate_model, dict):
            self.width = Q(D(plate_model['width']), 'mm')
            self.length = Q(D(plate_model['length']), 'mm')
        else:
            self.width = Q(plate_model.width, 'mm')
            self.length = Q(plate_model.length, 'mm')
        self.setup_e(plate_model, report)

    def check(self):
        """ Nothing to do. This class doesnt need to check anything """
        return True


# ###################
# ## PROFILES #######
# ###################
class Profile:
    def __init__(self, profile_model, report):
        self.bolted_flange = False
        self.bolted_web = False

        if isinstance(profile_model, dict):
            solve_from_steel_mat(self, profile_model['material'], report)
            self.profile_type = profile_model['profile_type']
            self.use = profile_model['use']
            self.name = profile_model['profile']
            self.rotation = Q(D(profile_model['rotation']), "degrees")
            team = report.calc.user.profile.team
            q_object = Q_obj(team=team) | Q_obj(braced_builtin=True)
            self.mat_db_profile = ProfileSectionList.get_qs_by_q_obj(
                self.profile_type, q_object
            ).get(name=self.name)
        else:
            self.rotation = Q(D(0), "degrees")
            solve_from_steel_mat(self, profile_model.material)
            self.profile_type = profile_model.profile_type
            self.section_list_pk = profile_model.section_list_pk
            self.use = profile_model.use
            self.name = profile_model.profile
            self.mat_db_profile = profile_model.get_mat_db_object()

        # Informing report
        desc_string = "PROFILE DATA: " + str(self.profile_type) + " " +\
                      str(self.name) + " " + str(self.use)
        report.addLine(101, 10, desc_string, "")

    def get_polygon(self, report):
        """ Returns a "shapely" Polygon created from boundary
            points clockwise starting as minutes start in a clock (00:00) """

        if self.profile_type == "PIP":
            half_diameter = self.mat_db_profile.d / 2
            zero_point = Point(0, 0)
            polygon = zero_point.buffer(half_diameter)

        elif self.profile_type == "TUB":
            half_h = self.mat_db_profile.h / 2
            half_b = self.mat_db_profile.b / 2
            polygon = Polygon((
                (half_b, half_h), (half_b, -half_h),
                (-half_b, -half_h), (-half_b, half_h),
            ))

        elif self.profile_type == "H":
            half_h = self.mat_db_profile.h / 2
            half_b = self.mat_db_profile.b / 2
            half_tw = self.mat_db_profile.tw / 2
            tf = self.mat_db_profile.tf
            polygon = Polygon((
                # Top flange right
                (half_b, half_h), (half_b, half_h - tf),
                # Web right
                (half_tw, half_h - tf), (half_tw, -half_h + tf),
                # Bottom flange all
                (half_b, -half_h + tf), (half_b, -half_h),
                (-half_b, -half_h), (-half_b, -half_h + tf),
                # Web left
                (-half_tw, -half_h + tf), (-half_tw, half_h - tf),
                # Top flange left
                (-half_b, half_h - tf), (-half_b, half_h),
            ))

        elif self.profile_type == "U":
            half_h = self.mat_db_profile.h / 2
            half_b = self.mat_db_profile.b / 2
            tw = self.mat_db_profile.tw
            tf = self.mat_db_profile.tf
            polygon = Polygon((
                # Top flange
                (half_b, half_h), (half_b, half_h - tf),
                # Web right
                (- half_b + tw, half_h - tf), (- half_b + tw, -half_h + tf),
                # Bottom flange
                (half_b, -half_h + tf), (half_b, -half_h),
                # Web left
                (- half_b, -half_h), (- half_b, half_h),
            ))

        elif self.profile_type == "L":
            half_h = self.mat_db_profile.h / 2
            half_b = self.mat_db_profile.b / 2
            t = self.mat_db_profile.t
            polygon = Polygon((
                # h flange
                (half_b, t - half_h),
                (half_b, - half_h),
                (- half_b, - half_h),
                # v flange
                (- half_b, half_h),
                (t - half_b, half_h),
                (t - half_b, t - half_h),
            ))
        else:
            polygon = None

        # IF NEW APP
        if self.rotation:
            center_point = Point(0, 0)
            return affinity.rotate(
                polygon,
                -float(self.rotation.magnitude),
                origin=center_point)

        # TO DEPRECATE
        else:
            return polygon

    def get_protected_polygon(self, m, report):
        """ Returns a "shapely" Polygon. It is the restricted
            zone for a bolt. Its computed with a given m distance betweeen
            bolt axis and plate face. Polygons are created from boundary
            points clockwise starting as minutes start in a clock (00:00) """

        polygon = self.get_polygon(report)
        if polygon is not None:
            buffered_polygon = polygon.buffer(m.magnitude)
            return buffered_polygon
        else:
            return None

    def bolt_the_flange(self, ba, bp, report):
        if self.profile_type == "H":
            pass
        elif self.profile_type == "U":
            pass
        else:
            raise CalengCrash("UNIMPLEMENTED BOLTED PROFILE "
                              "DIFFERENT FROM H OR U")
        self.bolted_flange = BoltedFlange(self, ba, bp, report)

    def bolt_the_web(self, ba, bp, report):
        self.bolted_web = BoltedWeb(self, ba, bp, report)

    def check(self, report):
        return True


class SectionPosition:
    def __init__(self, section_position_model, report):
        self.bolt_array = None
        self.profile = None
        self.rotation = Q(D(section_position_model.rotation), "degrees")
        self.g1 = Q(D(section_position_model.g1), "mm")
        self.g2 = Q(D(section_position_model.g2), "mm")
        if section_position_model.flip_gs:
            self.g1 = -self.g1
            self.g2 = -self.g2
            print("FLIP")
        else:
            print("FLOP")

    @classmethod
    def from_g1(self, g1, report):
        """ Constructor from plate s displacement """
        self.bolt_array = None
        self.profile = None
        self.rotation = Q(D(0), "degrees")
        self.g1 = Q(D(g1), "mm")
        self.g2 = Q(D(0), "mm")
        return self

    @classmethod
    def centered(self):
        """ Empty constructor """
        self.bolt_array = None
        self.profile = None
        self.rotation = Q(D(0), "degrees")
        self.g1 = Q(D(0), "mm")
        self.g2 = Q(D(0), "mm")
        return self


class BoltedClipAngle(BoltedPlate):
    """ Bolted Clip Angle. Initially developed to solve the S006 sheet
        but may fit more pureportoses. Only allowed L profiles """

    def __init__(self, profile, dummy_bolted_plate, report):
        if profile.profile_type != "L":
            raise CalengCrash("Clip Angle must be a L Shaped Profile")
        self.profile_db_object = profile.get_mat_db_object()
        self.use = profile.use
        self.thickness = Q(self.profile_db_object.t, 'mm')
        self.locked_edges = []
        self.width = Q(self.profile_db_object.b, 'mm')
        self.length = Q(self.profile_db_object.h, 'mm')
        if self.width != self.length:
            # To avoid this crash, a lot of shit must be reviewed.
            # S006 soolver sets ec1 = ec3.
            # A second bolt array must be added... fuck a lot of things.
            raise CalengCrash("Only simmetric L Clip Angle alowed")
        solve_from_steel_mat(self, profile.material)
        self.setup_e(dummy_bolted_plate, report)
        if report:
            self.reportSetup(report)

    def reportSetup(self, report):
        """ Informing report """
        desc_string = "CLIP ANGLE DATA: " + str(self.profile_db_object) +\
                      " " + str(self.use)
        calc_string = "t = {}".format(self.thickness)
        report.addLine(101, 10, desc_string, calc_string)
        calc_string = "length = {}".format(self.length)
        report.addLine(100, 10, "", calc_string)
        calc_string = "width = {}".format(self.width)
        report.addLine(100, 10, "", calc_string)

    def check(self, bolt_array, forces, report):
        """ This method checks the L Profile as a plate. It fills some
            arguments needed, and then checks through BoltedPlate.check()
            Forces will be duplicated in order to check two connections.
            Provided forces must be the FRONT CONNECTION EQUIVALENT
            (Usually they are directly the connected beam forces) """

        self.heigh = bolt_array.p2_sum() +\
            self.e2_main + self.e2_other
        desc_string = "CLIP ANGLE: CHECKING AS A BOLTED PLATE"
        calc_string = "{} | heigh = {}".format(self.use, self.heigh)
        report.addLine(101, 30, desc_string, calc_string)
        return BoltedPlate.check(self, bolt_array, forces, report)

    def dist_bolts_to_plate(self, bolt_array):
        """ Returns distance from bolt center of gravity to the other
            flange. Usefull to get a eccentricity. Given a bolt_array """

        return self.width - self.e1_main - bolt_array.p1_sum() / 2


class BoltedClipAnglePair(BoltedClipAngle):
    """ Pair case of inherited class """

    def __init__(self, profile, dummy_bolted_plate, report):
        # REPORT SETUP AND CREATE A BOLTEDCLIPANGLE
        BoltedClipAngle.__init__(self, profile, dummy_bolted_plate, None)
        self.use += " | x2 (Angle Pair)"
        if report:
            self.reportSetup(report)

    def check(self, bolt_array, forces, report):
        """ FRONT CONNECTION EQUIVALENT FORCES MUST BE PROVIDED.
            Forces are duplicated to check 2 connections. front
            and lateral ones """

        return BoltedClipAngle.check(self, bolt_array, forces, report)


class BoltedWeb(BoltedPlate):
    """
    Bolted profile web. Only allowed H,L,U profiles
    It's assumed that e1p1e1* runs with the profile axis.
    and e2p2e2* runs with the profile section.

    """

    def __init__(self, beam_profile, bolt_array, plate, report):
        self.fu = beam_profile.fu
        self.fy = beam_profile.fy
        self.Ym0 = beam_profile.Ym0
        self.Ym1 = beam_profile.Ym1
        self.Ym2 = beam_profile.Ym2
        self.E = beam_profile.E
        self.G = beam_profile.G
        self.material_name = beam_profile.material_name
        self.db_profile = beam_profile.mat_db_profile
        self.use = beam_profile.use + " | bolted web"
        self.bolt_array = bolt_array
        self.thickness = Q(self.db_profile.tw, 'mm')
        self.locked_edges = []
        if isinstance(plate, Plate):
            self.heigh = bolt_array.p2_sum() + plate.e2_main + plate.e2_other
            self.width = Q(D(self.db_profile.h), 'mm')
            self.e1_main = plate.e1_main
            self.e1_other = plate.e1_other
            self.is_e1_sym = True
            self.e2_main = plate.e2_main
            self.e2_other = plate.e2_other
            self.is_e2_sym = plate.is_e2_sym
        else:
            self.heigh = bolt_array.p2_sum() +\
                Q(D(plate['e2_main'] + plate['e2_other']), 'mm')
            self.width = bolt_array.p1_sum() +\
                Q(D(plate['e1_main']), 'mm') + Q(D(plate['e1_other']), 'mm')
            # e data
            self.setup_e(plate, report)
        self.length = self.heigh

        # Informing report
        desc_string = "BOLTED WEB DATA: " + str(self.material_name) +\
                      " " + str(self.use)
        calc_string = "t = {}".format(self.thickness)
        report.addLine(101, 10, desc_string, calc_string)
        calc_string = "length = {}".format(self.length)
        report.addLine(100, 10, "", calc_string)
        calc_string = "width = {}".format(self.width)
        report.addLine(100, 10, "", calc_string)

    def check(self, forces, report):
        """ This method checks the typical plate failures. Be carefull,
            specific checks like check_collisions_legacy and check_t_stub
            must be checked if needed """

        return (
            BoltedPlate.check(self, self.bolt_array, forces, report) &
            self.check_flange_colision(report)
        )

    def check_flange_colision(self, report):
        """ Checking if bolt is not too near to flanges """

        desc_string = "BOLTED WEB: CHECKING BOLT CLASHES"
        report.addLine(101, 30, desc_string, self.use)

        min_e1 = Q(D(self.db_profile.tf), 'mm') +\
            M_DIST_TO_PLATE * self.bolt_array.bolt.diameter

        desc_string = "Minimum distance to a flange or plate"
        report.addLine(100, 30, desc_string, "m = " + str(min_e1))

        if self.e1_main < min_e1:
            desc_string = "Checking clashes | CLASH"
            calc_string = "e1 = {} < d*M+tf = {}".format(self.e1_main, min_e1)
            report.addLine(500, 30, desc_string, calc_string)
            return False
        else:
            desc_string = "Checking clashes | OK"
            calc_string = "e1 = {} >= d*M+tf = {}".format(self.e1_main, min_e1)
            report.addLine(200, 30, desc_string, calc_string)
            return True


class BoltedFlange(BoltedPlate):
    def __init__(self, prof, ba, bp, report):
        self.fu = prof.fu
        self.fy = prof.fy
        self.Ym0 = prof.Ym0
        self.Ym1 = prof.Ym1
        self.Ym2 = prof.Ym2
        self.E = prof.E
        self.G = prof.G
        self.material_name = prof.material_name
        self.db_profile = prof.mat_db_profile
        self.profile = prof
        self.bolt_array = ba
        self.thickness = Q(self.db_profile.tf, 'mm')
        self.locked_edges = []
        self.heigh = ba.p2_sum() + bp.e2_main + bp.e2_other
        self.length = self.heigh
        self.width = Q(D(prof.mat_db_profile.b), 'mm')
        self.e1_main = (self.width - ba.p1_sum()) / 2
        self.e1_other = (self.width - ba.p1_sum()) / 2
        self.is_e1_sym = True
        if prof.profile_type == "H":
            self.use = prof.use + " | bolted H flange"
        elif prof.profile_type == "U":
            self.use = prof.use + " | bolted U flange"
        self.e2_main = bp.e2_main
        self.e2_other = bp.e2_other
        self.is_e2_sym = bp.is_e2_sym

        # Informing report
        desc_string = "BOLTED FLANGE DATA: " + str(self.material_name) +\
                      " " + str(self.use)
        calc_string = "t = {}".format(self.thickness)
        report.addLine(101, 10, desc_string, calc_string)
        calc_string = "length* = {}".format(self.length)
        report.addLine(100, 10, "", calc_string)
        calc_string = "width = {}".format(self.width)
        report.addLine(100, 10, "", calc_string)

    def check(self, forces, report):
        """ This method checks the typical plate failures. Be carefull,
            specific checks like check_collisions_legacy and check_t_stub
            must be checked if needed """

        return (
            BoltedPlate.check(self, self.bolt_array, forces, report) &
            self.check_web_colision(report)
        )

    def check_web_colision(self, report):
        """ Checking if bolt is not too near to flanges """

        if self.profile.profile_type == "H":
            desc_string = "BOLTED H FLANGE: CHECKING BOLT CLASHES"
        if self.profile.profile_type == "U":
            desc_string = "BOLTED U FLANGE: CHECKING BOLT CLASHES"
        report.addLine(101, 30, desc_string, self.use)

        m_min = M_DIST_TO_PLATE * self.bolt_array.bolt.diameter

        desc_string = "Minimum distance to a web or plate"
        report.addLine(100, 30, desc_string, "m = " + str(m_min))

        if self.profile.profile_type == "H":
            m_serie = []
            demiwidth = (self.width + Q(D(self.db_profile.tw), 'mm')) / 2
            p_sum = Q(D(0), 'mm')
            m_serie.append(demiwidth - self.e1_main)
            for p in self.bolt_array.p1:
                p_sum += p
                ld = self.e1_main + p_sum
                rd = self.width - ld
                m_pair = [demiwidth - ld, demiwidth - rd]
                m = min([m for m in m_pair if m > Q(D(0), 'mm')])
                m_serie.append(m)
            m = min(m_serie)
            if m < m_min:
                desc_string = "Checking clash to web | CLASH"
                calc_string = "m = {} < d*M = {}".format(m, m_min)
                report.addLine(500, 30, desc_string, calc_string)
                return False
            else:
                desc_string = "Checking clash to web | OK"
                calc_string = "m = {} > d*M = {}".format(m, m_min)
                report.addLine(200, 30, desc_string, calc_string)
                return True

        if self.profile.profile_type == "U":
            m = self.e1_main - Q(D(self.db_profile.tw), 'mm')
            if m < m_min:
                desc_string = "Checking clash to web | CLASH"
                calc_string = "e1 - tw = {} < d*M = {}".format(m, m_min)
                report.addLine(500, 30, desc_string, calc_string)
                return False
            else:
                desc_string = "Checking clash to web | OK"
                calc_string = "e1 - tw = {} > d*M = {}".format(m, m_min)
                report.addLine(200, 30, desc_string, calc_string)
                return True
