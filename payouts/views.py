from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.template.response import TemplateResponse
from .services import PayoutRequestError, create_payout_request


@login_required(login_url='/users/login')
def payout_list(request):
    if not request.user.can_access_seller_dashboard:
        return redirect('sellers:register')
    seller = request.user.seller
    payouts = seller.payouts.order_by('-created_at')
    return TemplateResponse(request, 'payouts/list.html', {
        'seller': seller,
        'payouts': payouts,
    })


@login_required(login_url='/users/login')
def request_payout(request):
    if not request.user.can_access_seller_dashboard:
        return redirect('sellers:register')

    seller = request.user.seller

    if request.method == 'POST':
        try:
            payout = create_payout_request(
                seller=seller,
                requested_by=request.user.email,
                raw_amount=(request.POST.get('amount') or '').strip(),
                payment_method=request.POST.get('payment_method', ''),
            )
            messages.success(request, f'Payout request of ${payout.amount} submitted.')
        except PayoutRequestError as exc:
            messages.error(request, str(exc))

    return redirect('payouts:list')
