from django.shortcuts import render


# Create your views here.


def indexhome(request):
    return render(request, 'home_module/index.html')


def site_header_component(request):
    return render(request, 'site_header_component.html')


def site_footer_component(request):
    return render(request, 'site_footer_component.html')