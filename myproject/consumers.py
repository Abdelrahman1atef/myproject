# myproject/consumers.py

import json
from channels.generic.websocket import AsyncWebsocketConsumer

class OrderConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = "orders"
        await self.accept()  # MUST ACCEPT FIRST
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
    async def disconnect(self, close_code):
        # This is where we remove the WebSocket connection from the group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name,
        )

    async def receive(self, text_data):
        # Optionally handle incoming WebSocket messages here
        pass

    async def order_notification(self, event):
        # This function will send the order notification to the WebSocket
        message = event.get("message", "")
        await self.send(text_data=json.dumps({
            'type': 'order_notification',
            'message': message,
        }))