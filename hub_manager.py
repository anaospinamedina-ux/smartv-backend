import asyncio
import json
from typing import Optional
from fastapi import WebSocket


class HubManager:
    """Holds the single active WebSocket connection from the Raspberry Pi hub."""

    def __init__(self):
        self._ws: Optional[WebSocket] = None
        self._lock = asyncio.Lock()

    async def connect(self, ws: WebSocket):
        await ws.accept()
        async with self._lock:
            if self._ws is not None:
                # Disconnect previous hub if a new one connects
                try:
                    await self._ws.close()
                except Exception:
                    pass
            self._ws = ws

    async def disconnect(self):
        async with self._lock:
            self._ws = None

    async def send_command(self, payload: dict) -> bool:
        async with self._lock:
            if self._ws is None:
                return False
            try:
                await self._ws.send_text(json.dumps(payload))
                return True
            except Exception:
                self._ws = None
                return False

    @property
    def is_connected(self) -> bool:
        return self._ws is not None


hub_manager = HubManager()
