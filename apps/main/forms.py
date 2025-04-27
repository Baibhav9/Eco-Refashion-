from django import forms

from .constants import Roles, ProductCategory
from .models import Product, Order

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'title', 
            'description', 
            'image', 
            'category',
            'available_size',
            'color',
            'price',
            'stock_amount',
            'delivery_option',
            'pickup_address',
            'pickup_phone'
        ]
        labels = {
            "image": "Image",
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        category = kwargs.pop('category', None)
        super().__init__(*args, **kwargs)

        self.fields["category"].choices = [
            (category, category.title()),
        ]

        if category == ProductCategory.DONATION or category == ProductCategory.RECYCLE:
            if "price" in self.fields:
                del self.fields["price"]

        for field_name, field in self.fields.items():
            if field.widget.__class__.__name__ == 'Select':
                field.widget.attrs['class'] = 'form-select my-3'
            else:
                field.widget.attrs['class'] = 'form-control my-3'
            field.widget.attrs['placeholder'] = f'Enter {field.label}'

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["payment_method", "total_amount"]