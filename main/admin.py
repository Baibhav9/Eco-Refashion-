from django.contrib import admin
from .models import ClothUpload, SellerProduct, RentalRequest, Cart, Product
from django.shortcuts import render

class SellerProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'seller', 'category', 'status', 'price', 'created_at')
    list_filter = ('status', 'category', 'created_at')
    list_editable = ('price',)  # Allows direct editing in list view
    search_fields = ('title', 'seller__username', 'description')
    actions = ['approve_products', 'reject_products']
    readonly_fields = ('created_at',)  # Make creation timestamp non-editable

    # Field organization for add/edit forms
    fieldsets = (
        (None, {
            'fields': ('seller', 'title', 'description')
        }),
        ('Details', {
            'fields': ('category', 'price', 'available_size', 'color')
        }),
        ('Status', {
            'fields': ('status', 'image', 'created_at')
        }),
    )

    def approve_products(self, request, queryset):
        """Custom admin action to approve products"""
        updated = queryset.filter(status='pending').update(status='approved')
        self.message_user(
            request, 
            f"Successfully approved {updated} product(s). "
            f"{queryset.count() - updated} were already approved."
        )
    approve_products.short_description = "Approve selected pending products"

    def reject_products(self, request, queryset):
        """Custom admin action to reject products"""
        if 'confirm' in request.POST:
            updated = queryset.update(status='rejected')
            self.message_user(request, f"Rejected {updated} product(s)")
            return
        else:
            # Show confirmation page
            return render(request, 'reject_confirmation', 
                        {'products': queryset})
    reject_products.short_description = "Reject selected products"

class ClothUploadAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'status', 'upload_type', 'created_at')
    list_filter = ('status', 'upload_type')
    actions = ['approve_products']

    def approve_products(self, request, queryset):
        updated = queryset.update(status='approved')
        print(f"DEBUG: Attempted to approve {updated} ClothUpload items")  # Check server logs
        
        # Force-refresh one item to verify status
        sample_item = queryset.first()
        if sample_item:
            sample_item.refresh_from_db()
            print(f"DEBUG: Sample ClothUpload status after update: {sample_item.status}")  # Should be 'approved'
        
        self.message_user(request, f"{updated} clothing items approved.")
    approve_products.short_description = "Approve selected items"

#Admin classes
admin.site.register(SellerProduct, SellerProductAdmin)
admin.site.register(ClothUpload, ClothUploadAdmin)
admin.site.register(Cart)
