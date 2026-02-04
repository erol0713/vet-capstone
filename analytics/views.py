from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from django.shortcuts import render
from django.utils import timezone

from users.decorators import role_required

from adoption.models import AdoptionReservation, ReclaimRequest
from dogs.models import Dog
from penalties.models import PenaltyCase
from reports.models import Report
from vaccinations.models import VaccinationRecord


@login_required
@role_required('ADMIN', 'STAFF')
def dashboard(request):
    today = timezone.localdate()
    month_start = today.replace(day=1)

    captures_month = Dog.objects.filter(capture_datetime__date__gte=month_start).count()
    adoptions_month = AdoptionReservation.objects.filter(
        created_at__date__gte=month_start, status=AdoptionReservation.Status.COMPLETED
    ).count()
    reclaims_month = ReclaimRequest.objects.filter(
        created_at__date__gte=month_start, status=ReclaimRequest.Status.COMPLETED
    ).count()
    reports_month = Report.objects.filter(created_at__date__gte=month_start).count()

    revenue = (
        PenaltyCase.objects.filter(is_finalized=True)
        .aggregate(total=Sum('total_amount'))
        .get('total')
        or 0
    )

    barangay_counts = (
        Dog.objects.exclude(barangay='')
        .values('barangay')
        .annotate(count=Count('id'))
        .order_by('-count')[:5]
    )

    context = {
        'captures_month': captures_month,
        'adoptions_month': adoptions_month,
        'reclaims_month': reclaims_month,
        'reports_month': reports_month,
        'revenue_total': revenue,
        'barangay_counts': barangay_counts,
        'vaccinations_total': VaccinationRecord.objects.count(),
    }
    return render(request, 'analytics/dashboard.html', context)
