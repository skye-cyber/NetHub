from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from channels.generic.websocket import AsyncWebsocketConsumer
import asyncio
import time


@csrf_exempt
def device_authenticate(request):
    """Authenticate device"""
    if request.method == 'POST':
        data = json.loads(request.body)
        mac = data.get('mac', '').lower()

        # Call AP Manager CLI
        import subprocess
        result = subprocess.run(
            ['sudo', 'ap_manager', 'auth', 'authenticate', '--mac', mac, '--local'],
            capture_output=True,
            text=True
        )

        success = result.returncode == 0
        return JsonResponse({
            'success': success,
            'mac': mac,
            'timestamp': time.time(),
            'output': result.stdout if success else result.stderr
        })


@csrf_exempt
def device_block(request):
    """Block device"""
    if request.method == 'POST':
        data = json.loads(request.body)
        mac = data.get('mac', '').lower()

        import subprocess
        result = subprocess.run(
            ['sudo', 'ap_manager', 'auth', 'block', '--mac', mac, '--local'],
            capture_output=True,
            text=True
        )

        success = result.returncode == 0
        return JsonResponse({
            'success': success,
            'mac': mac,
            'timestamp': time.time(),
            'output': result.stdout if success else result.stderr
        })


class APManagerConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for AP Manager"""

    async def connect(self):
        await self.accept()
        await self.channel_layer.group_add('ap_manager', self.channel_name)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard('ap_manager', self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)

        if data.get('type') == 'register':
            # AP Manager registered
            await self.send(json.dumps({
                'type': 'registered',
                'message': 'AP Manager connected'
            }))

        elif data.get('type') == 'device_update':
            # Forward to frontend group
            await self.channel_layer.group_send('frontend', {
                'type': 'device_update',
                'data': data
            })

    async def device_update(self, event):
        """Send device update to frontend"""
        await self.send(json.dumps(event['data']))
