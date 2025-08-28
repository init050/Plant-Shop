import json

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.translation import gettext_lazy as _
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg
from django.utils import timezone
from django.db import transaction

from .models import (
    Product,
    ProductCategory,
    Cart,
    CartItem,
    Order,
    OrderItem,
    ProductVisit,
    ProductDiscount,
)
from .forms import (
    AddToCartForm,
    UpdateCartItemForm,
    CheckoutForm,
    ProductFilterForm,
    ProductDiscountForm,
)


def product_list(request):
    products = Product.objects.filter(is_active=True, is_delete=False)
    categories = ProductCategory.objects.filter(is_active=True, is_delete=False, parent=None)

    # Apply filters
    filter_form = ProductFilterForm(request.GET)
    if filter_form.is_valid():
        category = filter_form.cleaned_data.get('category')
        size = filter_form.cleaned_data.get('size')
        color = filter_form.cleaned_data.get('color')
        min_price = filter_form.cleaned_data.get('min_price')
        max_price = filter_form.cleaned_data.get('max_price')
        sort_by = filter_form.cleaned_data.get('sort_by')

        if category:
            products = products.filter(category=category)
        if size:
            products = products.filter(size=size)
        if color:
            products = products.filter(color=color)
        if min_price:
            products = products.filter(price__gte=min_price)
        if max_price:
            products = products.filter(price__lte=max_price)

        # Apply sorting
        if sort_by == 'price_asc':
            products = products.order_by('price')
        elif sort_by == 'price_desc':
            products = products.order_by('-price')
        elif sort_by == 'name_asc':
            products = products.order_by('title')
        elif sort_by == 'name_desc':
            products = products.order_by('-title')
        elif sort_by == 'newest':
            products = products.order_by('-created_at')

    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'products': page_obj,
        'categories': categories,
        'filter_form': filter_form,
        'page_obj': page_obj,
    }
    return render(request, 'product_module/product_list.html', context)


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True, is_delete=False)

    # Track product visit for analytics
    def get_client_ip(request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    ProductVisit.objects.create(
        product=product,
        user=request.user if request.user.is_authenticated else None,
        ip_address=get_client_ip(request),
    )

    # Get related products from same categories
    related_products = Product.objects.filter(
        category__in=product.category.all(),
        is_active=True,
        is_delete=False
    ).exclude(id=product.id).distinct()[:4]

    add_to_cart_form = AddToCartForm(product=product)

    context = {
        'product': product,
        'related_products': related_products,
        'add_to_cart_form': add_to_cart_form,
    }
    return render(request, 'product_module/product_detail.html', context)


def category_products(request, slug):
    category = get_object_or_404(ProductCategory, url_title=slug, is_active=True, is_delete=False)
    products = Product.objects.filter(
        category=category,
        is_active=True,
        is_delete=False
    )

    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'category': category,
        'products': page_obj,
        'page_obj': page_obj,
    }
    return render(request, 'product_module/category_products.html', context)


@login_required
@require_POST
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True, is_delete=False)

    if not product.is_in_stock:
        messages.error(request, _('Sorry, this product is out of stock.'))
        return redirect('product_module:product_detail', slug=product.slug)

    form = AddToCartForm(request.POST, product=product)
    if form.is_valid():
        quantity = form.cleaned_data['quantity']

        # Get or create user's cart
        cart, created = Cart.objects.get_or_create(user=request.user)

        # Check if item already exists in cart
        cart_item, item_created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity},
        )

        if not item_created:
            # Update quantity if item already exists
            new_quantity = cart_item.quantity + quantity
            if new_quantity <= product.stock_quantity:
                cart_item.quantity = new_quantity
                cart_item.save()
                messages.success(request, _('Cart updated successfully!'))
            else:
                messages.error(request, _('Not enough stock available.'))
        else:
            messages.success(request, _('Product added to cart successfully!'))
    else:
        messages.error(request, _('Error adding product to cart.'))

    return redirect('product_module:product_detail', slug=product.slug)


@login_required
def cart_detail(request):
    try:
        cart = Cart.objects.get(user=request.user)
        cart_items = cart.items.all()
    except Cart.DoesNotExist:
        cart_items = []
        cart = None

    context = {
        'cart': cart,
        'cart_items': cart_items,
    }
    return render(request, 'product_module/cart_detail.html', context)


