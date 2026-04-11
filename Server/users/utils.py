from rest_framework_simplejwt.tokens import RefreshToken
from datetime import timedelta, datetime, timezone
from django.http import JsonResponse
from rest_framework import status
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.decorators import api_view


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)

    # custom refresh expiry (7 days)
    refresh.set_exp(from_time=datetime.now(tz=timezone.utc), lifetime=timedelta(days=7))

    # custom access expiry (24 hours)
    access_token = refresh.access_token
    access_token.set_exp(
        from_time=datetime.now(tz=timezone.utc), lifetime=timedelta(hours=24)
    )

    return {
        "refresh": str(refresh),
        "access": str(access_token),
    }


def flushSession(request):
    request.session.flush()  # Ensure the session data is cleared
    return JsonResponse(
        {"status": "success", "code": status.HTTP_200_OK}, status=status.HTTP_200_OK
    )


@ensure_csrf_cookie
@api_view(["GET"])
def set_csrf_token(request):
    # _, token = set_test_cookie(request)
    # return JsonResponse({"detail": "CSRF cookie set", "csrf": token})
    pass
