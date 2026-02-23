import json

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Case, IntegerField, Q, Value, When
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.urls import reverse

from notifications.models import Notification

from .forms import BAYAWAN_BARANGAYS, PublicReportForm, StaffReportUpdateForm
from .models import Report
from users.decorators import role_required, verified_required
from users.models import CustomUser


def public_report(request):
    form = PublicReportForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        report = form.save(commit=False)
        if request.user.is_authenticated:
            report.reported_by = request.user
        report.save()
        messages.success(request, 'Report submitted. Thank you.')
        return redirect('reports_public')
    report_type_choices = [(choice[0].lower(), choice[1]) for choice in Report.ReportType.choices]
    return render(
        request,
        'reports/public_report.html',
        {
            'form': form,
            'report_type_choices': report_type_choices,
            'barangay_options': BAYAWAN_BARANGAYS,
            'google_maps_api_key': getattr(settings, 'GOOGLE_MAPS_API_KEY', ''),
        },
    )


@login_required
@role_required('ADMIN', 'STAFF')
def staff_list(request):
    reports = (
        Report.objects.annotate(
            is_completed=Case(
                When(
                    status__in=(Report.Status.RESOLVED, Report.Status.CLOSED),
                    then=Value(1),
                ),
                default=Value(0),
                output_field=IntegerField(),
            )
        )
        .order_by('is_completed', '-created_at')
    )
    return render(request, 'reports/staff_list.html', {'reports': reports})


@login_required
@role_required('ADMIN', 'STAFF')
def staff_detail(request, pk: int):
    report = get_object_or_404(Report, pk=pk)
    form = StaffReportUpdateForm(instance=report)
    return render(request, 'reports/staff_detail.html', {'report': report, 'form': form})


@login_required
@role_required('ADMIN', 'STAFF')
def update_status(request, pk: int):
    report = get_object_or_404(Report, pk=pk)
    action = request.POST.get('action')
    form = StaffReportUpdateForm(request.POST or None, instance=report)
    if request.method == 'POST':
        previous_status = report.status
        if action == 'captured':
            report.status = Report.Status.RESOLVED
            report.notes = (report.notes + "\n" if report.notes else "") + "Marked captured by staff."
            report.save(update_fields=['status', 'notes'])
        elif form.is_valid():
            form.save()
        else:
            messages.error(request, 'Please correct the form errors.')
            context = {'report': report, 'form': form}
            return render(request, 'reports/staff_detail.html', context)

        if report.reported_by and previous_status != report.status:
            Notification.objects.create(
                user=report.reported_by,
                title='Report Status Update',
                message=f'Your report #{report.id} is now {report.get_status_display()}.',
                action_url=reverse('reports_public_list'),
            )
        messages.success(request, 'Report updated.')
    return redirect('reports_staff_detail', pk=report.id)


def public_list(request):
    reports_qs = Report.objects.all()
    total_reports = reports_qs.count()

    query = (request.GET.get('q') or '').strip()
    status = (request.GET.get('status') or '').strip().upper()
    report_type = (request.GET.get('report_type') or '').strip().upper()
    mine_only = request.GET.get('mine') == '1'

    if query:
        filters = Q(location__icontains=query) | Q(description__icontains=query)
        try:
            query_id = int(query)
        except ValueError:
            query_id = None
        if query_id is not None:
            filters |= Q(id=query_id)
        reports_qs = reports_qs.filter(filters)

    valid_statuses = {choice[0] for choice in Report.Status.choices}
    if status in valid_statuses:
        reports_qs = reports_qs.filter(status=status)
    else:
        status = ''

    valid_types = {choice[0] for choice in Report.ReportType.choices}
    if report_type in valid_types:
        reports_qs = reports_qs.filter(report_type=report_type)
    else:
        report_type = ''

    if mine_only and request.user.is_authenticated:
        reports_qs = reports_qs.filter(reported_by=request.user)
    elif mine_only and not request.user.is_authenticated:
        mine_only = False

    reports = reports_qs.order_by('-created_at')
    filtered_count = reports.count()

    context = {
        'reports': reports,
        'total_reports': total_reports,
        'filtered_count': filtered_count,
        'status_choices': Report.Status.choices,
        'report_type_choices': Report.ReportType.choices,
        'filters': {
            'q': query,
            'status': status,
            'report_type': report_type,
            'mine': mine_only,
        },
    }
    return render(request, 'reports/public_list.html', context)


@require_POST
@verified_required
def public_delete(request, pk: int):
    report = get_object_or_404(Report, pk=pk)
    is_staff = request.user.role in (CustomUser.Roles.ADMIN, CustomUser.Roles.STAFF)
    if not is_staff and report.reported_by_id != request.user.id:
        messages.error(request, 'You can only delete your own reports.')
        return redirect('reports_public_list')

    if report.photo:
        report.photo.delete(save=False)
    report.delete()
    messages.success(request, 'Report deleted.')
    return redirect('reports_public_list')


