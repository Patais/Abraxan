import codecs
import csv
import datetime

from django.apps import apps
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Permission
from django.db import IntegrityError
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.datastructures import MultiValueDictKeyError

from nifleur.forms import DisciplineForm, SpeakerForm, ContractRequestForm, PerformanceForm, SchoolYearForm, \
    SchoolForm, RecruitmentTypeForm, RateTypeForm, CompanyTypeForm, UnitForm, RegisterForm, LegalStructureForm, \
    SchoolYearDetailForm, CompanyForm
from nifleur.models import ContractRequest, Speaker, Discipline, School, Performance, SchoolYear, Status, \
    RecruitmentType, RateType, CompanyType, Unit, LegalStructure, Company, STATUS_CHOICES, CLOSE
from nifleur.utils import export_csv, short_datetime


@login_required
def home(request):
    contract_count = ContractRequest.objects.count()
    today = datetime.date.today()
    today_contract_count = ContractRequest.objects.filter(created_at__gt=today).count()
    form = RegisterForm(request.POST or None, instance=request.user)

    if form.is_valid():
        form.save()
        messages.success(request, "Vous venez de modifier vos informations")

    return render(request, 'nifleur/home.html', {
        'contract_count': contract_count,
        'today_contract_count': today_contract_count,
        'form': form
    })


