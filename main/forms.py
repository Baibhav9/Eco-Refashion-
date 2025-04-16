from django import forms
from .models import SellerProduct, ClothUpload

class SellerProductForm(forms.ModelForm):
    class Meta:
        model = SellerProduct
        fields = [
            'title', 
            'description', 
            'image', 
            'category',
            'available_size',
            'color',
            'price'
        ]
class ClothUploadForm(forms.ModelForm):
    class Meta:
        model = ClothUpload
        fields = ['title', 'description', 'image']

    def clean(self):
        cleaned_data = super().clean()
        # Ensure rental duration is set only if item is marked as rentable
        if cleaned_data.get('is_rentable') and cleaned_data.get('rental_duration') > 7:
            raise forms.ValidationError("Rental duration cannot exceed 7 days.")
        return cleaned_data