@login_required
@require_POST
def update_cart_item(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    form = UpdateCartItemForm(request.POST, instance=cart_item)

    if form.is_valid():
        quantity = form.cleaned_data['quantity']
        if quantity <= cart_item.product.stock_quantity:
            cart_item.quantity = quantity
            cart_item.save()
            messages.success(request, _('Cart updated successfully!'))
        else:
            messages.error(request, _('Not enough stock available.'))

    return redirect('product_module:cart_detail')


@login_required
@require_POST
def remove_cart_item(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.delete()
    messages.success(request, _('Item removed from cart.'))
    return redirect('product_module:cart_detail')


@login_required
def checkout(request):
    try:
        cart = Cart.objects.get(user=request.user)
        if not cart.items.exists():
            messages.warning(request, _('Your cart is empty.'))
            return redirect('product_module:cart_detail')
    except Cart.DoesNotExist:
        messages.warning(request, _('Your cart is empty.'))
        return redirect('product_module:product_list')

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            # Create order with transaction to ensure data consistency
            with transaction.atomic():
                order = form.save(commit=False)
                order.user = request.user
                order.total_amount = cart.total_price
                order.save()

                # Create order items and update stock
                for cart_item in cart.items.all():
                    OrderItem.objects.create(
                        order=order,
                        product=cart_item.product,
                        quantity=cart_item.quantity,
                        price=cart_item.product.final_price,
                        product_title=cart_item.product.title,
                        product_size=cart_item.product.size,
                        product_color=cart_item.product.color,
                    )

                    # Update product stock
                    product = cart_item.product
                    product.stock_quantity -= cart_item.quantity
                    product.save()

                # Clear cart after successful order
                cart.items.all().delete()

                messages.success(request, _('Order placed successfully! Order ID: {}').format(order.order_id))
                return redirect('product_module:order_detail', order_id=order.order_id)
    else:
        form = CheckoutForm()

    context = {
        'form': form,
        'cart': cart,
    }
    return render(request, 'product_module/checkout.html', context)


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    context = {
        'order': order,
    }
    return render(request, 'product_module/order_detail.html', context)


@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')

    # Pagination
    paginator = Paginator(orders, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'orders': page_obj,
        'page_obj': page_obj,
    }
    return render(request, 'product_module/order_history.html', context)


@staff_member_required
def admin_discount_create(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        form = ProductDiscountForm(request.POST)
        if form.is_valid():
            discount = form.save(commit=False)
            discount.product = product
            discount.save()
            messages.success(request, _('Discount created successfully!'))
            return redirect('admin:product_module_product_change', product.id)
    else:
        form = ProductDiscountForm()

    context = {
        'form': form,
        'product': product,
    }
    return render(request, 'product_module/admin_discount_create.html', context)


@require_POST
@csrf_exempt
def ajax_add_to_cart(request):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': _('Please login first.')})

    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        quantity = int(data.get('quantity', 1))

        product = get_object_or_404(Product, id=product_id, is_active=True, is_delete=False)

        if not product.is_in_stock:
            return JsonResponse({'success': False, 'message': _('Product is out of stock.')})

        if quantity > product.stock_quantity:
            return JsonResponse({'success': False, 'message': _('Not enough stock available.')})

        cart, created = Cart.objects.get_or_create(user=request.user)
        cart_item, item_created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity},
        )

        if not item_created:
            new_quantity = cart_item.quantity + quantity
            if new_quantity <= product.stock_quantity:
                cart_item.quantity = new_quantity
                cart_item.save()
            else:
                return JsonResponse({'success': False, 'message': _('Not enough stock available.')})

        return JsonResponse({
            'success': True,
            'message': _('Product added to cart!'),
            'cart_count': cart.total_items,
        })

    except Exception as e:
        return JsonResponse({'success': False, 'message': _('Error adding product to cart.')})


def ajax_cart_count(request):
    """Get current cart item count for authenticated users"""
    if not request.user.is_authenticated:
        return JsonResponse({'count': 0})

    try:
        cart = Cart.objects.get(user=request.user)
        return JsonResponse({'count': cart.total_items})
    except Cart.DoesNotExist:
        return JsonResponse({'count': 0})


def search_products(request):
    query = request.GET.get('q', '').strip()
    products = []

    if query:
        products = Product.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(short_description__icontains=query),
            is_active=True,
            is_delete=False
        )[:20]

    context = {
        'products': products,
        'query': query,
    }
    return render(request, 'product_module/search_results.html', context)