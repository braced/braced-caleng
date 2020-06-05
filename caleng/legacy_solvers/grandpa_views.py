from django.shortcuts import render
from django.http import HttpResponse
from django.views import View
from django.contrib import messages
from caleng.parts.exceptions import CalengCrash
from caleng.parts.reports import Report
from engine.forms import *
from caleng.parts.settings import *
from django.http import HttpResponseRedirect


class Grandpa_Calc(View):

    """ def fill_meta(self) <- Method to be created in child class !!!
        REMEMBER: IT'S MANDATORY TO RUN builder.py ONCE YOU CHANGE
        SOME STRING IN A CHILD VIEW !!!!!!!

        >>> # make build

        """

    def fill_defaults(self):
        """ Initializes view with default strings. MANDATORY! """

        self.forms = {}  # form_name: form object
        self.models = {}  # model_name: model object
        self.calc = None

        self.extra_data_strings = [
            # (USE_STRING, FORM_PREFIX, FormClass),
            # ("MAIN", "main", CalcExtraDataS001),
        ]
        self.bolt_array_strings = [
            # (USE_STRING, FORM_PREFIX, BOLT_FORM_PREFIX),
            # ("MAIN", "main", "main"),
        ]
        self.bolt_strings = [
            # (USE_STRING, FORM_PREFIX),
            # ("MAIN", "main")
        ]
        self.force_strings = [
            # (USE_STRING, FORM_PREFIX, FORM_TYPE),
            # ("ULS", "uls", "FULL"),
            # ("SLS", "sls", "FULL"),
        ]
        self.profile_strings = [
            # TYPE_LIST=None is all types
            # (USE_STRING, FORM_PREFIX, TYPE_LIST, CAN_BE_ANY),
            # ("LANDING", "landing", None, False),
            # ("ARRIVING", "beam", ["L", "U"], True),
        ]
        self.plate_strings = [
            # FORM_TYPE's -> BOLTED, BOLTED_STIFFENER, WELDED, DUMMY
            # (USE_STRING, FORM_PREFIX, FORM_TYPE),
            # ("END_PLATE", "endplate", "BOLTED"),
        ]
        self.cover_plates_selection_strings = [
            # (USE_STRING, FORM_PREFIX),
            # ("MAIN", "main"),
        ]
        self.position_strings = [
            # (USE_STRING, FORM_PREFIX, PROFILE_PREFIX),
            # ("MAIN", "main", "landing"),
        ]
        self.extra_bracing_strings = [
            # (USE_STRING, FORM_PREFIX),
            # ("MAIN", "bracings"),
        ]
        self.sheetnumber = "X001"
        self.code = "EC3"
        self.solver = None

    def form_tweaks(self):
        """ This will be called at the end of build_forms. You can
            write some modifications in this function in your view """
        pass

    def build_forms(self, request, post_data=None):
        prof = request.user.profile

        # EDITING FORM BUILD
        if self.calc:
            calc_form = BasicCalculationForm(prof, instance=self.calc)
            self.forms["calc_form"] = calc_form

            for use, prefix, ExtraDataFormClass in self.extra_data_strings:
                ed = self.calc.calcextradatamodel
                ed_form = ExtraDataFormClass(instance=ed, prefix=prefix)
                self.forms[prefix + "_extra_data_form"] = ed_form

            for use, prefix, bolt_prefix in self.bolt_array_strings:
                ba = self.calc.bolt_arrays.get(use=use)
                ba_form = BoltArrayForm(instance=ba, prefix=prefix)
                self.forms[prefix + "_bolt_array_form"] = ba_form

            for use, prefix in self.bolt_strings:
                b = self.calc.bolts.get(use=use)
                b_form = BoltForm(request, instance=b, prefix=prefix)
                self.forms[prefix + "_bolt_form"] = b_form

            for use, prefix, form_type in self.force_strings:
                # THIS CAN BE PASSED TO THE FORM __INIT__ WHEN WORKING
                if form_type == "SHEAR":
                    form = ShearForcesSetForm
                elif form_type == "TIE":
                    form = TieForcesSetForm
                elif form_type == "AXIAL":
                    form = AxialForcesSetForm
                elif form_type == "BEAM":
                    form = BeamForcesSetForm
                else:
                    form = FullForcesSetForm
                force = self.calc.forces.get(use=use)
                force_form = form(instance=force, prefix=prefix)
                self.forms[prefix + "_force_form"] = force_form

            for use, prefix, type_list, can_any in self.profile_strings:
                profile = self.calc.profiles.get(use=use)
                profile_form = ProfileForm(
                    request, instance=profile, prefix=prefix, can_any=can_any)
                profile_form.allowed(type_list, request, instance=profile,
                                     can_any=can_any)
                self.forms[prefix + "_profile_form"] = profile_form

            for use, prefix, form_type in self.plate_strings:
                # THIS CAN BE PASSED TO THE FORM __INIT__ WHEN WORKING
                if form_type in ["BOLTED", "BOLTED_STIFFENER"]:
                    plate = self.calc.boltedplatemodel_set.get(use=use)
                    plate_form = BoltedPlateForm(
                        request, instance=plate, prefix=prefix)
                    if form_type == "BOLTED_STIFFENER":
                        plate_form.convert_to_stiffener()
                    self.forms[prefix + "_plate_form"] = plate_form
                elif form_type == "WELDED":
                    plate = self.calc.weldedplatemodel_set.get(use=use)
                    plate_form = WeldedPlateForm(
                        request, instance=plate, prefix=prefix)
                    self.forms[prefix + "_plate_form"] = plate_form
                else:
                    plate = self.calc.boltedplatemodel_set.get(use=use)
                    plate_form = DummyFrontPlateForm(
                        instance=plate, prefix=prefix)
                    self.forms[prefix + "_plate_form"] = plate_form

            for use, prefix in self.cover_plates_selection_strings:
                selection = self.calc.cover_plates_selections.get(use=use)
                selection_form = CoverPlatesSelectionForm(
                    instance=selection, prefix=prefix)
                form_name = prefix + "_cover_plates_selection_form"
                self.forms[form_name] = selection_form

            for use, prefix, profile_prefix in self.position_strings:
                position = self.calc.positions.get(use=use)
                position_form = SectionPositionForm(
                    instance=position, prefix=prefix)
                form_name = prefix + "_position_form"
                self.forms[form_name] = position_form

            for use, prefix in self.extra_bracing_strings:
                extra_bracing = self.calc.extra_bracings.get(use=use)
                extra_bracing_form = ExtraBracingsForm(
                    instance=extra_bracing, prefix=prefix)
                form_name = prefix + "_extra_bracing_form"
                self.forms[form_name] = extra_bracing_form

        # NON-EDITING FORM BUILDING
        else:
            calc_form = BasicCalculationForm(prof, post_data)
            self.forms["calc_form"] = calc_form

            for use, prefix, ExtraDataFormClass in self.extra_data_strings:
                ed_form = ExtraDataFormClass(post_data, prefix=prefix)
                self.forms[prefix + "_extra_data_form"] = ed_form

            for use, prefix, bolt_prefix in self.bolt_array_strings:
                ba_form = BoltArrayForm(post_data, prefix=prefix)
                self.forms[prefix + "_bolt_array_form"] = ba_form

            for use, prefix in self.bolt_strings:
                b_form = BoltForm(request, post_data, prefix=prefix)
                self.forms[prefix + "_bolt_form"] = b_form

            for use, prefix, form_type in self.force_strings:
                # THIS CAN BE PASSED TO THE FORM __INIT__ WHEN WORKING
                if form_type == "SHEAR":
                    form = ShearForcesSetForm
                elif form_type == "TIE":
                    form = TieForcesSetForm
                elif form_type == "AXIAL":
                    form = AxialForcesSetForm
                elif form_type == "BEAM":
                    form = BeamForcesSetForm
                else:
                    form = FullForcesSetForm
                force_form = form(post_data, prefix=prefix)
                self.forms[prefix + "_force_form"] = force_form

            for use, prefix, type_list, can_any in self.profile_strings:
                profile_form = ProfileForm(
                    request, post_data, prefix=prefix, can_any=can_any)
                profile_form.allowed(type_list, request, can_any=can_any)
                self.forms[prefix + "_profile_form"] = profile_form

            for use, prefix, form_type in self.plate_strings:
                # THIS CAN BE PASSED TO THE FORM __INIT__ WHEN WORKING
                if form_type in ["BOLTED", "BOLTED_STIFFENER"]:
                    plate_form = BoltedPlateForm(
                        request, post_data, prefix=prefix)
                    if form_type == "BOLTED_STIFFENER":
                        plate_form.convert_to_stiffener()
                    self.forms[prefix + "_plate_form"] = plate_form
                elif form_type == "WELDED":
                    plate_form = WeldedPlateForm(
                        request, post_data, prefix=prefix)
                    self.forms[prefix + "_plate_form"] = plate_form
                else:
                    plate_form = DummyFrontPlateForm(
                        post_data, prefix=prefix)
                    self.forms[prefix + "_plate_form"] = plate_form
            for use, prefix in self.cover_plates_selection_strings:
                selection_form = CoverPlatesSelectionForm(
                    post_data, prefix=prefix)
                form_name = prefix + "_cover_plates_selection_form"
                self.forms[form_name] = selection_form

            for use, prefix, profile_prefix in self.position_strings:
                position_form = SectionPositionForm(
                    post_data, prefix=prefix)
                form_name = prefix + "_position_form"
                self.forms[form_name] = position_form

            for use, prefix in self.extra_bracing_strings:
                extra_bracing_form = ExtraBracingsForm(
                    post_data, prefix=prefix)
                form_name = prefix + "_extra_bracing_form"
                self.forms[form_name] = extra_bracing_form

        # Last but not least, call form_tweaks!!
        self.form_tweaks()

    def build_models(self):
        # LOOP 0. Form to Model basics
        for form_name, form in self.forms.items():
            # fill self.models
            model_name = form_name.replace("_form", "")
            self.models[model_name] = form.save(commit=False)

            # Extra Data forms
            # for use, prefix, ExtraDataFormClass in self.extra_data_strings:
            #     if prefix + "_extra_data_form" == form_name:
            #         self.models[model_name].use = use_string
            # Bolt Array forms
            for use_string, prefix, bolt_prefix in self.bolt_array_strings:
                if prefix + "_bolt_array_form" == form_name:
                    self.models[model_name].use = use_string
            # Bolt forms
            for use_string, prefix in self.bolt_strings:
                if prefix + "_bolt_form" == form_name:
                    self.models[model_name].use = use_string
            # Forces forms
            for use_string, prefix, form_type in self.force_strings:
                if prefix + "_force_form" == form_name:
                    self.models[model_name].use = use_string
            # Profile forms
            for use_string, prefix, type_list, can_any in self.profile_strings:
                if prefix + "_profile_form" == form_name:
                    model_pk = form.cleaned_data['profile']
                    self.models[model_name].set_relations(
                        use_string, model_pk)
            # Plates forms
            for use_string, prefix, form_type in self.plate_strings:
                if prefix + "_plate_form" == form_name:
                    self.models[model_name].use = use_string
            # Plates forms
            for use_string, prefix in self.cover_plates_selection_strings:
                if prefix + "_cover_plates_selection_form" == form_name:
                    self.models[model_name].use = use_string
            # Position forms
            for use_string, prefix, profile_prefix in self.position_strings:
                if prefix + "_position_form" == form_name:
                    self.models[model_name].use = use_string
                    self.models[model_name].flip_gs = form.flip_gs
            # Extra bracings form
            for use_string, prefix in self.extra_bracing_strings:
                if prefix + "_extra_bracing_form" == form_name:
                    self.models[model_name].use = use_string

            # Bind to calc and save
            if model_name not in ["calc"]:
                self.models[model_name].calc = self.calc
            self.models[model_name].save()

        # LOOP 1. Link bolts and bolt arrays
        for ba_use, ba_prefix, bolt_prefix in self.bolt_array_strings:
            for b_use, b_prefix in self.bolt_strings:
                if b_prefix == bolt_prefix:
                    ba_name = ba_prefix + "_bolt_array"
                    b_name = b_prefix + "_bolt"
                    self.models[b_name].bolt_array = self.models[ba_name]
                    self.models[b_name].save()

        # LOOP 2. Link profile and position
        for pro_use, pro_prefix, type_list, can_any in self.profile_strings:
            for pos_use, pos_prefix, profile_prefix in self.position_strings:
                if pro_prefix == profile_prefix:
                    pro_name = pro_prefix + "_profile"
                    pos_name = pos_prefix + "_position"
                    self.models[pos_name].profile = self.models[pro_name]
                    self.models[pos_name].save()

    def void_get(self, request):

        # Build forms
        if "edit" in request.GET:
            try:
                self.calc = BasicCalculationModel.objects.get(
                    uuid=request.GET["edit"],
                    project__in=request.user.profile.open_projects())
            except BasicCalculationModel.DoesNotExist:
                messages.error(
                    request, ("The calc does not exist or you can't edit it"))
                self.calc = None
                return HttpResponseRedirect(request.path)
            self.build_forms(request)
        else:
            self.build_forms(request)

        # Rendering GET Response
        enginesheet_template_path = 'enginesheets/' +\
            self.sheetnumber + '_' + self.code + '.html'
        page_title = CALCULATION_NAMES[self.sheetnumber] +\
            " | " + CODE_NAMES[self.code]
        context = {
            **self.forms,
            'calc_object': self.calc,
            'calcs': CALCULATION_LINKS,
            'calc_names': CALCULATION_NAMES,
            'page_title': page_title,
            'sheetnumber': self.sheetnumber,
        }
        return render(request, enginesheet_template_path, context)

    def void_post(self, request):

        # Build forms
        self.build_forms(request, post_data=request.POST)

        # processing
        cache_pk = None
        report = None

        forms_valid = True
        for form_name, form in self.forms.items():
            if not form.is_valid():
                forms_valid = False

        if forms_valid:

            # handling calc
            self.calc = self.forms["calc_form"].save(commit=False)
            # validating user to write in project
            if self.calc.project not in request.user.profile.open_projects():
                return HttpResponse(
                    "You can not edit this project."
                    " See hackers.txt!",
                    status=401)
            try:
                self.calc.parent_calc = BasicCalculationModel.objects.get(
                    uuid=request.POST.get('parent_calc_uuid', None))
                self.calc.is_published = self.calc.parent_calc.is_published
            except BasicCalculationModel.DoesNotExist:
                self.calc.parent_calc = None
            except ValueError:
                self.calc.parent_calc = None

            self.calc.user = request.user
            self.calc.enginesheet = self.sheetnumber
            self.calc.code = self.code
            self.calc.save()
            self.models['calc'] = self.calc

            # Build models
            self.build_models()

            # Solving
            try:
                report = self.solver(self.models)
                if self.calc.is_structural_safe:
                    messages.success(
                        request,
                        ("Checked")
                    )
                else:
                    messages.warning(
                        request,
                        ("FAILED: Unsafe connection. Find details @ report")
                    )
            except CalengCrash as e:
                messages.warning(
                    request,
                    ("Calculation crashed with error: " + str(e))
                )
                report = Report(self.calc)
                report.set_unsafe()

            # Caching report and passing pk to template
            cache_pk = report.to_cache()

        else:
            for form_name, form in self.forms.items():
                if form.is_valid():
                    print("[+] Valid form: " + form_name)
                else:
                    print("[-] Invalid form: " + form_name)
                    print(form)
                    print(form.errors)
            messages.error(
                request,
                ("Bad forms. Errors while parsing data.")
            )

        # Rendering POST Response
        enginesheet_template_path = 'enginesheets/' +\
            self.sheetnumber + '_' + self.code + '.html'
        page_title = CALCULATION_NAMES[self.sheetnumber] +\
            " | " + CODE_NAMES[self.code]
        context = {
            **self.forms,
            'calc_object': self.calc,
            'report': report,
            'cache_pk': cache_pk,
            'calcs': CALCULATION_LINKS,
            'calc_names': CALCULATION_NAMES,
            'page_title': page_title,
            'sheetnumber': self.sheetnumber,
        }
        return render(request, enginesheet_template_path, context)

    def get(self, request):
        self.fill_defaults()
        self.fill_meta()
        return self.void_get(request)

    def post(self, request):
        self.fill_defaults()
        self.fill_meta()
        return self.void_post(request)
