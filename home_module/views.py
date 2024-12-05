from django.shortcuts import render
from django.http import HttpRequest

# Create your views here.


def indexhome(request):
    return render(request, 'home_module/index.html')


def site_header_partial(request):
    return render(request, 'shared/site_header_partial.html')