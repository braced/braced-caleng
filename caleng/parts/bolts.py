import numpy as np
from decimal import Decimal as D
from caleng.parts.exceptions import CalengCrash
from caleng.parts.unit_registry import *
from materials.models import BoltMaterialList
from materials.models import BoltSizeList

# MAIN MODULE FOR BOLTS CLASSES #


##################################################
# _____  BOLT CLASSES. (can be imperial)  ______ #
##################################################
class EuroBolt:
    def __init__(self, bolt_model, report):
        # TO DO: Include try-crash with django exception internal
        if isinstance(bolt_model, dict):
            # This case when JSON object passed
            self.bolt_holes = bolt_model['bolt_holes']
            self.solveFromGrade(bolt_model['bolt_grade'])
            self.solveFromSize(bolt_model['bolt_size'])
            self.n = bolt_model['n']  # cutting planes
            self.conn_cat = bolt_model['conn_cat']
            self.surface_class = bolt_model['surface_class']
        else:
            # This is provisional case with django models
            self.bolt_holes = bolt_model.bolt_holes
            self.solveFromGrade(bolt_model.bolt_grade)
            self.solveFromSize(bolt_model.bolt_size)
            self.n = bolt_model.n  # cutting planes
            self.conn_cat = bolt_model.conn_cat
            self.surface_class = bolt_model.surface_class

        self.Ft_Rd_hash = None
        self.Ft_Rd = None

        # Preloading parameters
        self.solvePreload()

        # Plates cutting at threat or shaft??
        self.shaft_cut = False

        # Informing report
        desc_string = "BOLT DATA: " + str(self.size_name) + " " +\
                      str(self.grade_name)
        report.addLine(101, 10, desc_string, "")

    # SOLVING SLIP RESISTANT STUFF
    def solvePreload(self):

        # preloading and elu slipping booleans
        if self.conn_cat in ['C', 'E']:
            self.uls_slip = True
            self.preloaded = True
        elif self.conn_cat == 'B':
            self.uls_slip = False
            self.preloaded = True
        else:
            self.uls_slip = False
            self.preloaded = False

        # Preloading force
        self.Fp_C = (D(0.7) * self.fub * self.As if self.preloaded
                     else Q(D(0), "kN")).to("kN")

        # Slipping factor
        self.Ym3 = D(1.25) if self.uls_slip else D(1.10)

        mus = {"A": D(0.5), "B": D(0.4), "C": D(0.3), "D": D(0.2)}
        self.mu = Q(mus[self.surface_class])

        self.alfav = Q(D(0.50)) if "10.9" in self.grade_name else Q(D(0.60))

        # ks (normal, oversized, slotted, long slotted)
        kss = (
            ("N", D(1), D(1)),
            ("O", D(0.85), D(0.85)),
            # ("S1", D(0.76), D(0.85)),
            # ("S2", D(0.85), D(0.76)),
            # ("L1", D(0.63), D(0.70)),
            # ("L2", D(0.70), D(0.63)),
        )
        for tup in kss:
            if self.bolt_holes == tup[0]:
                self.ks1 = tup[1]
                # self.ks2 = tup[2] <- future, slotted holes

    # SOLVING GRADE (AMERICAN OR EURO)
    def solveFromGrade(self, grade_model):
        if isinstance(grade_model, int):
            grade_model = BoltMaterialList.objects.get(id=int(grade_model))
        elif isinstance(grade_model, str):
            grade_model = BoltMaterialList.objects.get(name=grade_model)
        try:
            self.fub = Q(grade_model.fub, "MPa")
            self.fyb = Q(grade_model.fyb, "MPa")
            self.Ym2 = D(1.25)
            if self.fub.magnitude < 401:
                self.Ym2 = D(1.50)
            self.E = Q(grade_model.E, "MPa")
            self.grade_name = grade_model.name
        except Exception as e:
            raise CalengCrash("Something happend when solving bolt parameters"
                              " from provided bolt grade. Exc: " + str(e))

    # SOLVING DIAMETER (IMPERIAL OR METRIC)
    def solveFromSize(self, size_model):
        if isinstance(size_model, int):
            size_model = BoltSizeList.objects.get(id=int(size_model))
        elif isinstance(size_model, str):
            size_model = BoltSizeList.objects.get(name=size_model)
        try:
            self.length = Q(size_model.length, "mm")
            self.diameter = Q(size_model.diameter, "mm")
            self.shaft_length = Q(size_model.shaft_length, "mm")
            self.A = Q(size_model.A, "mm**2")
            self.As = Q(size_model.As, "mm**2")
            self.dm = Q(size_model.dm, "mm")
            self.size_name = size_model.name

            if self.bolt_holes == "N":
                self.d0 = Q(size_model.hole, "mm")
            elif self.bolt_holes == "O":
                self.d0 = Q(size_model.os_hole, "mm")
            else:
                raise CalengCrash("Hole diameters are only defined for normal"
                                  " or oversized holes")
        except Exception as e:
            raise CalengCrash("Something happend when solving bolt parameters"
                              " from provided bolt size. Exc: " + str(e))

    # BOLT STRENGTH TO TRACTION
    def getFt_Rd(self, report):
        hash_now = hash(self)
        if hash_now == self.Ft_Rd_hash:
            return self.Ft_Rd
        else:
            # FOR CAT-E JOINTS (PRET)
            if self.preloaded:
                desc_string = "PRELOADED BOLT: SOLVING MAX TENSION"
            # FOR CAT-D JOINTS (NON PRET)
            else:
                desc_string = "SNUG-TIGHT BOLT: SOLVING MAX TENSION"
            report.addLine(101, 20, desc_string, "Ft_Rd")

            # solve
            Ft_Rd = (D(0.9) * self.fub * self.As / self.Ym2).to("kN")

            # report
            report.addLine(100, 20, "", "As = " + str(self.As))
            report.addLine(100, 20, "", "Ym2 = " + str(self.Ym2))
            report.addLine(100, 20, "", "Ft_Rd = " + str(Ft_Rd))

            self.Ft_Rd_hash = hash_now
            self.Ft_Rd = Ft_Rd
        return Ft_Rd

    # BOLT STRENGTH TO SHEAR
    def getFv_Rd(self, report):
        # Title
        if self.preloaded:
            desc_string = "PRELOADED BOLT: SOLVING MAX SHEAR"
        else:
            desc_string = "SNUG-TIGHT BOLT: SOLVING MAX SHEAR"
        report.addLine(101, 20, desc_string, "Fv_Rd")

        # Solve
        Fv_Rd = (self.alfav * self.fub * self.A / self.Ym2).to("kN")

        # Report
        report.addLine(100, 20, "", "alfa_v = " + str(self.alfav))
        report.addLine(100, 20, "", "Ym2 = " + str(self.Ym2))
        report.addLine(100, 20, "", "Fv_Rd = " + str(Fv_Rd))

        return Fv_Rd

    # BOLT MAX NO-SLIPPING FORCE (PRELOADED ONLY)
    def getFs_Rd(self, report):

        if not self.preloaded:
            raise CalengCrash("Can't get Fs_Rd in a snug tight bolt!")
        else:
            desc_string = "PRELOADED BOLT: SOLVING SLIP-RESISTANT CAPACITY"
            report.addLine(101, 20, desc_string, "")

            # solving
            Fs_Rd = (
                self.n * self.ks1 * self.mu * self.Fp_C / self.Ym3).to("kN")

            # reporting
            desc_string = "Preloaded bolt parameters"
            calc_string = "μ = " + str(self.mu) + ", ks = " + str(self.ks1) +\
                          ", Fp_C = " + str(self.Fp_C)
            report.addLine(100, 20, desc_string, calc_string)
            desc_string = "Max Slip-Resistant per-bolt capacity"
            calc_string = "Fs_Rd = " + str(Fs_Rd)
            report.addLine(100, 20, desc_string, calc_string)

            return Fs_Rd

    def check(self, Ft_Ed_sls, Fv_Ed_sls, Ft_Ed_uls, Fv_Ed_uls, report):

        if self.preloaded:
            desc_string = "PRELOADED BOLT: STARTING BOLT CHECK"
            report.addLine(101, 20, desc_string, "")
            return self.check_preloaded(Ft_Ed_sls, Fv_Ed_sls, Ft_Ed_uls,
                                        Fv_Ed_uls, report)
        else:
            desc_string = "SNUG BOLT: STARTING BOLT CHECK"
            report.addLine(101, 20, desc_string, "")
            return self.check_snug(Ft_Ed_uls, Fv_Ed_uls, report)

    def check_preloaded(self, Ft_Ed_sls, Fv_Ed_sls, Ft_Ed_uls, Fv_Ed_uls,
                        report):

        # Avoid doing void calculations if there is no shear or tension
        if Fv_Ed_sls.magnitude == 0 and Fv_Ed_uls.magnitude == 0:
            Ft_Rd = self.getFt_Rd(report)
            return self.check_preloaded_tension(Ft_Ed_sls, Ft_Ed_uls,
                                                Ft_Rd, report)
        elif Ft_Ed_sls.magnitude == 0 and Ft_Ed_uls.magnitude == 0:
            Ft_Rd = self.getFt_Rd(report)
            Fs_Rd = self.getFs_Rd(report)
            return self.check_preloaded_shear(Ft_Ed_sls, Fv_Ed_sls, Ft_Ed_uls,
                                              Fv_Ed_uls, Ft_Rd, Fs_Rd, report)
        else:
            Ft_Rd = self.getFt_Rd(report)
            Fs_Rd = self.getFs_Rd(report)
            a = self.check_preloaded_tension(Ft_Ed_sls, Ft_Ed_uls,
                                             Ft_Rd, report)
            return self.check_preloaded_shear(Ft_Ed_sls, Fv_Ed_sls, Ft_Ed_uls,
                                              Fv_Ed_uls, Ft_Rd, Fs_Rd, report)
            return a and b

    def check_preloaded_tension(self, Ft_Ed_sls, Ft_Ed_uls, Ft_Rd, report):
        # 1 -- BLOCK 1: TENSION
        if Ft_Ed_uls > Ft_Rd:
            desc_string = "Bolt tension check | OVERLOADED"
            calc_string = "Ft_Ed_uls = " + str(Ft_Ed_uls) + " > Ft_Rd = " +\
                          str(Ft_Rd)
            report.addLine(500, 20, desc_string, calc_string)
            return False

        else:
            desc_string = "Bolt tension check | OK"
            calc_string = "Ft_Ed_uls = " + str(Ft_Ed_uls) + " < Ft_Rd = " +\
                          str(Ft_Rd)
            report.addLine(200, 20, desc_string, calc_string)
            return True

    def check_preloaded_shear(self, Ft_Ed_sls, Fv_Ed_sls, Ft_Ed_uls,
                              Fv_Ed_uls, Ft_Rd, Fs_Rd, report):

        # 2A -- BLOCK 2. SLIDING. PART A: ULS SLIDING
        if self.uls_slip:
            desc_string = "PRELOADED BOLT. SLIP-RESISTANT AT ULS: " +\
                          "STARTING BOLT CHECK"
            report.addLine(101, 20, desc_string, "")

            # check sliding
            if Fv_Ed_uls > Fs_Rd:
                desc_string = "Bolt sliding check | OVERLOADED"
                calc_string = "Fv_Ed_uls = " + str(Fv_Ed_uls) +\
                              " > Fs_Rd = " + str(Fs_Rd)
                report.addLine(500, 20, desc_string, calc_string)
                return False
            else:
                desc_string = "Bolt sliding check | OK"
                calc_string = "Fv_Ed_uls = " + str(Fv_Ed_uls) +\
                              " < Fs_Rd = " + str(Fs_Rd)
                report.addLine(200, 20, desc_string, calc_string)

            # scape if combo not needed
            if Fv_Ed_uls.magnitude == 0 or Ft_Ed_uls.magnitude == 0:
                report.addLine(100, 20, "Bolt combined check | Not needed", "")
                return True

            # check combo
            reduced_Fp_C = self.Fp_C - D(0.80) * Ft_Ed_uls
            Fs_Rd_uls = self.n * self.ks1 * self.mu * reduced_Fp_C / self.Ym3

            if Fv_Ed_uls > Fs_Rd_uls:
                desc_string = "Bolt combined check | OVERLOADED"
                calc_string = "Fv_Ed_uls = " + str(Fv_Ed_uls) +\
                              " > Fs_Rd_uls = " + str(Fs_Rd_uls)
                report.addLine(500, 20, desc_string, calc_string)
                return False
            else:
                desc_string = "Bolt combined check | OK"
                calc_string = "Fv_Ed_uls = " + str(Fv_Ed_uls) +\
                              " < Fs_Rd_uls = " + str(Fs_Rd_uls)
                report.addLine(200, 20, desc_string, calc_string)
                # end of calc this way, return true
                return True

        # 2B -- BLOCK 2. SLIDING. PART B: SLS SLIDING
        else:
            desc_string = "PRELOADED BOLT. SLIP-RESISTANT AT SLS: " +\
                          "STARTING BOLT CHECK"
            report.addLine(101, 20, desc_string, "")

            # check sliding
            if Fv_Ed_sls > Fs_Rd:
                desc_string = "Bolt sliding check | OVERLOADED"
                calc_string = "Fv_Ed_sls = " + str(Fv_Ed_sls) +\
                              " > Fs_Rd = " + str(Fs_Rd)
                report.addLine(500, 20, desc_string, calc_string)
                return False
            else:
                desc_string = "Bolt sliding check | OK"
                calc_string = "Fv_Ed_sls = " + str(Fv_Ed_sls) +\
                              " < Fs_Rd = " + str(Fs_Rd)
                report.addLine(200, 20, desc_string, calc_string)

            # if combo not needed, whe pass sliding combo, but still bearing
            if Fv_Ed_sls.magnitude == 0 or Ft_Ed_sls.magnitude == 0:
                report.addLine(100, 20, "Bolt combined check | Not needed", "")
            else:
                # check sliding combo
                reduced_Fp_C = self.Fp_C - D(0.80) * Ft_Ed_sls
                Fs_Rd_sls = self.n * self.ks1 * self.mu * reduced_Fp_C / self.Ym3

                if Fv_Ed_sls > Fs_Rd_sls:
                    desc_string = "Bolt combined check | OVERLOADED"
                    calc_string = "Fv_Ed_sls = " + str(Fv_Ed_sls) +\
                                  " > Fs_Rd_sls = " + str(Fs_Rd_sls)
                    report.addLine(500, 20, desc_string, calc_string)
                    return False
                else:
                    desc_string = "Bolt combined check | OK"
                    calc_string = "Fv_Ed_sls = " + str(Fv_Ed_sls) +\
                                  " < Fs_Rd_sls = " + str(Fs_Rd_sls)
                    report.addLine(200, 20, desc_string, calc_string)

            # check bearing and bearing combo
            return self.check_snug(Ft_Ed_uls, Fv_Ed_uls, report)

    def check_snug(self, Ft_Ed, Fv_Ed, report):
        Ft_Rd = self.getFt_Rd(report)
        Fv_Rd = self.getFv_Rd(report)

        if Ft_Ed > Ft_Rd:
            desc_string = "Bolt tension check | OVERLOADED"
            calc_string = "Ft_Ed = " + str(Ft_Ed) + " > Ft_Rd = " +\
                          str(Ft_Rd)
            report.addLine(500, 20, desc_string, calc_string)
            return False
        else:
            desc_string = "Bolt tension check | OK"
            calc_string = "Ft_Ed = " + str(Ft_Ed) + " < Ft_Rd = " +\
                          str(Ft_Rd)
            report.addLine(200, 20, desc_string, calc_string)

        if Fv_Ed > Fv_Rd:
            desc_string = "Bolt shear check | OVERLOADED"
            calc_string = "Fv_Ed = " + str(Fv_Ed) + " > Fv_Rd = " +\
                          str(Fv_Rd)
            report.addLine(500, 20, desc_string, calc_string)
            return False
        else:
            desc_string = "Bolt shear check | OK"
            calc_string = "Fv_Ed = " + str(Fv_Ed) + " < Fv_Rd = " +\
                          str(Fv_Rd)
            report.addLine(200, 20, desc_string, calc_string)

        # Here, single tests are passed
        if Fv_Ed.magnitude == 0 or Ft_Ed.magnitude == 0:
            report.addLine(100, 20, "Bolt combined check | Not needed", "")
            return True

        factor = (Fv_Ed / Fv_Rd) + (Ft_Ed / (D(1.4) * Ft_Rd))

        if factor > 1:
            desc_string = "Bolt combined check | OVERLOADED"
            calc_string = "Fv_Ed/Fv_Rd + Ft_Ed/(1.4*Ft_Rd) = " +\
                          str(factor) + " > 1"
            report.addLine(500, 20, desc_string, calc_string)
            return False
        else:
            desc_string = "Bolt combined check | OK"
            calc_string = "Fv_Ed/Fv_Rd + Ft_Ed/(1.4*Ft_Rd) = " +\
                          str(factor) + " < 1"
            report.addLine(200, 20, desc_string, calc_string)
            return True


