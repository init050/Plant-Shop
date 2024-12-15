from django.db import models
from account_module.models import User 
from product_module.models import Product

# Create your models here.

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Username')
    is_paid = models.BooleanField(verbose_name='Is Paid /  Is Not Paid')
    payment_date = models.DateField(null=True, blank=True, verbose_name='Payment Date')

    class Meta:
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
    
    def __str__(self):
        return str(self.user)
    

class DetailOrder(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, verbose_name='Detail Order')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='Product')
    final_price = models.IntegerField(null=True, blank=True, verbose_name='Final Price')
    count = models.IntegerField(verbose_name='Count')

    class Meta:
        verbose_name = 'Detail Order'
        verbose_name_plural = 'Details Orders'

    def __str__(self):
        return str(self.order)