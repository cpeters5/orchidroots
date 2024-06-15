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