# Bolt class IMPERIAL
class AISCBolt:
    pass


##################################################
# _______  BOLT ARRAYS. (can be imperial)  _____ #
##################################################
class BoltArray:
    def __init__(self, bolt_array, bolt, report):
        if isinstance(bolt_array, dict):
            # HERE INTRODUCING INCONSISTENCY p1, p1_string vs p1, p1_list
            self.p1_string = bolt_array['p1']
            self.p2_string = bolt_array['p2']
            self.use = bolt_array['use']
        else:
            # HERE INTRODUCING INCONSISTENCY p1, p1_string vs p1, p1_list
            self.p1_string = bolt_array.p1
            self.p2_string = bolt_array.p2
            self.use = bolt_array.use

        self.p1 = self.from_tekla_string(self.p1_string)
        self.p2 = self.from_tekla_string(self.p2_string)
        self.bolt = bolt
        self.n1 = Q(len(self.p1) + 1)
        self.n2 = Q(len(self.p2) + 1)
        self.n = self.n1 * self.n2
        self.connected_plate = None
        self.bolt_matrix = None

        # Informing report
        if report:
            desc_string = "BOLT ARRAY - {}: {} x {}".format(
                self.use, self.p1_string, self.p2_string
            )
            report.addLine(101, 10, desc_string, "")

    def check(self, forces, report):
        return False

    def from_tekla_string(self, tekla_string):
        if not isinstance(tekla_string, str):
            print("NOT STRING")
        if tekla_string == "0" or tekla_string == "":
            return [] * ureg.mm
        nested_array = tekla_string.split()
        dim_array = []
        for item in nested_array:
            if "*" in item:
                splited = item.split("*")
                dim_array.extend([D(splited[1])] * int(splited[0]))
            else:
                dim_array.append(D(item))
        return dim_array * ureg.mm

    def p1_mean(self):
        if len(self.p1) == 0:
            return Q(D(0), 'mm')
        else:
            return np.mean(self.p1)

    def p2_mean(self):
        if len(self.p2) == 0:
            return Q(D(0), 'mm')
        else:
            return np.mean(self.p2)

    def p1_sum(self):
        if len(self.p1) == 0:
            return Q(D(0), 'mm')
        else:
            return np.sum(self.p1)

    def p2_sum(self):
        if len(self.p2) == 0:
            return Q(D(0), 'mm')
        else:
            return np.sum(self.p2)

    def p1_median(self):
        """ returns the first bolt-to-bolt distance bigger than p1_sum/2
            like here:
                        |    +    +    +     +  +   +    +   |
                             +---------------+
                                   p1_median
                             +-------------+-------------+
                                p1_sum()/2     p1_sum()/2  """
        p_stack = Q(D(0), 'mm')
        half_p1 = self.p1_sum() / 2
        for p in self.p1:
            if p_stack < half_p1:
                p_stack += p
        return p_stack

    def p2_median(self):
        """ returns the first bolt-to-bolt distance bigger than  p2_sum/2
            like here:
                        |    +    +    +     +  +   +    +   |
                             +---------------+
                                   p2_median
                             +-------------+-------------+
                                p2_sum()/2     p2_sum()/2  """
        p_stack = Q(D(0), 'mm')
        half_p2 = self.p2_sum() / 2
        for p in self.p2:
            if p_stack < half_p2:
                p_stack += p
        return p_stack

    def get_bolt_matrix(self):
        """ Compute and store the bolt matrix positional data.
            Its only calculated and reported first time.
            --- --- ---
            Returns a list of tuples. Each tuple having this structure:
            (i, row, col, x1, x2, d, A, As)
            Starting from botton left, you increase i, through the row
            to the right, then next column (up), etc """

        # Return previously solved
        if self.bolt_matrix is not None:
            return self.bolt_matrix

        self.bolt_matrix = []
        p1_count = len(self.p1) + 1
        p2_count = len(self.p2) + 1
        p1_total = self.p1_sum()
        p2_total = self.p2_sum()
        for row in range(0, p2_count):
            for col in range(0, p1_count):
                i = col + p1_count * row
                x1 = - p1_total / 2 + np.sum(self.p1[0:col])
                x2 = - p2_total / 2 + np.sum(self.p2[0:row])
                d = np.sqrt(x1 ** 2 + x2 ** 2)
                A = self.bolt.A
                As = self.bolt.As
                bolt_tuple = (i, row, col, x1, x2, d, A, As)
                self.bolt_matrix.append(bolt_tuple)
        return self.bolt_matrix

        # Old approach with n1 and n2
        # for row in range(0, self.n1):
        #     for col in range(0, self.n2):
        #         i = col + self.n2 * row
        #         x1 = (row - (self.n1 - D(1)) / D(2)) * self.p1
        #         x2 = (col - (self.n2 - D(1)) / D(2)) * self.p2
        #         d = np.sqrt(x1 ** 2 + x2 ** 2)
        #         A = self.bolt.A
        #         As = self.bolt.As
        #         bolt_tuple = (i, row, col, x1, x2, d, A, As)
        #         self.bolt_matrix.append(bolt_tuple)
        # return self.bolt_matrix


