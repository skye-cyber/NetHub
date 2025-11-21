from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from util.view_utils import BaseAPIView
from .models import CustomUser, UserProfile
from networks.models import Network
from django.contrib.auth import login, logout, authenticate, get_backends
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import CustomUserCreationForm, CustomAuthenticationForm
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from rest_framework import status  # , viewsets, generics, permissions
from .utils import get_tokens_for_user

User = get_user_model()


@method_decorator(csrf_exempt, name='dispatch')
class UserManagementAPIView(BaseAPIView):

    def get(self, request):
        """Get all users with profiles"""
        try:
            users = CustomUser.objects.select_related('profile').all()
            data = []
            for user in users:
                profile = user.profile
                data.append({
                    'id': user.id,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'role': profile.role,
                    'status': profile.status,
                    'last_login': profile.last_login.isoformat() if profile.last_login else None,
                    'networks': [str(net.id) for net in profile.networks.all()],
                    'created_at': profile.created_at.isoformat(),
                })
            return self.json_response({'users': data})
        except Exception as e:
            return self.error_response(str(e), 500)

    def post(self, request):
        """Create a new user"""
        data = self.parse_json_body(request)
        if not data:
            return self.error_response('Invalid JSON')

        try:
            form = CustomUserCreationForm(data)
            if form.is_valid():
                user = form.save()

            '''
            # Create user
            user = User.objects.create_user(
                username=data.get('email'),
                email=data.get('email'),
                password=data.get('password', 'temp123'),  # Should be generated
                first_name=data.get('first_name', ''),
                last_name=data.get('last_name', '')
            )
            '''

            # Specify backend explicitly
            backend = get_backends()[0]  # Use the first backend (usually ModelBackend)
            login(
                request,
                user,
                backend=backend.__class__.__module__ + "." + backend.__class__.__name__,
            )
            # Create profile
            profile = UserProfile.objects.create(
                user=user,
                role=data.get('role', 'viewer'),
                status=data.get('status', 'active'),
                phone=data.get('phone'),
                department=data.get('department')
            )

            # Add network access
            network_ids = data.get('networks', [])
            if network_ids:
                networks = Network.objects.filter(id__in=network_ids)
                profile.networks.set(networks)

            return self.json_response({
                'message': 'User created successfully',
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'role': profile.role
                }
            }, 201)
        except Exception as e:
            return self.error_response(str(e), 400)


@csrf_exempt  # This MUST be outermost
@require_POST
def login_view(request):
    """User login view."""
    if request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'Invalid credentials', 'code': status.HTTP_200_OK})

    try:
        import json
        data = json.loads(request.body.decode())
        data = data if data else request.POST
    except Exception:
        return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)

        form = CustomAuthenticationForm(request, data=data)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(request, username=username, password=password)

        if not user.is_active:
            return JsonResponse(
                {
                    "status": "error",
                    "message": "Account is disabled.",
                    "code": status.HTTP_401_UNAUTHORIZED,
                }
            )

        if user is None:
            return JsonResponse(
                {
                    "status": "error",
                    "message": "Invalid credentials.",
                    "code": status.HTTP_400_BAD_REQUEST,
                }
            )

        login(request, user)

        # Update user online status
        user.is_online = True
        user.save()

        # issue JWT tokens
        # refresh = RefreshToken.for_user(user)
        # access_token = str(refresh.access_token)

        tokens = get_tokens_for_user(user)

        # print("Auth Status:", user.is_authenticated, user.is_anonymous)

        # Update lats seen
        request.user.update_last_seen()
        return JsonResponse(
            {
                "status": "success",
                "message": f'Welcome {request.user}',
                "verified": user.email_verified,
                "email": user.email,
                "redirect": "Dashboard",
                "auth": user.is_authenticated,
                "code": status.HTTP_200_OK,
                "auth_data": {
                    "username": user.username,
                    "roles": ["user"],
                    "access": tokens["access"],
                    "refresh": tokens["refresh"],
                },
            },
            status.HTTP_200_OK
        )

    return JsonResponse(
        {
            "status": "error",
            "message": "Invalid form data",
            "errors": form.errors,
            "code": status.HTTP_400_BAD_REQUEST,
        }
    )


@login_required
def logout_view(request):
    """User logout view."""
    # Update user online status
    request.user.is_online = False

    # Update lats seen
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
    return JsonResponse({'status': 'sucess', 'data': context, 'code': 200})


@login_required
def update_profile_view(request):
    """Update user profile."""
    if request.method == "POST":
        user = request.user
        user.email = request.POST.get("email", user.email)
        user.bio = request.POST.get("bio", user.bio)
        user.color_scheme = request.POST.get("color_scheme", user.color_scheme)
        user.notification_enabled = "notification_enabled" in request.POST
        user.sound_enabled = "sound_enabled" in request.POST

        if "avatar" in request.FILES:
            user.avatar = request.FILES["avatar"]

        user.save()
        messages.success(request, "Profile updated successfully!")
        return redirect("profile")

    return render(request, "users/update_profile.html")
