from django.db import transaction, IntegrityError
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from util.view_utils import BaseAPIView
from networks.models import Network
from django.contrib.auth import login, logout, authenticate, get_backends
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from rest_framework import status
from .utils import get_tokens_for_user
from .forms import NetHubUserCreationForm

User = get_user_model()


@method_decorator(csrf_exempt, name='dispatch')
class UserManagementAPIView(BaseAPIView):
    def get(self, request):
        try:
            users = User.objects.all().prefetch_related('networks')

            data = []
            for user in users:
                data.append({
                    'id': user.id,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'role': user.role,
                    'status': user.status,
                    'last_login': user.last_login.isoformat() if user.last_login else None,
                    'networks': [str(net.id) for net in user.networks.all()],
                    'created_at': user.created_at.isoformat(),
                })

            return self.json_response({'users': data})

        except Exception as e:
            print(e)
            return self.error_response(str(e), 500)

    def post(self, request):
        """Create a new user"""
        data = self.parse_json_body(request)
        if not data:
            return self.error_response('Invalid JSON')

        try:
            with transaction.atomic():
                # Create user with all fields
                user = User.objects.create_user(
                    username=data.get('username'),
                    email=data.get('email'),
                    password=data.get('password'),
                    first_name=data.get('first_name', ''),
                    last_name=data.get('last_name', ''),
                    role=data.get('role', 'viewer'),
                    status=data.get('status', 'active'),
                    phone=data.get('phone'),
                    department=data.get('department')
                )

                # Add network access
                network_ids = data.get('networks', [])
                if network_ids:
                    networks = Network.objects.filter(id__in=network_ids)
                    user.networks.set(networks)

                # Specify backend explicitly
                backend = get_backends()[0]  # Use the first backend (usually ModelBackend)
                login(
                    request,
                    user,
                    backend=backend.__class__.__module__ + "." + backend.__class__.__name__,
                )

                return self.json_response({
                    'user': {
                        'id': user.id,
                        'email': user.email,
                        'role': user.role,
                        'networks': [str(net.id) for net in user.networks.all()],
                        'status': user.status
                    }
                }, 201)

        except Exception as e:
            print(e)
            return self.error_response(str(e), 400)


@csrf_exempt
@require_POST
def login_view(request):
    if request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'Already authenticated', 'code': status.HTTP_200_OK})

    try:
        import json
        data = json.loads(request.body.decode())
        data = data if data else request.POST
    except Exception:
        return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)

    form = NetHubUserCreationForm(request, data=data)
    if form.is_valid():
        username = form.cleaned_data.get("username")
        password = form.cleaned_data.get("password")
        user = authenticate(request, username=username, password=password)

    if not user:
        return JsonResponse(
            {
                "status": "error",
                "message": "Invalid credentials.",
                "code": status.HTTP_400_BAD_REQUEST,
            }
        )

    if not user.is_active:
        return JsonResponse(
            {
                "status": "error",
                "message": "Account is disabled.",
                "code": status.HTTP_401_UNAUTHORIZED,
            }
        )

    login(request, user)

    # Update user online status
    user.is_online = True
    user.save()

    # Issue JWT tokens
    tokens = get_tokens_for_user(user)

    # Update last seen
    request.user.update_last_seen()

    return JsonResponse(
        {
            "status": "success",
            "message": f'Welcome {request.user}',
            "redirect": "Dashboard",
            "auth": user.is_authenticated,
            "code": status.HTTP_200_OK,
            "auth_data": {
                "username": user.username,
                "roles": [user.role],
                "access": tokens["access"],
                "refresh": tokens["refresh"],
            },
        },
        status.HTTP_200_OK
    )


@login_required
def logout_view(request):
    # Update user online status
    request.user.is_online = False
    request.user.save()

    # Update last seen
    request.user.update_last_seen()

    logout(request)
    return JsonResponse({'status': 'success', 'message': 'Logged out successfully'})


@login_required
def profile_view(request):
    """User profile view."""
    user = request.user

    context = {
        "user": user,
    }
    return JsonResponse({'status': 'success', 'data': context, 'code': 200})


@login_required
def update_profile_view(request):
    if request.method == "POST":
        user = request.user
        user.email = request.POST.get("email", user.email)
        user.first_name = request.POST.get("first_name", user.first_name)
        user.last_name = request.POST.get("last_name", user.last_name)
        user.bio = request.POST.get("bio", user.bio)
        user.color_scheme = request.POST.get("color_scheme", user.color_scheme)
        user.phone = request.POST.get("phone", user.phone)
        user.department = request.POST.get("department", user.department)

        if "avatar" in request.FILES:
            user.avatar = request.FILES["avatar"]

        user.save()
        messages.success(request, "Profile updated successfully!")
        return redirect("profile")

    return render(request, "users/update_profile.html")