# Shear bolt group
class ShearBoltArray(BoltArray):
    def __init__(self, bolt_array, bolt, report):
        BoltArray.__init__(self, bolt_array, bolt, report)
        self.computed_Fv_Ed = {}  # Must contain hash_of_forces: Fv_Ed_computed

    def getFv_Ed_max(self, forces, report):
        # Return if already computed
        hash_of_forces = hash(forces) + hash(self)
        if hash_of_forces in self.computed_Fv_Ed.keys():
            return self.computed_Fv_Ed.get(hash_of_forces)

        desc_string = "SHEAR BOLT ARRAY: COMPUTING MAX SHEAR AT BOLTS"\
                      " | {}".format(forces.use)
        report.addLine(101, 20, desc_string, "")
        desc_string = "In plane shear distribution"
        calc_string = "n = " + str(self.n)
        report.addLine(100, 20, desc_string, calc_string)

        # If only one bolt, cant be torsion. Or crash.
        if not Q(D(-1), "N*mm") < forces.T < Q(D(1), "N*mm"):
            if self.n == 1:
                raise CalengCrash("One single bolt can't"
                                  " resist torsion forces!!")
        # else (T = 0), we dont need to compute anything else.
        else:
            Fv_Ed = (forces.V / self.n).to("kN")
            desc_string = "Max shear (no torsion)"
            calc_string = "Fv_Ed = " + str(Fv_Ed)
            report.addLine(100, 20, desc_string, calc_string)
            self.computed_Fv_Ed[hash_of_forces] = Fv_Ed
            return Fv_Ed

        sum_A_d2 = Q(D(0), "mm**4")
        max_A_d = Q(D(0), "mm**3")

        # Distribution of shear: shear_share
        for b in self.get_bolt_matrix():
            if b[5] * self.bolt.A > max_A_d:
                max_A_d = b[5] * self.bolt.A
            sum_A_d2 += b[5] ** 2 * self.bolt.A
            desc_string = "Bolt " + str(b[0]) + ": row = " + str(b[1]) +\
                          ", col = " + str(b[2])
            calc_string = "d = " + str(b[5])
            report.addLine(100, 20, desc_string, calc_string)

        report.addLine(100, 20, "Total Inertia", "I = " + str(sum_A_d2))
        shear_share = max_A_d / sum_A_d2

        # Getting worst bolt Fv_Ed
        Fv_Ed_T = (forces.T * shear_share).to("kN")
        desc_string = "Max shear due to torsion"
        calc_string = "Fv_Ed_T = " + str(Fv_Ed_T)
        report.addLine(100, 20, desc_string, calc_string)

        Fv_Ed = (Fv_Ed_T + forces.V / self.n).to("kN")
        desc_string = "Max shear (including torsion)"
        calc_string = "Fv_Ed = " + str(Fv_Ed)
        report.addLine(100, 20, desc_string, calc_string)
        self.computed_Fv_Ed[hash_of_forces] = Fv_Ed
        return Fv_Ed

    def check(self, sls_forces, uls_forces, report):

        if sls_forces.P.magnitude != 0 or sls_forces.M.magnitude != 0 \
                or uls_forces.P.magnitude != 0 or uls_forces.M.magnitude != 0:
            raise CalengCrash("Not a ShearForcesSet provided"
                              " to ShearBoltArray.check()")
        else:
            Fv_Ed_max_sls = self.getFv_Ed_max(sls_forces, report)
            Fv_Ed_max_uls = self.getFv_Ed_max(uls_forces, report)
            bolt_check = self.bolt.check(
                Q(0, "kN"),
                Fv_Ed_max_sls,
                Q(0, "kN"),
                Fv_Ed_max_uls,
                report
            )
            # Its needed to return de check status
            return bolt_check


