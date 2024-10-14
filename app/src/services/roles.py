"""
Module of role access class
"""


from typing import List

from fastapi import Depends, HTTPException, status

from app.src.database.models import User, Role
from app.src.services.auth import auth_service


class RoleAccess:
    def __init__(self, allowed_roles: List[Role]):
        self.allowed_roles = allowed_roles

    async def __call__(
        self, user: User = Depends(auth_service.get_current_user)
    ):
        if user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Operation forbidden"
            )