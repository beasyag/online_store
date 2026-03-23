from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from django.contrib.auth import get_user_model, authenticate
from django.utils.html import strip_tags
from django.core.validators import RegexValidator

from users.models import Address, CustomUser

User = get_user_model()


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, max_length=254, widget=forms.EmailInput(attrs={'class': 'dotted-input w-full py-3 text-sm font-medium text-gray-900 placeholder-gray-500', 'placeholder': 'EMAIL'}))
    first_name = forms.CharField(required=True, max_length=50, widget=forms.TextInput(attrs={'class': 'dotted-input w-full py-3 text-sm font-medium text-gray-900 placeholder-gray-500', 'placeholder': 'FIRST NAME'}))
    last_name = forms.CharField(required=True, max_length=50, widget=forms.TextInput(attrs={'class': 'dotted-input w-full py-3 text-sm font-medium text-gray-900 placeholder-gray-500', 'placeholder': 'LAST NAME'}))
    password1 = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={'class': 'dotted-input w-full py-3 text-sm font-medium text-gray-900 placeholder-gray-500', 'placeholder': 'PASSWORD'})
    )
    password2 = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={'class': 'dotted-input w-full py-3 text-sm font-medium text-gray-900 placeholder-gray-500', 'placeholder': 'CONFIRM PASSWORD'})
    )

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Email already registered')
        return email
    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = None
        if commit:
            user.save()
        return user

class CustomUserLoginForm(AuthenticationForm):
    username = forms.CharField(label="Email", widget=forms.TextInput(attrs={'class': 'dotted-input w-full py-3 text-sm font-medium text-gray-900 placeholder-gray-500', 'placeholder': 'EMAIL'}))
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={'class': 'dotted-input w-full py-3 text-sm font-medium text-gray-900 placeholder-gray-500', 'placeholder': 'PASSWORD'})
    )

    def clean(self):
        email = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if email and password:
            self.user_cache = authenticate(self.request, email=email, password=password)
            if self.user_cache is None:
                raise forms.ValidationError('Invalid email or password')
            elif not self.user_cache.is_active:
                raise forms.ValidationError('This account is inactive')
        return self.cleaned_data


class CustomUserUpdateForm(forms.ModelForm):
    phone = forms.CharField(
        required=False,
        validators=[RegexValidator(r'^\+?1?\d{9,15}$', "Enter a valid phone number.")],
        widget=forms.TextInput(attrs={'class': 'dotted-input w-full py-3 text-sm font-medium text-gray-900 placeholder-gray-500', 'placeholder': 'PHONE NUMBER'})
    )
    first_name = forms.CharField(
        required=True,
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'dotted-input w-full py-3 text-sm font-medium text-gray-900 placeholder-gray-500', 'placeholder': 'FIRST NAME'})
    )
    last_name = forms.CharField(
        required=True,
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'dotted-input w-full py-3 text-sm font-medium text-gray-900 placeholder-gray-500', 'placeholder': 'LAST NAME'})
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={'class': 'dotted-input w-full py-3 text-sm font-medium text-gray-900 placeholder-gray-500', 'placeholder': 'EMAIL'})
    )

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'company', 'address1', 'address2', 'city', 'country', 'province', 'postal_code', 'phone')
        widgets = {
            'company': forms.TextInput(
                attrs={'class': 'dotted-input w-full py-3 text-sm font-medium text-gray-900 placeholder-gray-500',
                       'placeholder': 'COMPANY'}),
            'address1': forms.TextInput(
                attrs={'class': 'dotted-input w-full py-3 text-sm font-medium text-gray-900 placeholder-gray-500',
                       'placeholder': 'ADDRESS LINE 1'}),
            'address2': forms.TextInput(
                attrs={'class': 'dotted-input w-full py-3 text-sm font-medium text-gray-900 placeholder-gray-500',
                       'placeholder': 'ADDRESS LINE 2'}),
            'city': forms.TextInput(
                attrs={'class': 'dotted-input w-full py-3 text-sm font-medium text-gray-900 placeholder-gray-500',
                       'placeholder': 'CITY'}),
            'country': forms.TextInput(
                attrs={'class': 'dotted-input w-full py-3 text-sm font-medium text-gray-900 placeholder-gray-500',
                       'placeholder': 'COUNTRY'}),
            'province': forms.TextInput(
                attrs={'class': 'dotted-input w-full py-3 text-sm font-medium text-gray-900 placeholder-gray-500',
                       'placeholder': 'PROVINCE'}),
            'postal_code': forms.TextInput(
                attrs={'class': 'dotted-input w-full py-3 text-sm font-medium text-gray-900 placeholder-gray-500',
                       'placeholder': 'POSTAL CODE'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exclude(id=self.instance.id).exists():
            raise forms.ValidationError('Email already registered')
        return email

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('email'):
            cleaned_data['email'] = self.instance.email
        for field in ['company', 'address1', 'address2', 'city', 'country', 'province', 'postal_code', 'phone']:
            if cleaned_data.get(field):
                cleaned_data[field] = strip_tags(cleaned_data[field])
        return cleaned_data

class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = (
            'first_name', 'last_name', 'address1', 'address2',
            'city', 'country', 'province', 'postal_code', 'phone', 'is_default'
        )
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'dotted-input w-full py-3 text-sm',
                'placeholder': 'FIRST NAME'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'dotted-input w-full py-3 text-sm',
                'placeholder': 'LAST NAME'
            }),
            'address1': forms.TextInput(attrs={
                'class': 'dotted-input w-full py-3 text-sm',
                'placeholder': 'ADDRESS LINE 1'
            }),
            'address2': forms.TextInput(attrs={
                'class': 'dotted-input w-full py-3 text-sm',
                'placeholder': 'ADDRESS LINE 2 (OPTIONAL)'
            }),
            'city': forms.TextInput(attrs={
                'class': 'dotted-input w-full py-3 text-sm',
                'placeholder': 'CITY'
            }),
            'country': forms.TextInput(attrs={
                'class': 'dotted-input w-full py-3 text-sm',
                'placeholder': 'COUNTRY'
            }),
            'province': forms.TextInput(attrs={
                'class': 'dotted-input w-full py-3 text-sm',
                'placeholder': 'STATE / PROVINCE'
            }),
            'postal_code': forms.TextInput(attrs={
                'class': 'dotted-input w-full py-3 text-sm',
                'placeholder': 'POSTAL CODE'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'dotted-input w-full py-3 text-sm',
                'placeholder': 'PHONE'
            }),
        }

class ProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'email')
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'dotted-input w-full py-3 text-sm',
                'placeholder': 'FIRST NAME'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'dotted-input w-full py-3 text-sm',
                'placeholder': 'LAST NAME'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'dotted-input w-full py-3 text-sm',
                'placeholder': 'EMAIL'
            }),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and CustomUser.objects.filter(
            email=email
        ).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Email already registered')
        return email


class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_password'].widget = forms.PasswordInput(attrs={
            'class': 'dotted-input w-full py-3 text-sm',
            'placeholder': 'CURRENT PASSWORD'
        })
        self.fields['new_password1'].widget = forms.PasswordInput(attrs={
            'class': 'dotted-input w-full py-3 text-sm',
            'placeholder': 'NEW PASSWORD'
        })
        self.fields['new_password2'].widget = forms.PasswordInput(attrs={
            'class': 'dotted-input w-full py-3 text-sm',
            'placeholder': 'CONFIRM NEW PASSWORD'
        })