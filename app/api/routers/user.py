from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends, status

from app.api.dependencies import verify_user
from app.db import User

router = APIRouter(prefix="/user", tags=["user"])


@router.get("/profile")
async def get_user(user: User = Depends(verify_user)) -> Dict[str, Any]:
    """Get info about current authorize user.

    Args:
        user: User object.

    Returns:
        dict[str, Any]: ID and role of user.
    """
    return {"id": user.id, "email": user.email, "username": user.username}
