from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from . import models


@admin.register(models.ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'url_title',
        'parent',
        'is_active',
        'created_at',
    ]
    list_filter = [
        'is_active',
        'is_delete',
        'created_at',
        'parent',
    ]
    search_fields = [
        'title',
        'description',
    ]
    prepopulated_fields = {
        'url_title': ('title',)
    }
    list_editable = [
        'is_active',
    ]
    list_per_page = 25

    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_delete=False)


@admin.register(models.Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'price',
        'size',
        'color',
        'stock_quantity',
        'is_featured',
        'is_active',
        'created_at',
    ]
    list_filter = [
        'is_active',
        'is_delete',
        'is_featured',
        'size',
        'color',
        'category',
        'created_at',
    ]
    search_fields = [
        'title',
        'description',
        'short_description',
    ]
    prepopulated_fields = {
        'slug': ('title',)
    }
    filter_horizontal = [
        'category',
    ]
    list_editable = [
        'price',
        'stock_quantity',
        'is_featured',
        'is_active',
    ]
    list_per_page = 25
    readonly_fields = [
        'created_at',
        'updated_at',
    ]

    fieldsets = (
        (
            _('Basic Information'), {
                'fields': ('title', 'slug', 'category', 'short_description', 'description')
            }
        ),
        (
            _('Media'), {
                'fields': ('image',)
            }
        ),
        (
            _('Specifications'), {
                'fields': ('size', 'color', 'price', 'stock_quantity')
            }
        ),
        (
            _('Status'), {
                'fields': ('is_active', 'is_featured', 'is_delete')
            }
        ),
        (
            _('Timestamps'), {
                'fields': ('created_at', 'updated_at'),
                'classes': ('collapse',)
            }
        ),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_delete=False)


@admin.register(models.ProductGallery)
class ProductGalleryAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'image_preview',
        'alt_text',
        'is_active',
        'created_at',
    ]
    list_filter = [
        'is_active',
        'created_at',
    ]
    list_editable = [
        'is_active',
    ]

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="50" height="50" style="object-fit: cover;" />',
                obj.image.url
            )
        return '-'

    image_preview.short_description = _('Preview')


@admin.register(models.ProductDiscount)
class ProductDiscountAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'product',
        'discount_type',
        'value',
        'start_date',
        'end_date',
        'is_active',
    ]
    list_filter = [
        'discount_type',
        'is_active',
        'start_date',
        'end_date',
    ]
    search_fields = [
        'title',
        'product__title',
    ]
    list_editable = [
        'is_active',
    ]
    date_hierarchy = 'start_date'

    fields = [
        'product',
        'title',
        'discount_type',
        'value',
        'start_date',
        'end_date',
        'is_active',
    ]


@admin.register(models.Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'created_at',
        'updated_at',
    ]
    list_filter = [
        'created_at',
        'updated_at',
    ]
    search_fields = [
        'user__email',
        'user__username',
    ]
    readonly_fields = [
        'created_at',
        'updated_at',
    ]


@admin.register(models.CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = [
        'cart',
        'product',
        'quantity',
        'created_at',
    ]
    list_filter = [
        'created_at',
    ]
    search_fields = [
        'cart__user__email',
        'product__title',
    ]


@admin.register(models.Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_id',
        'user',
        'status',
        'total_amount',
        'created_at',
    ]
    list_filter = [
        'status',
        'created_at',
        'updated_at',
    ]
    search_fields = [
        'order_id',
        'user__email',
        'user__username',
    ]
    list_editable = [
        'status',
    ]
    readonly_fields = [
        'order_id',
        'created_at',
        'updated_at',
    ]
    date_hierarchy = 'created_at'

    fieldsets = (
        (
            _('Order Information'), {
                'fields': ('order_id', 'user', 'status', 'total_amount')
            }
        ),
        (
            _('Shipping Details'), {
                'fields': ('shipping_address', 'phone_number', 'notes')
            }
        ),
        (
            _('Timestamps'), {
                'fields': ('created_at', 'updated_at'),
                'classes': ('collapse',)
            }
        ),
    )


@admin.register(models.OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = [
        'order',
        'product_title',
        'quantity',
        'price',
    ]
    list_filter = [
        'order__created_at',
    ]
    search_fields = [
        'order__order_id',
        'product_title',
    ]


@admin.register(models.ProductVisit)
class ProductVisitAdmin(admin.ModelAdmin):
    list_display = [
        'product',
        'user',
        'ip_address',
        'timestamp',
    ]
    list_filter = [
        'timestamp',
    ]
    search_fields = [
        'product__title',
        'user__email',
        'ip_address',
    ]
    readonly_fields = [
        'timestamp',
    ]
    date_hierarchy = 'timestamp'

    def has_add_permission(self, request):
        return False