"""
AP Manager Communication System
- REST client for Django API
- WebSocket client for real-time updates
- Webhook handler for Django callbacks
"""

import json
import asyncio
import aiohttp
import websockets
import threading
from typing import Dict, Any, Optional, Callable
import ssl
import certifi


class APManagerCommunicator:
    """Handles communication between AP Manager and Django"""

    def __init__(self, base_url: str = "http://localhost:8001",
                 api_token: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.api_token = api_token
        self.ws_url = self.base_url.replace('http', 'ws') + '/ws/ap-manager/'
        self.session = None
        self.ws_connection = None
        self.running = False
        self.callbacks = {
            'device_connected': [],
            'device_disconnected': [],
            'device_authenticated': [],
            'device_blocked': [],
            'hotspot_status': [],
        }

    async def initialize(self):
        """Initialize async session"""
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        self.session = aiohttp.ClientSession(
            headers=self._get_headers(),
            connector=aiohttp.TCPConnector(ssl=ssl_context)
        )

    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers with authentication"""
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'AP-Manager/1.0'
        }
        if self.api_token:
            headers['Authorization'] = f'Bearer {self.api_token}'
        return headers

    async def send_device_update(self, device_data: Dict[str, Any]) -> bool:
        """Send device update to Django API"""
        try:
            async with self.session.post(
                f'{self.base_url}/api/devices/update/',
                json=device_data
            ) as response:
                return response.status == 200
        except Exception as e:
            print(f"Error sending device update: {e}")
            return False

    async def authenticate_device(self, mac: str,
                                  hook: Optional[str] = None) -> Dict[str, Any]:
        """Authenticate device via API"""
        data = {'mac': mac.lower()}
        if hook:
            data['callback_url'] = hook

        try:
            async with self.session.post(
                f'{self.base_url}/api/devices/authenticate/',
                json=data
            ) as response:
                if response.status == 200:
                    result = await response.json()

                    # Also send webhook if provided
                    if hook and result.get('success'):
                        await self._send_webhook(hook, {
                            'mac': mac,
                            'status': 'authenticated',
                            'timestamp': result.get('timestamp')
                        })

                    return result
                return {'success': False, 'error': f'HTTP {response.status}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def block_device(self, mac: str,
                           hook: Optional[str] = None) -> Dict[str, Any]:
        """Block device via API"""
        data = {'mac': mac.lower()}
        if hook:
            data['callback_url'] = hook

        try:
            async with self.session.post(
                f'{self.base_url}/api/devices/block/',
                json=data
            ) as response:
                if response.status == 200:
                    result = await response.json()

                    # Send webhook if provided
                    if hook and result.get('success'):
                        await self._send_webhook(hook, {
                            'mac': mac,
                            'status': 'blocked',
                            'timestamp': result.get('timestamp')
                        })

                    return result
                return {'success': False, 'error': f'HTTP {response.status}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def get_device_status(self, mac: str,
                                hook: Optional[str] = None) -> Dict[str, Any]:
        """Get device status from API"""
        try:
            async with self.session.get(
                f'{self.base_url}/api/devices/{mac}/status/'
            ) as response:
                if response.status == 200:
                    result = await response.json()

                    # Send webhook if provided
                    if hook:
                        await self._send_webhook(hook, result)

                    return result
                return {'authenticated': False, 'error': f'HTTP {response.status}'}
        except Exception as e:
            return {'authenticated': False, 'error': str(e)}

    async def _send_webhook(self, url: str, data: Dict[str, Any]) -> bool:
        """Send webhook callback"""
        try:
            async with self.session.post(url, json=data) as response:
                return response.status in [200, 201, 202]
        except:
            return False

    async def connect_websocket(self):
        """Connect to Django WebSocket for real-time updates"""
        try:
            headers = self._get_headers()
            self.ws_connection = await websockets.connect(
                self.ws_url,
                additional_headers=headers
            )
            print(f"✅ Connected to WebSocket: {self.ws_url}")

            # Send registration message
            await self.ws_connection.send(json.dumps({
                'type': 'register',
                'client': 'ap_manager',
                'action': 'monitoring'
            }))

            # Start listening
            await self._listen_websocket()

        except Exception as e:
            print(f"❌ WebSocket connection failed: {e}")

    async def _listen_websocket(self):
        """Listen for WebSocket messages"""
        try:
            async for message in self.ws_connection:
                await self._handle_websocket_message(message)
        except websockets.exceptions.ConnectionClosed:
            print("WebSocket connection closed")
        except Exception as e:
            print(f"WebSocket error: {e}")

    async def _handle_websocket_message(self, message: str):
        """Handle incoming WebSocket message"""
        try:
            data = json.loads(message)
            message_type = data.get('type')

            if message_type == 'command':
                # Handle commands from Django
                command = data.get('command')
                if command == 'authenticate':
                    mac = data.get('mac')
                    if mac:
                        await self.authenticate_device(mac)
                elif command == 'block':
                    mac = data.get('mac')
                    if mac:
                        await self.block_device(mac)
                elif command == 'refresh':
                    # Trigger device scan
                    self._trigger_callback('hotspot_status', {})

            elif message_type == 'notification':
                # Forward to callbacks
                event = data.get('event')
                payload = data.get('data', {})
                if event in self.callbacks:
                    self._trigger_callback(event, payload)

        except json.JSONDecodeError:
            print(f"Invalid JSON message: {message}")

    def register_callback(self, event: str, callback: Callable):
        """Register callback for events"""
        if event in self.callbacks:
            self.callbacks[event].append(callback)

    def _trigger_callback(self, event: str, data: Dict[str, Any]):
        """Trigger registered callbacks"""
        for callback in self.callbacks.get(event, []):
            try:
                callback(data)
            except Exception as e:
                print(f"Callback error: {e}")

    def start_monitoring(self):
        """Start monitoring loop"""
        self.running = True

        async def monitor():
            await self.initialize()
            await self.connect_websocket()

            # Keep connection alive
            while self.running:
                try:
                    # Send heartbeat
                    if self.ws_connection:
                        await self.ws_connection.send(json.dumps({
                            'type': 'heartbeat',
                            'timestamp': asyncio.get_event_loop().time()
                        }))

                    await asyncio.sleep(30)  # Heartbeat every 30s

                except Exception as e:
                    print(f"Monitoring error: {e}")
                    await asyncio.sleep(5)

        # Run in background thread
        thread = threading.Thread(
            target=lambda: asyncio.run(monitor()),
            daemon=True
        )
        thread.start()
        print("✅ Monitoring started")

    def stop_monitoring(self):
        """Stop monitoring"""
        self.running = False
        if self.session:
            asyncio.run(self.session.close())
        print("⏹️ Monitoring stopped")