def login_user(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect(home)
        else:
            messages.error(request, 'Utilisateur ou mot de passe incorrect')
            return redirect(login_user)

    return render(request, 'nifleur/login.html')


def logout_user(request):
    logout(request)
    messages.success(request, "Vous avez bien été déconnecté")
    return redirect(login_user)


@login_required
def import_data(request, file, model, status=False):
    django_model = apps.get_model(app_label='nifleur', model_name=model)
    csv_reader = csv.reader(codecs.iterdecode(file, 'utf-8'), delimiter=';')
    for row in csv_reader:
        try:
            name = row[0]
            if status:
                color = row[2] if row[2][0] == '#' else f'#{row[2]}'
                s_type = row[3]
                status_type = None
                for index, l_type in enumerate(STATUS_CHOICES):
                    if s_type == l_type[0]:
                        status_type = s_type
                        break
                    elif s_type == l_type[1]:
                        status_type = STATUS_CHOICES[index][0]
                        break
                if not s_type:
                    messages.error(request, f"Le statut {name} contient un type erroné : {s_type}")
                    continue
                django_model.objects.create(label=name, position=row[1], color=color, type=status_type)
            else:
                django_model.objects.create(label=name)
        except IntegrityError as e:
            if request.user.is_superuser:
                messages.error(request, e)
            else:
                messages.error(request, f"La donnée nommée {row[0]} existe déjà")
    return messages.info(request, f"Des données on été importées")


@login_required
def parameters(request):
    # models data
    performances = Performance.objects.all().order_by('label')
    status = Status.objects.all().order_by('position')
    recruitment_types = RecruitmentType.objects.all()
    rate_types = RateType.objects.all()
    company_types = CompanyType.objects.all()
    units = Unit.objects.all()
    legal_structures = LegalStructure.objects.all()
    users = User.objects.all()

    # Forms
    performance_form = PerformanceForm(request.POST or None, prefix='performance-form')
    recruitment_type_form = RecruitmentTypeForm(request.POST or None, prefix='recruitment_typ-form')
    rate_type_form = RateTypeForm(request.POST or None, prefix='rate_type-form')
    company_type_form = CompanyTypeForm(request.POST or None, prefix='company_type-form')
    unit_form = UnitForm(request.POST or None, prefix='unit-form')
    user_form = RegisterForm(request.POST or None, prefix='user-form')
    legal_structure_form = LegalStructureForm(request.POST or None, prefix='legal-structure-form')

    if performance_form.is_valid():
        performance_form.save()
        messages.success(request, "Une nouvelle performance a bien été créée")
        return redirect(parameters)

    if recruitment_type_form.is_valid():
        recruitment_type_form.save()
        messages.success(request, "Un nouveau type de recrutement a bien été créé")
        return redirect(parameters)

    if rate_type_form.is_valid():
        rate_type_form.save()
        messages.success(request, "Un nouveau type de tarif a bien été créé")
        return redirect(parameters)

    if company_type_form.is_valid():
        company_type_form.save()
        messages.success(request, "Un nouveau type de société a bien été créé")
        return redirect(parameters)

    if unit_form.is_valid():
        unit_form.save()
        messages.success(request, "Une nouvelle unité a bien été créée")
        return redirect(parameters)

    if legal_structure_form.is_valid():
        legal_structure_form.save()
        messages.success(request, "Une nouvelle structure juridique a bien été créée")
        return redirect(parameters)

    if user_form.is_valid():
        user_form.save()
        messages.success(request, "Une nouvel utilisateur a bien été créé")
        return redirect(parameters)

    if request.method == 'POST':
        try:
            performance_csv = request.FILES['performance_csv']
        except MultiValueDictKeyError:
            performance_csv = None

        try:
            recruitment_type_csv = request.FILES['recruitment_type_csv']
        except MultiValueDictKeyError:
            recruitment_type_csv = None

        try:
            rate_type_csv = request.FILES['rate_type_csv']
        except MultiValueDictKeyError:
            rate_type_csv = None

        try:
            company_type_csv = request.FILES['company_type_csv']
        except MultiValueDictKeyError:
            company_type_csv = None

        try:
            unit_csv = request.FILES['unit_csv']
        except MultiValueDictKeyError:
            unit_csv = None

        try:
            status_csv = request.FILES['status_csv']
        except MultiValueDictKeyError:
            status_csv = None

        try:
            legal_structure_csv = request.FILES['legal_structure_csv']
        except MultiValueDictKeyError:
            legal_structure_csv = None

        if performance_csv:
            import_data(request, performance_csv, 'Performance')
        elif recruitment_type_csv:
            import_data(request, recruitment_type_csv, 'RecruitmentType')
        elif rate_type_csv:
            import_data(request, rate_type_csv, 'RateType')
        elif company_type_csv:
            import_data(request, company_type_csv, 'CompanyType')
        elif unit_csv:
            import_data(request, unit_csv, 'Unit')
        elif legal_structure_csv:
            import_data(request, legal_structure_csv, 'LegalStructure')
        elif status_csv:
            import_data(request, status_csv, 'Status', True)

    return render(request, 'nifleur/parameters.html', {
        'performances': performances,
        'status': status,
        'recruitment_types': recruitment_types,
        'rate_types': rate_types,
        'company_types': company_types,
        'units': units,
        'legal_structures': legal_structures,
        'users': users,
        'performance_form': performance_form,
        'recruitment_type_form': recruitment_type_form,
        'rate_type_form': rate_type_form,
        'company_type_form': company_type_form,
        'unit_form': unit_form,
        'legal_structure_form': legal_structure_form,
        'user_form': user_form
    })


@login_required
def delete_model_object(request, model, object_id):
    django_model = apps.get_model(app_label='nifleur', model_name=model)
    model_object = get_object_or_404(django_model, id=object_id)
    model_object.delete()
    return JsonResponse({'success': True})


@login_required
def edit_simple_form(request, model, object_id):
    django_model = apps.get_model(app_label='nifleur', model_name=model)
    model_object = get_object_or_404(django_model, id=object_id)
    all_forms = [PerformanceForm, RecruitmentTypeForm, RateTypeForm, CompanyTypeForm, UnitForm, LegalStructureForm]
    form = None
    for value in all_forms:
        if model in str(value):
            form = value

    if form:
        form = form(request.POST or None, instance=model_object)
        if form.is_valid():
            form.save()
            messages.success(request, "Les données ont bien été mise à jour")
            return redirect(parameters)
        return render(request, 'nifleur/edit_simple_form.html', {'form': form, 'title': model_object.get_verbose_name})
    else:
        messages.error(request, "Une erreur est survenue lors de la recherche du formulaire")
        return redirect(parameters)


@login_required
def contract_requests_list(request):
    contract_requests = ContractRequest.objects.all()
    return render(request, 'nifleur/contract_requests.html', {'contract_requests': contract_requests})


@login_required
def contract_request_detail(request, contract_id):
    contract = get_object_or_404(ContractRequest, id=contract_id)
    status = Status.objects.all().order_by('position')
    return render(request, 'nifleur/contract_request_details.html', {
        'contract': contract,
        'status': status
    })


@login_required
def change_contract_status(request, contract_id, action):
    contract = get_object_or_404(ContractRequest, id=contract_id)
    if action == 'reset':
        status = Status.objects.get(position=1)
        contract.status = status
        contract.save()
    elif action == 'back' and contract.status.can_back:
        status = Status.objects.get(position=contract.status.position - 1)
        contract.status = status
        contract.save()
    elif action == 'next' and contract.status.can_next:
        status = Status.objects.get(position=contract.status.position + 1)
        contract.status = status
        contract.save()
    elif action == 'finish':
        status = Status.objects.filter(type=CLOSE).first()
        contract.status = status
        contract.save()
    elif action == 'cancel':
        status = Status.objects.filter(type=CLOSE).last()
        contract.status = status
        contract.save()
    else:
        messages.error(request, "Une erreur est survenue")
    return redirect(contract_request_detail, contract_id)


@login_required
def create_contract_request(request):
    form = ContractRequestForm(request.POST or None)
    if form.is_valid():
        contract_request = form.save(commit=False)
        contract_request.company = contract_request.speaker.company
        contract_request.save()
        discipline = get_object_or_404(Discipline, id=contract_request.discipline.id)
        discipline.speaker = contract_request.speaker
        discipline.save()
        messages.success(request, "La demande de contrat a bien été créée")
        return redirect(contract_request_detail, contract_request.id)
    return render(request, 'nifleur/contract_request_form.html', {'form': form})


@login_required
def export_contract_requests(request):
    contract_requests = ContractRequest.objects.all()
    data = [[
        'Date Demande', 'Marque / Ecole', 'Civilité', 'Nom', 'Prénom', 'Type société', 'Société', 'Commentaire',
        'Status contrat', 'Type de mission', 'Tarif a appliquer', 'TTC/SST', 'Horaire ou forfait', 'Volume horaire',
        'Unité', 'Date début', 'Date fin', 'Matière', 'Promotion', 'Alternant/Initial', 'Période', 'RP', 'Téléphone',
        'Mail', 'Type de recrutement', 'Intitulé du diplôme le plus élevé', 'Domaine de compétence principal',
        'Domaine de compétence 2', 'Domaine de compétence 3', "Niveau d'expertise en pédagogie",
        "Niveau d'expertise matière professionnelle"
    ]]
    for contract in contract_requests:
        ttc = 'TTC' if contract.ttc else 'SST'
        alternating = 'Alternant' if contract.alternating else 'Initial'
        if contract.speaker.company:
            company = contract.speaker.company.label
            company_type = contract.speaker.company.company_type
        else:
            company = ''
            company_type = ''
        data.append([
            short_datetime(contract.created_at), contract.school.label, contract.speaker.get_civility_display(),
            contract.speaker.last_name, contract.speaker.first_name, company_type, company, contract.comment,
            contract.status.label, contract.performance.label, contract.applied_rate, ttc, contract.rate_type.label,
            contract.hourly_volume, contract.unit.label, short_datetime(contract.started_at),
            short_datetime(contract.ended_at), contract.discipline.label, contract.school_year.year, alternating,
            contract.get_period_display(), contract.rp.get_full_name(), contract.speaker.phone_number,
            contract.speaker.mail, contract.recruitment_type.label, contract.speaker.highest_degree,
            contract.speaker.main_area_of_expertise, contract.speaker.second_area_of_expertise,
            contract.speaker.third_area_of_expertise, contract.speaker.get_teaching_expertise_level_display(),
            contract.get_professional_expertise_level_display()
        ])
    xls = request.GET.get('xls')
    return export_csv('demandes_de_contrat', data, True if xls else False)


@login_required
def speakers_list(request):
    speakers = Speaker.objects.all()
    edit_instance = request.GET.get('edit_instance', None)
    instance = Speaker.objects.get(id=edit_instance) if edit_instance else None
    form = SpeakerForm(request.POST or None, instance=instance)
    if form.is_valid():
        form.save()
        messages.success(
            request,
            f"L'intervenant {form.cleaned_data['first_name']} {form.cleaned_data['last_name']} a bien été "
            f"{'modifié' if instance else 'créé'}"
        )
        return redirect(speakers_list)

    return render(request, 'nifleur/speakers.html', {
        'speakers': speakers,
        'form': form,
        'edit_instance': edit_instance
    })


@login_required
def speaker_details(request, speaker_id):
    speaker = get_object_or_404(Speaker, id=speaker_id)
    campus = School.objects.filter(school_year__disciplines__speaker=speaker)
    data = dict()

    for school in campus.all():
        if school in data:
            data[school] += 1
        else:
            data[school] = 1
    morris_data = [({'label': m_data.label, 'value': data[m_data]}) for m_data in data]

    speaker_hours = 0
    for contract in speaker.contract_request_speaker.all():
        speaker_hours += contract.hourly_volume

    return render(request, 'nifleur/speaker_details.html', {
        'speaker': speaker,
        'morris_data': morris_data,
        'speaker_hours': speaker_hours
    })


@login_required
def speaker_form(request):
    form = SpeakerForm(request.POST or None)
    created = False
    if form.is_valid():
        form.save()
        created = True
        return redirect(speaker_form)

    return render(request, 'nifleur/add_speaker.html', {
        'form': form,
        'created': created
    })


@login_required
def discipline_list(request):
    disciplines = Discipline.objects.all().order_by('school_year')
    form = DisciplineForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(
            request,
            f"La matière {form.cleaned_data['label']} a bien été créée pour la classe {form.cleaned_data['school_year']}"
        )
        return redirect(discipline_list)

    return render(request, 'nifleur/disciplines.html', {
        'disciplines': disciplines,
        'form': form
    })


@login_required
def school_list(request):
    schools = School.objects.all()
    form = SchoolForm(request.POST or None, prefix='school-form')
    school_year_form = SchoolYearForm(request.POST or None, prefix='school-year-form')
    permissions = Permission.objects.filter(group__user=request.user)

    if permissions.filter(codename='add_school').exists() or request.user.is_staff:
        if form.is_valid():
            form.save()
            messages.success(request, f"L'école {form.cleaned_data['label']} a bien été créée")
            return redirect(school_list)
    else:
        messages.error(request, "Vous n'avez pas la permission d'ajouter des écoles")

    if permissions.filter(codename='add_schoolyear').exists() or request.user.is_staff:
        if school_year_form.is_valid():
            promotion = school_year_form.save()
            messages.success(request, f"La classe {promotion.year} {promotion.school} a bien été créée")
            return redirect(school_list)
    else:
        messages.error(request, "Vous n'avez pas la permission d'ajouter des promotions")

    if request.method == 'POST':
        try:
            school_csv = request.FILES['school_csv']
        except MultiValueDictKeyError:
            pass
        else:
            csv_reader = csv.reader(codecs.iterdecode(school_csv, 'utf-8'), delimiter=';')
            for row in csv_reader:
                try:
                    School.objects.create(label=row[0], full_name=row[1])
                except IntegrityError as e:
                    if request.user.is_superuser:
                        messages.error(request, e)
                    else:
                        messages.error(request, f"L'école {row[0]} existe déjà")
            messages.info(request, f"Des écoles ont été importées")

        try:
            school_year_csv = request.FILES['school_year_csv']
        except MultiValueDictKeyError:
            pass
        else:
            csv_reader = csv.reader(codecs.iterdecode(school_year_csv, 'utf-8'), delimiter=';')
            total_school_year = 0
            total_school_year_imported = 0
            for row in csv_reader:
                try:
                    school = get_object_or_404(School, label=row[0])
                    initial = True if row[3] in ('oui', '1') else False
                    alternating = True if row[4] in ('oui', '1') else False

                    if SchoolYear.objects.filter(year=row[1]).exists():
                        messages.error(request, f"La promotion {row[1]} existe déjà dans l'école {row[0]}")
                        continue

                    SchoolYear.objects.create(
                        school=school,
                        year=row[1],
                        label=row[2],
                        initial=initial,
                        alternating=alternating
                    )
                except IntegrityError as e:
                    if request.user.is_superuser:
                        messages.error(request, e)
                    else:
                        messages.error(
                            request,
                            f"Une erreur est survenue sur l'import de la promotion {row[1]} ({row[0]})"
                        )
                else:
                    total_school_year_imported += 1
                finally:
                    total_school_year += 1

            messages.info(request, f"{total_school_year_imported} promotions on été importée sur {total_school_year}")

    return render(request, 'nifleur/schools.html', {
        'schools': schools,
        'form': form,
        'school_year_form': school_year_form
    })


@login_required
def school_details(request, school_id):
    school = get_object_or_404(School, id=school_id)
    form = SchoolYearDetailForm(request.POST or None)

    if form.is_valid():
        school_year = form.save(commit=False)
        school_year.school = school
        school_year.save()
        messages.success(request, f"La promotion {school_year.year} vient d'être créée")
        return redirect(school_details, school_id)

    return render(request, 'nifleur/school_details.html', {
        'school': school,
        'form': form
    })


@login_required
def company_list(request):
    companies = Company.objects.all()
    form = CompanyForm(request.POST or None)
    if form.is_valid():
        company = form.save()
        messages.success(request, f"La société {company.label} vient d'être créée")
        return redirect(company_list)

    return render(request, 'nifleur/companies.html', {
        'companies': companies,
        'form': form
    })


@login_required
def company_details(request, company_id):
    company = get_object_or_404(Company, id=company_id)
    speakers = Speaker.objects.filter(company=company)
    contracts = ContractRequest.objects.filter(company=company)
    return render(request, 'nifleur/company_details.html', {
        'company': company,
        'speakers': speakers,
        'contracts': contracts
    })
