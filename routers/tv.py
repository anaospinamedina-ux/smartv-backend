from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from auth import verify_token
from hub_manager import hub_manager

router = APIRouter(prefix="/tv", tags=["tv"])

SAMSUNG_APP_IDS = {
    "netflix": "11101200001",
    "spotify": "3201606009684",
    "youtube": "111299001912",
}


class PowerRequest(BaseModel):
    state: str  # "on" | "off"


async def _send_or_raise(payload: dict):
    sent = await hub_manager.send_command(payload)
    if not sent:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Hub is not connected",
        )


@router.post("/power")
async def tv_power(body: PowerRequest, _: str = Depends(verify_token)):
    if body.state not in ("on", "off"):
        raise HTTPException(status_code=400, detail="state must be 'on' or 'off'")
    await _send_or_raise({"type": "tv_power", "state": body.state})
    return {"ok": True}


@router.post("/app/{app_name}")
async def tv_app(app_name: str, _: str = Depends(verify_token)):
    app_id = SAMSUNG_APP_IDS.get(app_name.lower())
    if app_id is None:
        raise HTTPException(status_code=404, detail=f"Unknown app '{app_name}'")
    await _send_or_raise({"type": "tv_app", "app_id": app_id})
    return {"ok": True, "app": app_name}


@router.post("/key/{key_name}")
async def tv_key(key_name: str, _: str = Depends(verify_token)):
    await _send_or_raise({"type": "tv_key", "key": key_name})
    return {"ok": True, "key": key_name}


@router.get("/status")
async def hub_status(_: str = Depends(verify_token)):
    return {"hub_connected": hub_manager.is_connected}
