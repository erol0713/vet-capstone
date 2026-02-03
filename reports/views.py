from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from notifications.models import Notification

from .forms import PublicReportForm, StaffReportUpdateForm
from .models import Report
from users.decorators import role_required


def public_report(request):
    form = PublicReportForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        report = form.save(commit=False)
        if request.user.is_authenticated:
            report.reported_by = request.user
        report.save()
        messages.success(request, 'Report submitted. Thank you.')
        return redirect('reports_public')
    return render(request, 'reports/public_report.html', {'form': form})


@login_required
@role_required('ADMIN', 'STAFF')
def staff_list(request):
    reports = Report.objects.order_by('-created_at')
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
            return redirect('reports_staff_detail', pk=report.id)

        if report.reported_by and previous_status != report.status:
            Notification.objects.create(
                user=report.reported_by,
                title='Report Status Update',
                message=f'Your report #{report.id} is now {report.get_status_display()}.',
            )
        messages.success(request, 'Report updated.')
    return redirect('reports_staff_detail', pk=report.id)


def public_list(request):
    reports = Report.objects.order_by('-created_at')
    return render(request, 'reports/public_list.html', {'reports': reports})
