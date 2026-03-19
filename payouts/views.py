from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.template.response import TemplateResponse
from .models import Payout
from sellers.models import Seller


@login_required(login_url='/users/login')
def payout_list(request):
    if not hasattr(request.user, 'seller'):
        return redirect('sellers:register')
    seller = request.user.seller
    payouts = seller.payouts.order_by('-created_at')
    return TemplateResponse(request, 'payouts/list.html', {
        'seller': seller,
        'payouts': payouts,
    })


@login_required(login_url='/users/login')
def request_payout(request):
    if not hasattr(request.user, 'seller'):
        return redirect('sellers:register')

    seller = request.user.seller

    if request.method == 'POST':
        amount = request.POST.get('amount')
        if not amount:
            messages.error(request, 'Please enter an amount.')
            return redirect('payouts:list')

        amount = float(amount)
        if amount > float(seller.balance):
            messages.error(request, 'Insufficient balance.')
            return redirect('payouts:list')

        Payout.objects.create(
            seller=seller,
            amount=amount,
            payment_method=request.POST.get('payment_method', ''),
        )
        seller.balance -= amount  # ← резервируем сумму
        seller.save()
        messages.success(request, f'Payout request of €{amount} submitted.')

    return redirect('payouts:list')