# Tension bolt group
class TensionBoltArray(BoltArray):
    def __init__(self, bolt_array, bolt, report):
        BoltArray.__init__(self, bolt_array, bolt, report)
        self.computed_Ft_Ed = {}  # Must contain hash_of_forces: Fv_Ed_computed

    def getFt_Ed_max_preloaded(self, forces, report):
        desc_string = "Preloaded bolt group tension distribution"
        calc_string = "n = " + str(self.n)
        report.addLine(100, 20, desc_string, calc_string)

        # Tension distribution. FIST STEP: Getting inertias.
        I1 = Q(D(0), "mm**4")
        I2 = Q(D(0), "mm**4")
        for b in self.get_bolt_matrix():
            I1 += b[7] * b[3] ** 2  # b[3] is x1
            I2 += b[7] * b[4] ** 2  # b[4] is x2

        # Tension distribution. SECOND STEP: Getting forces, reporting
        max_A_x1 = Q(D(0), "mm**3")
        max_A_x2 = Q(D(0), "mm**3")
        for b in self.get_bolt_matrix():
            if b[3] * b[7] > max_A_x1:
                max_A_x1 = b[3] * b[7]
            if b[4] * b[7] > max_A_x2:
                max_A_x2 = b[4] * b[7]
            desc_string = "Bolt " + str(b[0]) + ": row = " + str(b[1]) +\
                          ", col = " + str(b[2])
            calc_string = "x1={}, x2={}, As={}".format(
                str(b[3]), str(b[4]), str(b[7]))
            report.addLine(100, 20, desc_string, calc_string)

        # Getting worst bolt Ft_Ed_max
        Ft_Ed_M2 = (forces.M2 * max_A_x1 / I1).to("kN")
        Ft_Ed_M3 = (forces.M3 * max_A_x2 / I2).to("kN")
        Ft_Ed_P = (forces.P / self.n).to("kN")
        desc_string = "Max bolt tension due to moments"
        calc_string = "Ft_Ed_M2 = {}, Ft_Ed_M3 = {}".format(
            str(Ft_Ed_M2), str(Ft_Ed_M3))
        report.addLine(100, 20, desc_string, calc_string)
        desc_string = "Max bolt tension due to joint tension"
        calc_string = "Ft_Ed_P = {}".format(str(Ft_Ed_P))
        report.addLine(100, 20, desc_string, calc_string)

        Ft_Ed = Ft_Ed_P + Ft_Ed_M2 + Ft_Ed_M3
        desc_string = "Max bolt tension"
        calc_string = "Ft_Ed = " + str(Ft_Ed)
        report.addLine(100, 20, desc_string, calc_string)
        return Ft_Ed

    def getFt_Ed_max_snug(self, forces, report):
        desc_string = "Snug-tight bolt group tension distribution"
        calc_string = "n = " + str(self.n)
        report.addLine(100, 20, desc_string, calc_string)

        if self.connected_plate is None:
            if forces.M2.magnitude != 0 and\
                    forces.M3.magnitude != 0:
                raise CalengCrash("TensionBoltArray needs a connected_plate"
                                  " if snug tight bolts.")
            else:
                return self.getFt_Ed_only_P(forces, report)

        if self.n2 == 1 and forces.M2.magnitude != 0:
            raise CalengCrash("Cant resist moments without lever arm")

        if self.connected_plate.length.magnitude == 0\
                or self.connected_plate.width.magnitude == 0:
            raise CalengCrash("Plate must have a width and length")

        # Get forces due to M2
        b = self.connected_plate.length
        h = self.connected_plate.width
        # Avoid 0 division
        p2_lev = self.p2_mean() if len(self.p2) > 0 else self.connected_plate.e2_main
        d = self.n1 * self.bolt.As / p2_lev
        c1 = (b - np.sqrt(d * b)) / (b - d) * h
        c = h - c1
        I2 = d * c ** 3 / 3 + b * c1 ** 3 / 3
        desc_string = "Solving parameters for M2"
        report.addLine(100, 20, desc_string, "d = {}".format(str(d)))
        report.addLine(100, 20, "", "c1 = {}".format(str(c1)))
        report.addLine(100, 20, "", "c = {}".format(str(c)))
        report.addLine(100, 20, "", "I = {}".format(str(I2)))

        Ft_Ed_M2 = (forces.M2 * c * self.bolt.As / I2).to("kN")
        desc_string = "Max bolt tension due to joint M2"
        calc_string = "Ft_Ed_M2 = {}".format(str(Ft_Ed_M2))
        report.addLine(100, 20, desc_string, calc_string)

        if self.n1 == 1 and forces.M3.magnitude != 0:
            raise CalengCrash("Cant resist moments without lever arm")

        # Get forces due to M3
        b = self.connected_plate.width
        h = self.connected_plate.length
        # Avoid 0 division
        p1_lev = self.p1_mean() if len(self.p1) > 0 else self.connected_plate.e1_main
        d = self.n2 * self.bolt.As / p1_lev
        c1 = (b - np.sqrt(d * b)) / (b - d) * h
        c = h - c1
        I3 = d * c ** 3 / 3 + b * c1 ** 3 / 3
        desc_string = "Solving parameters for M3"
        report.addLine(100, 20, desc_string, "d = {}".format(str(d)))
        report.addLine(100, 20, "", "c1 = {}".format(str(c1)))
        report.addLine(100, 20, "", "c = {}".format(str(c)))
        report.addLine(100, 20, "", "I = {}".format(str(I3)))

        Ft_Ed_M3 = (forces.M3 * c * self.bolt.As / I3).to("kN")
        desc_string = "Max bolt tension due to joint M3"
        calc_string = "Ft_Ed_M3 = {}".format(str(Ft_Ed_M3))
        report.addLine(100, 20, desc_string, calc_string)

        # Get forces due to P
        Ft_Ed_P = (forces.P / self.n).to("kN")
        desc_string = "Max bolt tension due to joint tension"
        calc_string = "Ft_Ed_P = {}".format(str(Ft_Ed_P))
        report.addLine(100, 20, desc_string, calc_string)

        # Returning solution
        Ft_Ed = Ft_Ed_P + Ft_Ed_M2 + Ft_Ed_M3
        desc_string = "Max bolt tension"
        calc_string = "Ft_Ed = " + str(Ft_Ed)
        report.addLine(100, 20, desc_string, calc_string)
        return Ft_Ed

    def getFt_Ed_only_P(self, forces, report):
        desc_string = "Snug-tight bolt group tension (no moments)"
        calc_string = "n = " + str(self.n)
        report.addLine(100, 20, desc_string, calc_string)

        # Returning Ft_Ed
        Ft_Ed_P = (forces.P / self.n).to("kN")
        desc_string = "Max bolt tension"
        calc_string = "Ft_Ed = " + str(Ft_Ed_P)
        report.addLine(100, 20, desc_string, calc_string)
        return Ft_Ed_P

    def getFt_Ed_max(self, forces, report):
        # Return if already computed (forces or self may be changed)
        hash_of_forces = hash(forces) + hash(self)
        if hash_of_forces in self.computed_Ft_Ed.keys():
            return self.computed_Ft_Ed.get(hash_of_forces)

        desc_string = "TENSION BOLT ARRAY: COMPUTING MAX TENSIONS AT BOLTS"\
                      " | {}".format(forces.use)
        report.addLine(101, 20, desc_string, "")

        if self.bolt.preloaded:
            Ft_Ed = self.getFt_Ed_max_preloaded(forces, report)
        else:
            Ft_Ed = self.getFt_Ed_max_snug(forces, report)

        # Save and return
        self.computed_Ft_Ed[hash_of_forces] = Ft_Ed
        return Ft_Ed

    def check(self, sls_forces, uls_forces, report):

        # If not shear forces, Crash.
        if sls_forces.T.magnitude != 0 or sls_forces.V.magnitude != 0 \
                or uls_forces.T.magnitude != 0 or uls_forces.V.magnitude != 0:
            raise CalengCrash("Not a FrontForcesSet provided"
                              " to TensionBoltArray.check()")

        else:
            Ft_Ed_max_sls = self.getFt_Ed_max(sls_forces, report)
            Ft_Ed_max_uls = self.getFt_Ed_max(uls_forces, report)
            bolt_check = self.bolt.check(
                Ft_Ed_max_sls,
                Q(0, "kN"),
                Ft_Ed_max_uls,
                Q(0, "kN"),
                report
            )
            return bolt_check


