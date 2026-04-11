from django.views import View
from django.http import JsonResponse
import json


class BaseAPIView(View):
    """Base API view with common functionality"""

    def json_response(self, data, status=200):
        return JsonResponse(data, status=status)

    def error_response(self, message, status=400):
        return self.json_response({'error': message}, status=status)

    def parse_json_body(self, request):
        try:
            return json.loads(request.body)
        except json.JSONDecodeError:
            return None
