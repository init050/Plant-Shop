def get_client_ip(request):
    """
    Retrieves the client's IP address from the request object.
    
    This utility function is designed to correctly identify the client's IP
    even when the application is behind a proxy or load balancer. It prioritizes
    the 'HTTP_X_FORWARDED_FOR' header, which is a standard way proxies
    pass along the original IP, falling back to 'REMOTE_ADDR' if it's not present.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
