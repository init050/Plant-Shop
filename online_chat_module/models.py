from django.db import models
from account_module.models import User

# Create your models here.
class Message(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Author')
    content = models.TextField(verbose_name='Content')
    timestamp= models.DateTimeField(auto_now_add=True, verbose_name='Date & Time')

    def last_message(self):
        return Message.objects.order_by('-timestamp').all()
    
    def __str__(self) -> str:
        return self.author.username