from django import forms
from .models import Seller
from main.models import Product, Category


class SellerRegistrationForm(forms.ModelForm):
    class Meta:
        model = Seller
        fields = ('shop_name', 'description', 'logo')
        widgets = {
            'shop_name': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 px-4 py-3 text-sm focus:outline-none focus:border-black',
                'placeholder': 'Shop Name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full border border-gray-300 px-4 py-3 text-sm focus:outline-none focus:border-black',
                'placeholder': 'Describe your shop',
                'rows': 4
            }),
        }


class SellerProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ('name', 'category', 'color', 'price', 'description', 'main_image')
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 px-4 py-3 text-sm focus:outline-none focus:border-black',
                'placeholder': 'Product Name'
            }),
            'category': forms.Select(attrs={
                'class': 'w-full border border-gray-300 px-4 py-3 text-sm focus:outline-none focus:border-black',
            }),
            'color': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 px-4 py-3 text-sm focus:outline-none focus:border-black',
                'placeholder': 'Color'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'w-full border border-gray-300 px-4 py-3 text-sm focus:outline-none focus:border-black',
                'placeholder': '0.00'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full border border-gray-300 px-4 py-3 text-sm focus:outline-none focus:border-black',
                'placeholder': 'Product description',
                'rows': 4
            }),
        }