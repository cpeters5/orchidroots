from django.http import HttpResponsePermanentRedirect
import logging
from django.utils.deprecation import MiddlewareMixin

class CleanUTF8Middleware(MiddlewareMixin):
    def process_request(self, request):
        if request.method in ['POST', 'PUT']:
            cleaned_data = {key: self.clean_invalid_utf8_characters(value)
                            for key, value in request.POST.items()}
            request.POST = cleaned_data
        return None

    def clean_invalid_utf8_characters(self, input_string):
        return input_string.encode('utf-8', 'ignore').decode('utf-8')


class LogIPMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.ip_address = get_client_ip(request)  # Attach IP address to the request
        return None

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


#  To force django to chose nonwww url as preferred url.
#  Not currently used.  We redirect www url to non www in nginx.conf instead
class RemoveWwwMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host()
        if host.startswith('www.'):
            non_www_host = host[4:]
            return HttpResponsePermanentRedirect(f'{request.scheme}://{non_www_host}{request.get_full_path()}')
        return self.get_response(request)
