from django import forms
from django.forms import inlineformset_factory

from .models import Seller
from main.models import Product, Category, ProductSize


class SellerRegistrationForm(forms.ModelForm):
    class Meta:
        model = Seller
        fields = ('shop_name', 'description', 'logo')
        widgets = {
            'shop_name': forms.TextInput(attrs={
                'class': 'w-full bg-white text-gray-900 border border-gray-300 px-4 py-3 text-sm focus:outline-none focus:border-black',
                'placeholder': 'Shop Name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full bg-white text-gray-900 border border-gray-300 px-4 py-3 text-sm focus:outline-none focus:border-black',
                'placeholder': 'Describe your shop',
                'rows': 4
            }),
        }


class SellerProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = (
            'name', 'category', 'size_kind', 'color', 'price',
            'description', 'main_image',
        )
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full bg-white text-gray-900 border border-gray-300 px-4 py-3 text-sm focus:outline-none focus:border-black',
                'placeholder': 'Product Name'
            }),
            'category': forms.Select(attrs={
                'class': 'w-full bg-white text-gray-900 border border-gray-300 px-4 py-3 text-sm focus:outline-none focus:border-black',
            }),
            'size_kind': forms.Select(attrs={
                'class': 'w-full bg-white text-gray-900 border border-gray-300 px-4 py-3 text-sm focus:outline-none focus:border-black',
            }),
            'color': forms.TextInput(attrs={
                'class': 'w-full bg-white text-gray-900 border border-gray-300 px-4 py-3 text-sm focus:outline-none focus:border-black',
                'placeholder': 'Color'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'w-full bg-white text-gray-900 border border-gray-300 px-4 py-3 text-sm focus:outline-none focus:border-black',
                'placeholder': '0.00'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full bg-white text-gray-900 border border-gray-300 px-4 py-3 text-sm focus:outline-none focus:border-black',
                'placeholder': 'Product description',
                'rows': 4
            }),
        }


class BaseSellerProductSizeFormSet(forms.BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            from main.models import Size
            valid_sizes = Size.objects.filter(kind=self.instance.size_kind)
            for form in self.forms:
                if 'size' in form.fields:
                    form.fields['size'].queryset = valid_sizes
            if 'size' in self.empty_form.fields:
                self.empty_form.fields['size'].queryset = valid_sizes

SellerProductSizeFormSet = inlineformset_factory(
    Product,
    ProductSize,
    formset=BaseSellerProductSizeFormSet,
    fields=('size', 'stock'),
    extra=2,
    can_delete=True,
    widgets={
        'size': forms.Select(attrs={
            'class': 'w-full bg-white text-gray-900 border border-gray-300 px-4 py-3 text-sm focus:outline-none focus:border-black',
        }),
        'stock': forms.NumberInput(attrs={
            'class': 'w-full bg-white text-gray-900 border border-gray-300 px-4 py-3 text-sm focus:outline-none focus:border-black',
            'min': 0,
        }),
    },
)