from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Div, Submit, Field

from .models import Product, ProductCategory, CartItem, Order, ProductDiscount


class AddToCartForm(forms.ModelForm):
    class Meta:
        model = CartItem
        fields = [
            'quantity',
        ]
        widgets = {
            'quantity': forms.NumberInput(
                attrs={
                    'min': 1,
                    'max': 999,
                    'value': 1,
                    'class': 'w-20 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500',
                }
            )
        }

    def __init__(self, *args, **kwargs):
        self.product = kwargs.pop('product', None)
        super().__init__(*args, **kwargs)

        if self.product:
            self.fields['quantity'].widget.attrs['max'] = self.product.stock_quantity

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if self.product and quantity > self.product.stock_quantity:
            raise ValidationError(
                _('Not enough stock available. Only {} items left.').format(self.product.stock_quantity)
            )
        return quantity


class UpdateCartItemForm(forms.ModelForm):
    class Meta:
        model = CartItem
        fields = [
            'quantity',
        ]
        widgets = {
            'quantity': forms.NumberInput(
                attrs={
                    'min': 1,
                    'class': 'w-16 px-2 py-1 border border-gray-300 rounded text-center',
                }
            )
        }


class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            'shipping_address',
            'phone_number',
            'notes',
        ]
        widgets = {
            'shipping_address': forms.Textarea(
                attrs={
                    'rows': 4,
                    'placeholder': _('Enter your complete shipping address...'),
                }
            ),
            'phone_number': forms.TextInput(
                attrs={
                    'placeholder': _('Your phone number'),
                }
            ),
            'notes': forms.Textarea(
                attrs={
                    'rows': 3,
                    'placeholder': _('Any special instructions or notes...'),
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Row(
                Column('shipping_address', css_class='form-group col-12'),
                css_class='form-row',
            ),
            Row(
                Column('phone_number', css_class='form-group col-md-6'),
                Column('notes', css_class='form-group col-md-6'),
                css_class='form-row',
            ),
            Div(
                Submit(
                    'submit',
                    _('Place Order'),
                    css_class='bg-green-600 hover:bg-green-700 text-white px-8 py-3 rounded-lg'
                ),
                css_class='mt-4 text-center',
            )
        )


class ProductFilterForm(forms.Form):
    category = forms.ModelChoiceField(
        queryset=ProductCategory.objects.filter(is_active=True, is_delete=False),
        empty_label=_('All Categories'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    size = forms.ChoiceField(
        choices=[('', _('All Sizes'))] + Product.SIZE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    color = forms.ChoiceField(
        choices=[('', _('All Colors'))] + Product.COLOR_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    min_price = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(
            attrs={
                'placeholder': _('Min Price'),
                'class': 'form-control',
            }
        ),
    )

    max_price = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(
            attrs={
                'placeholder': _('Max Price'),
                'class': 'form-control',
            }
        ),
    )

    SORT_CHOICES = [
        ('', _('Default')),
        ('price_asc', _('Price: Low to High')),
        ('price_desc', _('Price: High to Low')),
        ('name_asc', _('Name: A to Z')),
        ('name_desc', _('Name: Z to A')),
        ('newest', _('Newest First')),
    ]

    sort_by = forms.ChoiceField(
        choices=SORT_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    def clean(self):
        cleaned_data = super().clean()
        min_price = cleaned_data.get('min_price')
        max_price = cleaned_data.get('max_price')

        if min_price and max_price and min_price > max_price:
            raise ValidationError(
                _('Minimum price cannot be greater than maximum price.')
            )

        return cleaned_data


class ProductDiscountForm(forms.ModelForm):
    class Meta:
        model = ProductDiscount
        fields = [
            'title',
            'discount_type',
            'value',
            'start_date',
            'end_date',
        ]
        widgets = {
            'start_date': forms.DateTimeInput(
                attrs={
                    'type': 'datetime-local',
                    'class': 'form-control',
                }
            ),
            'end_date': forms.DateTimeInput(
                attrs={
                    'type': 'datetime-local',
                    'class': 'form-control',
                }
            ),
            'title': forms.TextInput(
                attrs={
                    'placeholder': _('e.g., Summer Sale'),
                    'class': 'form-control',
                }
            ),
            'value': forms.NumberInput(
                attrs={
                    'step': '0.01',
                    'min': '0',
                    'class': 'form-control',
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Row(
                Column('title', css_class='form-group col-md-6'),
                Column('discount_type', css_class='form-group col-md-6'),
                css_class='form-row',
            ),
            Row(
                Column('value', css_class='form-group col-md-4'),
                Column('start_date', css_class='form-group col-md-4'),
                Column('end_date', css_class='form-group col-md-4'),
                css_class='form-row',
            ),
            Div(
                Submit(
                    'submit',
                    _('Create Discount'),
                    css_class='bg-blue-600 hover:bg-blue-700'
                ),
                css_class='mt-3 text-right',
            )
        )