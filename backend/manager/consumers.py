import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.cache import cache


class APManagerConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for AP Manager CLI"""

    async def connect(self):
        """Handle WebSocket connection"""
        self.room_group_name = 'ap_manager'
        self.client_id = None

        # Accept the connection
        await self.accept()

        # Add to AP Manager group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        print(f"✅ AP Manager WebSocket connected: {self.channel_name}")

        # Send connection confirmation
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'AP Manager WebSocket connected',
            'client_id': self.channel_name
        }))

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        # Remove from group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

        print(f"❌ AP Manager WebSocket disconnected: {self.channel_name}")

    async def receive(self, text_data):
        """Receive message from WebSocket"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            self.client_id = data.get('client_id', self.channel_name)

            if message_type == 'register':
                # AP Manager registering
                await self.handle_registration(data)

            elif message_type == 'heartbeat':
                # Heartbeat from AP Manager
                await self.handle_heartbeat(data)

            elif message_type == 'device_update':
                # Device status update
                await self.handle_device_update(data)

            elif message_type == 'command_result':
                # Result of command execution
                await self.handle_command_result(data)

            else:
                # Forward unknown messages to frontend
                await self.channel_layer.group_send('frontend', {
                    'type': 'forward_message',
                    'data': data
                })

        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))

    async def handle_registration(self, data):
        """Handle AP Manager registration"""
        client_type = data.get('client_type', 'ap_manager')
        version = data.get('version', '1.0')

        # Store client info in cache
        await database_sync_to_async(cache.set)(
            f'ap_manager_client_{self.channel_name}',
            {
                'type': client_type,
                'version': version,
                'connected': True
            },
            300  # 5 minutes expiry
        )

        # Send registration confirmation
        await self.send(text_data=json.dumps({
            'type': 'registered',
            'client_id': self.channel_name,
            'message': f'{client_type} registered successfully',
            'timestamp': asyncio.get_event_loop().time()
        }))

        # Notify frontend that AP Manager is connected
        await self.channel_layer.group_send('frontend', {
            'type': 'ap_manager_status',
            'data': {
                'status': 'connected',
                'client_id': self.channel_name,
                'client_type': client_type
            }
        })

    async def handle_heartbeat(self, data):
        """Handle heartbeat from AP Manager"""
        # Update last heartbeat timestamp
        await database_sync_to_async(cache.set)(
            f'ap_manager_heartbeat_{self.channel_name}',
            asyncio.get_event_loop().time(),
            300
        )

    async def handle_device_update(self, data):
        """Forward device updates to frontend"""
        await self.channel_layer.group_send('frontend', {
            'type': 'device_update',
            'data': data.get('data', {})
        })

    async def handle_command_result(self, data):
        """Forward command results to frontend"""
        await self.channel_layer.group_send('frontend', {
            'type': 'command_result',
            'data': data.get('data', {})
        })

    async def forward_message(self, event):
        """Forward messages from Django to AP Manager"""
        await self.send(text_data=json.dumps(event['data']))

    async def ap_manager_command(self, event):
        """Receive commands from frontend to execute on AP Manager"""
        await self.send(text_data=json.dumps({
            'type': 'command',
            'command': event.get('command'),
            'data': event.get('data', {}),
            'request_id': event.get('request_id')
        }))


class FrontendConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for frontend (React/Vite)"""

    async def connect(self):
        """Handle frontend WebSocket connection"""
        await self.accept()

        # Add to frontend group
        await self.channel_layer.group_add(
            'frontend',
            self.channel_name
        )

        print(f"✅ Frontend WebSocket connected: {self.channel_name}")

    async def disconnect(self, close_code):
        """Handle frontend disconnection"""
        await self.channel_layer.group_discard(
            'frontend',
            self.channel_name
        )

        print(f"❌ Frontend WebSocket disconnected: {self.channel_name}")

    async def receive(self, text_data):
        """Receive message from frontend"""
        try:
            data = json.loads(text_data)

            if data.get('type') == 'command':
                # Forward command to AP Manager
                await self.channel_layer.group_send('ap_manager', {
                    'type': 'ap_manager_command',
                    'command': data.get('command'),
                    'data': data.get('data', {}),
                    'request_id': data.get('request_id'),
                    'frontend_channel': self.channel_name
                })

        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))

    async def device_update(self, event):
        """Send device updates to frontend"""
        await self.send(text_data=json.dumps({
            'type': 'device_update',
            'data': event['data']
        }))

    async def ap_manager_status(self, event):
        """Send AP Manager status to frontend"""
        await self.send(text_data=json.dumps({
            'type': 'ap_manager_status',
            'data': event['data']
        }))

    async def command_result(self, event):
        """Send command results to frontend"""
        await self.send(text_data=json.dumps({
            'type': 'command_result',
            'data': event['data']
        }))
