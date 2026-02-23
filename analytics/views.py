from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.shortcuts import render
from django.utils import timezone
from django.utils.dateparse import parse_date

from users.decorators import role_required

from adoption.models import AdoptionReservation, ReclaimRequest
from dogs.models import Dog
from penalties.models import PenaltyCase
from reports.models import Report
from vaccinations.models import VaccinationRecord


def shift_month(value, offset):
    month_index = (value.month - 1) + offset
    year = value.year + (month_index // 12)
    month = (month_index % 12) + 1
    return value.replace(year=year, month=month)


def get_default_date_range(today):
    end = today
    start = shift_month(today.replace(day=1), -5)
    return start, end


def get_date_range(request):
    today = timezone.localdate()
    default_start, default_end = get_default_date_range(today)
    raw_start = request.GET.get('start')
    raw_end = request.GET.get('end')

    start = parse_date(raw_start) if isinstance(raw_start, str) and raw_start else None
    end = parse_date(raw_end) if isinstance(raw_end, str) and raw_end else None

    start = start or default_start
    end = end or default_end

    if start > end:
        start, end = end, start

    return start, end


def format_date_range(start, end):
    if start == end:
        return start.strftime('%b %d, %Y')
    if start.year == end.year:
        if start.month == end.month:
            return f"{start.strftime('%b %d')} - {end.strftime('%d, %Y')}"
        return f"{start.strftime('%b %d')} - {end.strftime('%b %d, %Y')}"
    return f"{start.strftime('%b %d, %Y')} - {end.strftime('%b %d, %Y')}"


def build_month_labels(start, end):
    months = []
    current = start.replace(day=1)
    last = end.replace(day=1)
    while current <= last:
        months.append(current)
        current = shift_month(current, 1)
    include_year = len({month.year for month in months}) > 1
    labels = [
        month.strftime('%b %Y') if include_year else month.strftime('%b') for month in months
    ]
    return months, labels


@login_required
@role_required('ADMIN', 'STAFF')
def dashboard(request):
    today = timezone.localdate()
    range_start, range_end = get_date_range(request)

    captures_range = Dog.objects.filter(
        capture_datetime__date__range=(range_start, range_end)
    ).count()
    adoptions_range = AdoptionReservation.objects.filter(
        created_at__date__range=(range_start, range_end),
        status=AdoptionReservation.Status.COMPLETED,
    ).count()
    reclaims_range = ReclaimRequest.objects.filter(
        created_at__date__range=(range_start, range_end),
        status=ReclaimRequest.Status.COMPLETED,
    ).count()
    reports_range = Report.objects.filter(
        created_at__date__range=(range_start, range_end)
    ).count()

    revenue = (
        PenaltyCase.objects.filter(
            is_finalized=True, finalized_at__date__range=(range_start, range_end)
        )
        .aggregate(total=Sum('total_amount'))
        .get('total')
        or 0
    )

    barangay_counts = (
        Dog.objects.filter(capture_datetime__date__range=(range_start, range_end))
        .exclude(barangay='')
        .values('barangay')
        .annotate(count=Count('id'))
        .order_by('-count')[:5]
    )

    months, month_labels = build_month_labels(range_start, range_end)
    capture_monthly = (
        Dog.objects.filter(capture_datetime__date__range=(range_start, range_end))
        .annotate(month=TruncMonth('capture_datetime'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )
    capture_lookup = {item['month'].date(): item['count'] for item in capture_monthly}
    capture_series = [capture_lookup.get(month, 0) for month in months]

    chart_data = {
        'captures': {'labels': month_labels, 'data': capture_series},
        'adoption_vs_reclaim': {
            'labels': ['Adopted', 'Reclaimed'],
            'data': [adoptions_range, reclaims_range],
        },
    }

    context = {
        'captures_range': captures_range,
        'adoptions_range': adoptions_range,
        'reclaims_range': reclaims_range,
        'reports_range': reports_range,
        'revenue_total': revenue,
        'barangay_counts': barangay_counts,
        'vaccinations_total': VaccinationRecord.objects.filter(
            vaccinated_date__range=(range_start, range_end)
        ).count(),
        'today': today,
        'range_start': range_start,
        'range_end': range_end,
        'range_label': format_date_range(range_start, range_end),
        'chart_data': chart_data,
    }
    return render(request, 'analytics/dashboard.html', context)
