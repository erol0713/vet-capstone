from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.db import models, transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from users.decorators import role_required

from .models import PenaltyCase, PenaltyChecklistItem, PenaltyLineItem

LODGING_CODE = 'S28_2_LODGING_DAILY'

@login_required
@role_required('ADMIN', 'STAFF')
def checklist(request):
    items = PenaltyChecklistItem.objects.filter(is_active=True).order_by('section', 'description')
    items_by_code = {item.code: item for item in items}
    lodging_item = items_by_code.get(LODGING_CODE)
    case_id = request.GET.get('case')
    query = request.GET.get('q', '').strip()
    case = None
    if case_id:
        case = PenaltyCase.objects.filter(id=case_id).first()
    cases = PenaltyCase.objects.select_related('dog', 'owner').order_by('-created_at')
    if query:
        search_filter = models.Q(owner__email__icontains=query) | models.Q(
            dog__name__icontains=query
        )
        if query.isdigit():
            search_filter |= models.Q(id=int(query))
        cases = cases.filter(search_filter)

    if request.method == 'POST':
        action = request.POST.get('action')
        post_case_id = request.POST.get('case_id') or case_id
        if post_case_id:
            case = PenaltyCase.objects.filter(id=post_case_id).first()
        if action == 'save':
            if not case:
                messages.error(request, 'Select a penalty case first.')
                return redirect('penalties_checklist')
            if case.is_finalized:
                messages.error(request, 'This penalty case is finalized and locked.')
                return redirect('penalties_checklist')

            selected_codes = request.POST.getlist('items')
            with transaction.atomic():
                PenaltyLineItem.objects.filter(case=case).delete()
                total = Decimal('0.00')
                for code in selected_codes:
                    item = items_by_code.get(code)
                    if not item:
                        continue
                    if code == LODGING_CODE:
                        continue
                    line = PenaltyLineItem.objects.create(
                        case=case,
                        checklist_item=item,
                        description=item.description,
                        quantity=1,
                        unit_amount=item.default_amount,
                        total=item.default_amount,
                    )
                    total += line.total
                case.total_amount = total
                case.save(update_fields=['total_amount'])
                messages.success(request, 'Penalty checklist saved.')

        if action == 'finalize':
            if not case:
                messages.error(request, 'Select a penalty case first.')
                return redirect('penalties_checklist')
            if case.is_finalized:
                messages.error(request, 'Penalty case already finalized.')
                return redirect('penalties_checklist')
            case.is_finalized = True
            case.finalized_at = timezone.now()
            case.locked_by = request.user
            case.save(update_fields=['is_finalized', 'finalized_at', 'locked_by'])
            messages.success(request, 'Penalty case finalized and locked.')

        return redirect(f"{request.path}?case={case.id}" if case else request.path)

    selected_codes = set()
    lodging_days = 0
    lodging_rate = lodging_item.default_amount if lodging_item else Decimal('200.00')
    lodging_selected = False
    checklist_total = Decimal('0.00')
    grand_total = Decimal('0.00')
    if case:
        checklist_items = {item.id: item for item in items}
        for line in case.line_items.all():
            match = checklist_items.get(line.checklist_item_id)
            if match:
                selected_codes.add(match.code)
                if match.code == LODGING_CODE:
                    lodging_rate = line.unit_amount
                    lodging_days = line.quantity
                    lodging_selected = True
                else:
                    checklist_total += line.total
            if line.description == 'Lodging Fee':
                lodging_rate = line.unit_amount
                lodging_days = line.quantity
                lodging_selected = True
        if lodging_selected and lodging_item:
            selected_codes.add(LODGING_CODE)
        grand_total = checklist_total

    context = {
        'items': items,
        'case': case,
        'cases': cases,
        'query': query,
        'selected_codes': selected_codes,
        'lodging_days': lodging_days,
        'lodging_rate': lodging_rate,
        'lodging_code': LODGING_CODE,
        'checklist_total': checklist_total,
        'grand_total': grand_total,
    }
    return render(request, 'penalties/checklist.html', context)


@login_required
@role_required('ADMIN', 'STAFF')
def receipt(request, case_id):
    case = get_object_or_404(
        PenaltyCase.objects.select_related('dog', 'owner', 'owner__profile'),
        id=case_id,
    )
    line_items = case.line_items.select_related('checklist_item').order_by('created_at', 'id')
    try:
        owner_profile = case.owner.profile
    except ObjectDoesNotExist:
        owner_profile = None
    owner_name = (
        owner_profile.full_name
        if owner_profile and owner_profile.full_name
        else case.owner.get_full_name() or case.owner.username
    )
    issued_at = case.finalized_at or timezone.now()

    context = {
        'case': case,
        'line_items': line_items,
        'owner_name': owner_name,
        'owner_profile': owner_profile,
        'issued_at': issued_at,
    }
    return render(request, 'penalties/receipt.html', context)
