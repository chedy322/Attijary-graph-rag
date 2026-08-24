from pydantic import BaseModel, EmailStr
from datetime import datetime
from models.user import User


class AuthServiceDTO(BaseModel):
    user_id: str
    email: EmailStr
    role: str
    created_at: datetime

    @classmethod
    def map(cls, user: User):
        try:
            return cls(
                user_id=str(getattr(user, "user_id")),
                email=user.email,
                role=getattr(user, "role", "USER"),
                created_at=getattr(user, "created_at", datetime.utcnow()),
            )
        except Exception as e:
            raise ValueError(f"Error mapping user to AuthServiceDTO: {str(e)}")
