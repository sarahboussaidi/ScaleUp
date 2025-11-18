from channels.generic.websocket import AsyncWebsocketConsumer
import json

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # room_name passed in URL, e.g. ws/chat/question_5/
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.group_name = self.room_name
        # join group
        try:
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()
            print(f"[ChatConsumer] Accepted WS connection for group={self.group_name}")
        except Exception as e:
            # log to server console for debugging
            print(f"[ChatConsumer] connect error for group={self.group_name}: {e}")
            raise

    async def disconnect(self, close_code):
        # leave group
        try:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
            print(f"[ChatConsumer] Disconnected WS for group={self.group_name} code={close_code}")
        except Exception as e:
            print(f"[ChatConsumer] disconnect error for group={self.group_name}: {e}")

    # receive message from WebSocket (clients shouldn't need to send for this use-case)
    async def receive(self, text_data=None, bytes_data=None):
        # echo or ignore
        # optional: log client messages for debugging
        if text_data:
            print(f"[ChatConsumer] receive from client in {self.group_name}: {text_data}")
        return

    # receive message from group
    async def new_response(self, event):
        # forward to WebSocket client
        payload = event.get('payload', {})
        await self.send(text_data=json.dumps({
            'type': 'new_response',
            'payload': payload,
        }))
