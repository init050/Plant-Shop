# chat_module/forms.py
from django import forms
from django.utils.translation import gettext_lazy as _
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Div, Submit
from .models import ChatMessage


class ChatMessageForm(forms.ModelForm):
    class Meta:
        model = ChatMessage
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'placeholder': _('Type your message...'),
                'rows': 3,
                'class': 'resize-none'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_id = 'chat-message-form'
        self.helper.layout = Layout(
            Row(
                Column('content', css_class='form-group col-12'),
                css_class='form-row'
            ),
            Div(
                Submit('submit', _('Send'), css_class='bg-green-600 hover:bg-green-700'),
                css_class='mt-2 text-right'
            )
        )


class AdminChatMessageForm(forms.ModelForm):
    """Simplified form for admin quick replies"""
    class Meta:
        model = ChatMessage
        fields = ['content']
        widgets = {
            'content': forms.TextInput(attrs={
                'placeholder': _('Quick reply...'),
                'class': 'w-full'
            })
        }