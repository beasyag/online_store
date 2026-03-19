from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.http import HttpResponse
from django.template.response import TemplateResponse
from .forms import CustomUserCreationForm, CustomUserLoginForm, CustomUserUpdateForm
from .models import CustomUser
from django.contrib import messages
from main.models import Product
from orders.models import Order


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
        form = CustomUserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            if request.headers.get('HX-Request'):
                return HttpResponse(headers={'HX-Redirect': reverse('users:profile')})
            return redirect('users:profile')
    else:
        form = CustomUserUpdateForm(instance=request.user)

    recommended_products = Product.objects.all().order_by('id')[:3]
    context = {
        'form': form,
        'user': request.user,
        'recommended_products': recommended_products,
    }

    if request.headers.get('HX-Request'):
        return TemplateResponse(request, 'users/partials/profile_content.html', context)
    return TemplateResponse(request, 'users/profile_content.html', context)


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

    if request.headers.get('HX-Request'):
        return TemplateResponse(request, 'users/partials/order_history.html', context)
    return TemplateResponse(request, 'users/order_history_page.html', context)  # ← полная страница


@login_required(login_url='/users/login')
def order_detail(request, order_id):
    order = get_object_or_404(
        Order.objects.prefetch_related('items__product'),
        id=order_id,
        user=request.user
    )

    context = {'order': order}

    if request.headers.get('HX-Request'):
        return TemplateResponse(request, 'users/partials/order_detail.html', context)
    return TemplateResponse(request, 'users/order_detail_page.html', context)  # ← полная страница