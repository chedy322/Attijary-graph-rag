import uuid

from core.exceptions import AppError
from models.user import User
from config.clerk import clerk_client
from config.database import db
from services.dto.auth_service_dto import AuthServiceDTO
from flask import g
import logging
import datetime
audit_logger = logging.getLogger("audit")

class AuthService:
    def __init__(self, clerk_client, db):
        self.clerk_client = clerk_client
        self.db = db

    def sync_user(self,extra_data: dict = None) -> AuthServiceDTO:
        """
        Ensures the authenticated Clerk user exists in the local database.
        Creates a new local user record if they are logging in for the first time.
        """
        try:
            clerk_user_id = g.user_id

            # 1. Check if the user already exists in the database by CLERK_ID
            existing_user = (
                self.db.session.query(User).filter_by(clerk_id=clerk_user_id).first()
            )
            if existing_user:
                audit_logger.info("User log in successful", extra=
                                  {"audit": {
                                      "id":uuid.uuid4(),
                    "actor_id": existing_user.user_id, 
                 "action": "LOGIN",
                  "details": "User logged in successfully.",
                  "target_id": existing_user.user_id, 
                  "target_resource": "User",
                  "ip_address": extra_data.get("ip_address") if extra_data else None,
                  "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
                  }
                }
                  )
                # User exists, no need to make an expensive network call to Clerk
                return AuthServiceDTO.map(existing_user)

            # 2. If the user does not exist, they are new to  backend.
            user_data = self.clerk_client.get_user(user_id=clerk_user_id)
            if not user_data:
                raise AppError("User not found in Clerk", 404)

            # 3. Safely extract the primary email from Clerk's data structure
            primary_email = ""
            for email_obj in getattr(user_data, "email_addresses", []):
                if email_obj.id == getattr(user_data, "primary_email_address_id", None):
                    primary_email = email_obj.email_address
                    break

            # Fallback in case primary_email_address_id isn't set but emails exist
            if not primary_email and getattr(user_data, "email_addresses", None):
                primary_email = user_data.email_addresses[0].email_address

            # 4. Create the new user in the database
            new_user = User(
                clerk_id=clerk_user_id,
                firstname=getattr(user_data, "first_name", ""),
                lastname=getattr(user_data, "last_name", ""),
                email=primary_email,
            )

            self.db.session.add(new_user)
            self.db.session.commit()

            audit_logger.info("User registered successfullly", extra={"audit":
                              {
                "id":uuid.uuid4(),
                "user_id": new_user.user_id, 
             "action": "REGISTER",
                "details": "User registered successfully.",
                "target_id": new_user.user_id,
                "target_resource": "User",
                "ip_address": extra_data.get("ip_address") if extra_data else None,
                "created_at": datetime.datetime.utcnow()
                }
                }
                  )
            return AuthServiceDTO.map(new_user)
        except AppError as e:
            self.db.session.rollback()
            raise
        except Exception as e:
            self.db.session.rollback()
            raise AppError(f"User synchronization failed: {str(e)}", 500)


auth_service = AuthService(clerk_client=clerk_client, db=db)
