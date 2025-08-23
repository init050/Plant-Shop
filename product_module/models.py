from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.utils.text import slugify
from django.urls import reverse
from django.core.validators import MinValueValidator, MaxValueValidator
from account_module.models import User
import uuid


class ProductCategory(models.Model):
    title = models.CharField(_('Title Category'), max_length=80, db_index=True)
    url_title = models.CharField(_('URL Title Category'), max_length=200, db_index=True)
    description = models.TextField(_('Description'), blank=True, null=True)
    image = models.ImageField(_('Category Image'), upload_to='images/categories/', blank=True, null=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    is_active = models.BooleanField(_('Active Category'), default=True)
    is_delete = models.BooleanField(_('Delete category'), default=False)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        verbose_name = _('Product Category')
        verbose_name_plural = _('Product Categories')
        ordering = ['title']

    def __str__(self):
        return f'{self.title}'

    def save(self, *args, **kwargs):
        if not self.url_title:
            self.url_title = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('product_module:category_products', kwargs={'slug': self.url_title})


class Product(models.Model):
    SIZE_CHOICES = [
        ('small', _('Small')),
        ('medium', _('Medium')),
        ('large', _('Large')),
    ]
    
    COLOR_CHOICES = [
        ('white', _('White')),
        ('black', _('Black')),
        ('brown', _('Brown')),
        ('terracotta', _('Terracotta')),
        ('blue', _('Blue')),
        ('green', _('Green')),
        ('gray', _('Gray')),
        ('beige', _('Beige')),
    ]

    title = models.CharField(_('Product'), max_length=80, db_index=True)
    category = models.ManyToManyField(ProductCategory, related_name='products', verbose_name=_('Product Categories'))
    image = models.ImageField(_('Product Photo'), upload_to='images/products', null=True, blank=True)
    gallery = models.ManyToManyField('ProductGallery', blank=True, verbose_name=_('Product Gallery'))
    price = models.DecimalField(_('Price'), max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    size = models.CharField(_('Size'), max_length=10, choices=SIZE_CHOICES, default='medium')
    color = models.CharField(_('Color'), max_length=20, choices=COLOR_CHOICES, default='terracotta')
    stock_quantity = models.PositiveIntegerField(_('Stock Quantity'), default=0)
    short_description = models.CharField(_('Short Description'), max_length=350, null=True, db_index=True)
    description = models.TextField(_('Description'), db_index=True)
    slug = models.SlugField(_('URL Title'), max_length=200, default='', blank=True, unique=True, db_index=True)
    is_active = models.BooleanField(_('Active Product'), default=True)
    is_delete = models.BooleanField(_('Delete Product'), default=False)
    is_featured = models.BooleanField(_('Featured Product'), default=False)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        verbose_name = _('Product')
        verbose_name_plural = _('Products')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} - ${self.price}'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('product_module:product_detail', kwargs={'slug': self.slug})

    @property
    def is_in_stock(self):
        return self.stock_quantity > 0

    @property
    def final_price(self):
        active_discount = self.discounts.filter(
            is_active=True,
            start_date__lte=timezone.now(),
            end_date__gte=timezone.now()
        ).first()
        
        if active_discount:
            if active_discount.discount_type == 'percentage':
                discount_amount = (self.price * active_discount.value) / 100
                return self.price - discount_amount
            else:
                return max(self.price - active_discount.value, 0)
        return self.price


class ProductGallery(models.Model):
    image = models.ImageField(_('Gallery Image'), upload_to='images/products/gallery/')
    alt_text = models.CharField(_('Alt Text'), max_length=200, blank=True)
    is_active = models.BooleanField(_('Active'), default=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)

    class Meta:
        verbose_name = _('Product Gallery')
        verbose_name_plural = _('Product Galleries')

    def __str__(self):
        return f'Gallery Image {self.id}'


class ProductDiscount(models.Model):
    DISCOUNT_TYPES = [
        ('percentage', _('Percentage')),
        ('fixed', _('Fixed Amount')),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='discounts', verbose_name=_('Product'))
    title = models.CharField(_('Discount Title'), max_length=100)
    discount_type = models.CharField(_('Discount Type'), max_length=10, choices=DISCOUNT_TYPES)
    value = models.DecimalField(_('Discount Value'), max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    start_date = models.DateTimeField(_('Start Date'))
    end_date = models.DateTimeField(_('End Date'))
    is_active = models.BooleanField(_('Active'), default=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)

    class Meta:
        verbose_name = _('Product Discount')
        verbose_name_plural = _('Product Discounts')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} - {self.product.title}'

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.start_date >= self.end_date:
            raise ValidationError(_('End date must be after start date'))
        
        if self.discount_type == 'percentage' and self.value > 100:
            raise ValidationError(_('Percentage discount cannot exceed 100%'))

    def save(self, *args, **kwargs):
        if timezone.now() > self.end_date:
            self.is_active = False
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        return timezone.now() > self.end_date


class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart', verbose_name=_('User'))
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        verbose_name = _('Cart')
        verbose_name_plural = _('Carts')

    def __str__(self):
        return f'Cart - {self.user.email}'

    @property
    def total_price(self):
        return sum(item.subtotal for item in self.items.all())

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items', verbose_name=_('Cart'))
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name=_('Product'))
    quantity = models.PositiveIntegerField(_('Quantity'), default=1, validators=[MinValueValidator(1)])
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        verbose_name = _('Cart Item')
        verbose_name_plural = _('Cart Items')
        unique_together = ['cart', 'product']

    def __str__(self):
        return f'{self.product.title} x {self.quantity}'

    @property
    def subtotal(self):
        return self.product.final_price * self.quantity


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('processing', _('Processing')),
        ('shipped', _('Shipped')),
        ('delivered', _('Delivered')),
        ('cancelled', _('Cancelled')),
    ]

    order_id = models.UUIDField(_('Order ID'), default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders', verbose_name=_('User'))
    status = models.CharField(_('Status'), max_length=20, choices=STATUS_CHOICES, default='pending')
    total_amount = models.DecimalField(_('Total Amount'), max_digits=10, decimal_places=2)
    shipping_address = models.TextField(_('Shipping Address'))
    phone_number = models.CharField(_('Phone Number'), max_length=20)
    notes = models.TextField(_('Notes'), blank=True, null=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        verbose_name = _('Order')
        verbose_name_plural = _('Orders')
        ordering = ['-created_at']

    def __str__(self):
        return f'Order {self.order_id} - {self.user.email}'

    def get_absolute_url(self):
        return reverse('product_module:order_detail', kwargs={'order_id': self.order_id})


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name=_('Order'))
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name=_('Product'))
    quantity = models.PositiveIntegerField(_('Quantity'))
    price = models.DecimalField(_('Price'), max_digits=10, decimal_places=2)
    # Store product details at time of order for historical accuracy
    product_title = models.CharField(_('Product Title'), max_length=80)
    product_size = models.CharField(_('Product Size'), max_length=10)
    product_color = models.CharField(_('Product Color'), max_length=20)

    class Meta:
        verbose_name = _('Order Item')
        verbose_name_plural = _('Order Items')

    def __str__(self):
        return f'{self.product_title} x {self.quantity}'

    @property
    def subtotal(self):
        return self.price * self.quantity


class ProductVisit(models.Model):
    ip_address = models.GenericIPAddressField(_('IP Address'))
    timestamp = models.DateTimeField(_('Timestamp'), auto_now_add=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name=_('Product'))
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE, verbose_name=_('User'))

    class Meta:
        verbose_name = _('Product Visit')
        verbose_name_plural = _('Product Visits')

    def __str__(self):
        return f'{self.product.title} / {self.ip_address}'