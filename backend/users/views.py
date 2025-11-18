from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from portal.views import BaseAPIView
from .models import User, UserProfile
from portal.models import Network


@method_decorator(csrf_exempt, name='dispatch')
class UserManagementAPIView(BaseAPIView):

    def get(self, request):
        """Get all users with profiles"""
        try:
            users = User.objects.select_related('profile').all()
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
            # Create user
            user = User.objects.create_user(
                username=data.get('email'),
                email=data.get('email'),
                password=data.get('password', 'temp123'),  # Should be generated
                first_name=data.get('first_name', ''),
                last_name=data.get('last_name', '')
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
