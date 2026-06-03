import os
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status

from hub_manager import hub_manager

router = APIRouter()
logger = logging.getLogger(__name__)

HUB_SECRET = os.getenv("HUB_SECRET", "change-hub-secret")


@router.websocket("/hub/connect")
async def hub_connect(ws: WebSocket, secret: str = Query(...)):
    if secret != HUB_SECRET:
        await ws.close(code=status.WS_1008_POLICY_VIOLATION)
        logger.warning("Hub connection rejected — wrong secret")
        return

    await hub_manager.connect(ws)
    logger.info("Raspberry Pi hub connected")
    try:
        while True:
            # Keep connection alive; hub may send heartbeat pings
            await ws.receive_text()
    except WebSocketDisconnect:
        await hub_manager.disconnect()
        logger.info("Raspberry Pi hub disconnected")