def _parse_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _build_location_summary(address):
    parts = [
        address.get('street'),
        address.get('barangay'),
        address.get('city'),
        address.get('province'),
        address.get('postal_code'),
    ]
    summary = ', '.join([part for part in parts if part])
    if len(summary) > 255:
        return summary[:252] + '...'
    return summary


@require_POST
def api_reports(request):
    payload_raw = request.POST.get('payload')
    photo = request.FILES.get('photo') if payload_raw is not None else None
    if payload_raw is None:
        payload_raw = request.body or b'{}'
        if isinstance(payload_raw, bytes):
            payload_raw = payload_raw.decode('utf-8')
    try:
        payload = json.loads(payload_raw or '{}')
    except json.JSONDecodeError:
        return JsonResponse(
            {'success': False, 'errors': {'payload': 'Invalid JSON payload.'}},
            status=400,
        )

    errors = {}
    report_type_raw = (payload.get('report_type') or '').strip().upper()
    report_type_map = {
        'STRAY': Report.ReportType.STRAY,
        'INJURED': Report.ReportType.INJURED,
        'SURRENDER': Report.ReportType.SURRENDER,
        'DANGEROUS': Report.ReportType.DANGEROUS,
        'BITE_INCIDENT': Report.ReportType.BITE_INCIDENT,
        'BITE INCIDENT': Report.ReportType.BITE_INCIDENT,
        'BITE': Report.ReportType.BITE_INCIDENT,
        'ABANDONED': Report.ReportType.ABANDONED,
        'WELFARE': Report.ReportType.WELFARE,
        'NEGLECT': Report.ReportType.WELFARE,
        'OTHER': Report.ReportType.OTHER,
        'INCIDENT': Report.ReportType.DANGEROUS,
    }
    if not report_type_raw:
        errors['report_type'] = 'Report type is required.'
    elif report_type_raw not in report_type_map:
        errors['report_type'] = (
            'Report type must be stray, injured, surrender, dangerous, bite incident, '
            'abandoned, welfare, or other.'
        )

    description = (payload.get('description') or '').strip()
    if not description:
        errors['description'] = 'Description is required.'

    location_method_raw = (payload.get('location_method') or '').strip().lower()
    if location_method_raw not in ('both',):
        errors['location_method'] = 'Google Maps and manual address are both required.'

    location_payload = payload.get('location') if isinstance(payload.get('location'), dict) else {}
    contact_name = (payload.get('contact_name') or '').strip()
    contact_phone = (payload.get('contact_phone') or '').strip()
    contact_email = (payload.get('contact_email') or '').strip()

    latitude = None
    longitude = None
    maps_url = ''
    address = None

    latitude = _parse_float(location_payload.get('lat'))
    longitude = _parse_float(location_payload.get('lng'))
    if latitude is None or longitude is None:
        errors['google_maps'] = 'Latitude and longitude are required for Google Maps.'
    else:
        if not (-90 <= latitude <= 90):
            errors['latitude'] = 'Latitude must be between -90 and 90.'
        if not (-180 <= longitude <= 180):
            errors['longitude'] = 'Longitude must be between -180 and 180.'
    maps_url = (location_payload.get('maps_url') or '').strip()
    if not maps_url and latitude is not None and longitude is not None:
        maps_url = f'https://maps.google.com/?q={latitude},{longitude}'
    if not maps_url:
        errors['maps_url'] = 'Google Maps URL is required.'

    address = location_payload.get('address') if isinstance(location_payload.get('address'), dict) else {}
    if address and not address.get('barangay') and address.get('area'):
        address['barangay'] = address.get('area')
    if not address:
        errors['address'] = 'Address details are required.'
    else:
        required_fields = ('street', 'city', 'barangay')
        labels = {
            'street': 'Street address',
            'city': 'City',
            'barangay': 'Area / Neighborhood',
        }
        for field in required_fields:
            if not (address.get(field) or '').strip():
                errors[field] = f'{labels[field]} is required.'
    if not contact_name:
        errors['full_name'] = 'Full name is required for manual address.'
    if not contact_phone:
        errors['contact_phone'] = 'Phone number is required.'
    if contact_email:
        try:
            validate_email(contact_email)
        except ValidationError:
            errors['contact_email'] = 'Email address is invalid.'

    if errors:
        return JsonResponse({'success': False, 'errors': errors}, status=400)

    location_method_value = Report.LocationMethod.BOTH
    report_type_value = report_type_map[report_type_raw]

    location_summary = _build_location_summary(address)

    report = Report.objects.create(
        report_type=report_type_value,
        reported_by=request.user if request.user.is_authenticated else None,
        location=location_summary,
        photo=photo,
        description=description,
        contact_name=contact_name,
        contact_phone=contact_phone,
        contact_email=contact_email,
        location_method=location_method_value,
        latitude=latitude,
        longitude=longitude,
        maps_url=maps_url,
        address_json=address,
    )

    return JsonResponse({'success': True, 'report_id': report.id}, status=201)
