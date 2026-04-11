from django.core.management.base import BaseCommand
import websockets
import asyncio
import json


class Command(BaseCommand):
    help = 'Test WebSocket connection to Django'

    def add_arguments(self, parser):
        parser.add_argument('--url', default='ws://localhost:8001/ws/ap-manager/')

    def handle(self, *args, **options):
        asyncio.run(self.test_websocket(options['url']))

    async def test_websocket(self, url):
        self.stdout.write(f"Testing WebSocket connection to {url}")

        try:
            async with websockets.connect(url) as websocket:
                # Register as AP Manager
                await websocket.send(json.dumps({
                    'type': 'register',
                    'client_type': 'ap_manager',
                    'version': '1.0'
                }))

                # Wait for response
                response = await websocket.recv()
                self.stdout.write(f"Response: {response}")

                # Send heartbeat
                await websocket.send(json.dumps({
                    'type': 'heartbeat',
                    'timestamp': asyncio.get_event_loop().time()
                }))

                self.stdout.write(self.style.SUCCESS('✅ WebSocket test successful!'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ WebSocket test failed: {e}'))
