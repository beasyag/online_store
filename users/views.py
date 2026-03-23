from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie
from django.urls import reverse
from django.http import HttpResponse
from django.template.response import TemplateResponse
from .forms import CustomUserCreationForm, CustomUserLoginForm, CustomUserUpdateForm, AddressForm, \
    CustomPasswordChangeForm, ProfileForm
from .models import CustomUser, Address
from django.contrib import messages
from main.models import Product
from orders.models import Order


@ensure_csrf_cookie
def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            if request.headers.get('HX-Request'):
                return HttpResponse(headers={'HX-Redirect': reverse('main:index')})
            return redirect('main:index')
        if request.headers.get('HX-Request'):
            return TemplateResponse(request, 'users/register.html', {'form': form})
        return render(request, 'users/register_page.html', {'form': form})  # ← полная страница

    form = CustomUserCreationForm()
    if request.headers.get('HX-Request'):
        return TemplateResponse(request, 'users/register.html', {'form': form})
    return render(request, 'users/register_page.html', {'form': form})  # ← полная страница


@ensure_csrf_cookie
def login_view(request):
    if request.method == 'POST':
        form = CustomUserLoginForm(request=request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if request.headers.get('HX-Request'):
                return HttpResponse(headers={'HX-Redirect': reverse('main:index')})
            return redirect('main:index')
        messages.error(request, 'Invalid email or password')
        if request.headers.get('HX-Request'):
            return TemplateResponse(request, 'users/login.html', {'form': form})
        return render(request, 'users/login_page.html', {'form': form})  # ← полная страница

    form = CustomUserLoginForm()
    if request.headers.get('HX-Request'):
        return TemplateResponse(request, 'users/login.html', {'form': form})
    return render(request, 'users/login_page.html', {'form': form})  # ← полная страница


@login_required(login_url='/users/login')
def profile_view(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated.')
            if request.headers.get('HX-Request'):
                return HttpResponse(headers={'HX-Redirect': reverse('users:profile')})
            return redirect('users:profile')
    else:
        form = ProfileForm(instance=request.user)

    context = {'form': form}

    if request.method == 'GET' and request.headers.get('HX-Request'):
        return HttpResponse(headers={'HX-Redirect': reverse('users:profile')})
    # Всегда полная страница: профиль отдельный от других разделов.
    return TemplateResponse(request, 'users/profile_content.html', context)

@login_required(login_url='/users/login')
def change_password(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Password changed successfully.')
            if request.headers.get('HX-Request'):
                return HttpResponse(headers={'HX-Redirect': reverse('users:profile')})
            return redirect('users:profile')
    else:
        form = CustomPasswordChangeForm(request.user)

    context = {'form': form}

    if request.method == 'GET' and request.headers.get('HX-Request'):
        return HttpResponse(headers={'HX-Redirect': reverse('users:change_password')})
    # Всегда полная страница: смена пароля открывается отдельно.
    return TemplateResponse(request, 'users/change_password_page.html', context)

@login_required(login_url='/users/login')
def account_details(request):
    # ← request.user вместо лишнего запроса к БД
    return TemplateResponse(
        request,
        'users/partials/account_details.html',
        {'user': request.user}
    )


@login_required(login_url='/users/login')
def edit_account_details(request):
    form = CustomUserUpdateForm(instance=request.user)
    return TemplateResponse(
        request,
        'users/partials/edit_account_details.html',
        {'user': request.user, 'form': form}
    )


@login_required(login_url='/users/login')
def update_account_details(request):
    if request.method != 'POST':
        return redirect('users:profile')

    form = CustomUserUpdateForm(request.POST, instance=request.user)
    if form.is_valid():
        user = form.save(commit=False)
        user.clean()
        user.save()
        # ← обновляем request.user из БД
        request.user = CustomUser.objects.get(id=user.id)
        return TemplateResponse(
            request,
            'users/partials/account_details.html',
            {'user': request.user}
        )

    return TemplateResponse(
        request,
        'users/partials/edit_account_details.html',
        {'user': request.user, 'form': form}
    )


def logout_view(request):
    logout(request)
    if request.headers.get('HX-Request'):
        return HttpResponse(headers={'HX-Redirect': reverse('main:index')})
    return redirect('main:index')

@login_required(login_url='/users/login')
def order_history(request):
    orders = Order.objects.filter(
        user=request.user
    ).order_by('-created_at').prefetch_related('items')
    context = {'orders': orders}

    if request.method == 'GET' and request.headers.get('HX-Request'):
        return HttpResponse(headers={'HX-Redirect': reverse('users:order_history')})
    # Всегда полная страница: история заказов отдельная.
    return TemplateResponse(request, 'users/order_history_page.html', context)


@login_required(login_url='/users/login')
def order_detail(request, order_id):
    order = get_object_or_404(
        Order.objects.prefetch_related('items__product'),
        id=order_id,
        user=request.user
    )

    context = {'order': order}

    if request.method == 'GET' and request.headers.get('HX-Request'):
        return HttpResponse(headers={'HX-Redirect': reverse('users:order_detail', kwargs={'order_id': order_id})})
    # Всегда полная страница: детали заказа отдельные.
    return TemplateResponse(request, 'users/order_detail_page.html', context)  # ← полная страница

@login_required(login_url='/users/login')
def addresses_view(request):
    addresses = Address.objects.filter(
        user=request.user
    ).order_by('-is_default', '-created_at')
    context = {'addresses': addresses}

    if request.method == 'GET' and request.headers.get('HX-Request'):
        return HttpResponse(headers={'HX-Redirect': reverse('users:addresses')})
    # Всегда полная страница: адреса отдельные.
    return TemplateResponse(request, 'users/addresses_page.html', context)

@login_required(login_url='/users/login')
def address_add(request):
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()
            if request.headers.get('HX-Request'):
                return HttpResponse(headers={'HX-Redirect': reverse('users:addresses')})
            return redirect('users:addresses')
    else:
        form = AddressForm()

    context = {'form': form, 'action': 'Add'}
    if request.method == 'GET' and request.headers.get('HX-Request'):
        return HttpResponse(headers={'HX-Redirect': reverse('users:address_add')})
    # Всегда полная страница: форма адреса отдельная.
    return TemplateResponse(request, 'users/address_form_page.html', context)


@login_required(login_url='/users/login')
def address_edit(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    if request.method == 'POST':
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            if request.headers.get('HX-Request'):
                return HttpResponse(headers={'HX-Redirect': reverse('users:addresses')})
            return redirect('users:addresses')
    else:
        form = AddressForm(instance=address)

    context = {'form': form, 'action': 'Edit', 'address': address}
    if request.method == 'GET' and request.headers.get('HX-Request'):
        return HttpResponse(headers={'HX-Redirect': reverse('users:address_edit', kwargs={'pk': pk})})
    # Всегда полная страница: форма редактирования адреса отдельная.
    return TemplateResponse(request, 'users/address_form_page.html', context)


@login_required(login_url='/users/login')
def address_delete(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    if request.method == 'POST':
        address.delete()
        if request.headers.get('HX-Request'):
            return HttpResponse(headers={'HX-Redirect': reverse('users:addresses')})
        return redirect('users:addresses')
    return redirect('users:addresses')