# Shear and tensioned bolt group
class ShearTensionBoltArray(ShearBoltArray, TensionBoltArray):
    # quizas haya q modificar esto. aqui habria q checkear bolt a bolt
    # porq el peor shear no coincidira con el peor tension...
    # de momento lo consideramos despreciable!!

    def __init__(self, bolt_array, bolt, report):
        ShearBoltArray.__init__(self, bolt_array, bolt, report)
        TensionBoltArray.__init__(self, bolt_array, bolt, None)

    def check(self, sls_forces, uls_forces, report):

        Ft_Ed_max_sls = self.getFt_Ed_max(sls_forces, report)
        Ft_Ed_max_uls = self.getFt_Ed_max(uls_forces, report)
        Fv_Ed_max_sls = self.getFv_Ed_max(sls_forces, report)
        Fv_Ed_max_uls = self.getFv_Ed_max(uls_forces, report)
        bolt_check = self.bolt.check(
            Ft_Ed_max_sls,
            Fv_Ed_max_sls,
            Ft_Ed_max_uls,
            Fv_Ed_max_uls,
            report
        )
        # Its needed to return de check status
        return bolt_check


##################################################
# ______  BOLT CIRCLES. (can be imperial)  _____ #
##################################################
class BoltCircle:
    pass


# Shear bolt group
class ShearBoltCircle(BoltCircle):
    pass


# Friction (prestresed) bolt group
class FrictionBoltCircle(BoltCircle):
    pass


# Tension bolt group
class TensionBoltCircle(BoltCircle):
    pass


# Shear and tensioned bolt group
class ShearTensionBoltCircle(ShearBoltCircle, TensionBoltCircle):
    pass


# Friction and tensioned bolt group
class FrictionTensionBoltCircle(FrictionBoltCircle, TensionBoltCircle):
    pass
