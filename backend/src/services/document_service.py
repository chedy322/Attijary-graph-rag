# backend/services/document_service.py
import uuid
from datetime import datetime, timezone
from typing import Optional, Tuple, List

from models.user import User

from config.database import db
from core.exceptions import AppError
from models.document import Document, DocumentStatus, DocumentOrigin


class DocumentService:
    """CRUD + business logic for the Document entity."""

    def get_user_id_from_clerk_id(self, clerk_id: str):
        user = db.session.query(User).filter_by(clerk_id=clerk_id).first()
        return user.user_id if user else None

    # ── Read ──────────────────────────────────────────────────────────────────
    def get_documents(
        self,
        page: int = 1,
        limit: int = 10,
        status: Optional[str] = None,
    ) -> Tuple[List[Document], int]:
        """Return a paginated list of documents and the total count."""
        query = db.session.query(Document)

        if status:
            try:
                status_enum = DocumentStatus(status)
                query = query.filter(Document.status == status_enum)
            except ValueError:
                raise AppError(f"Invalid status value: '{status}'", 400)

        total = query.count()
        items = (
            query.order_by(Document.date.desc())
            .offset((page - 1) * limit)
            .limit(limit)
            .all()
        )
        return items, total

    def get_document_by_id(self, document_id) -> Optional[Document]:
        """Fetch a single document by its UUID primary key."""
        return db.session.query(Document).filter_by(document_id=document_id).first()

    def get_document_by_id_and_clerk_user_id(
        self, document_id, clerk_user_id
    ) -> Optional[Document]:
        """Fetch a single document by its UUID primary key and user ID."""
        user_id = self.get_user_id_from_clerk_id(clerk_user_id)
        return (
            db.session.query(Document)
            .filter_by(document_id=document_id, uploaded_by_user_id=user_id)
            .first()
        )

    # ── Create ────────────────────────────────────────────────────────────────

    def create_document(
        self,
        document_id: uuid.UUID,
        file_path: str,
        filename: str,
        title: str,
        uploaded_by_user_id: Optional[str] = None,
        number: Optional[str] = None,
        category: Optional[str] = None,
    ) -> Document:
        """
        Insert a new Document row with status PENDING_UPLOAD.
        The file_path is deterministic: documents/<uuid>.<extension>
        """
        try:
            # Extract extension from the original filename
            extension = (
                filename.rsplit(".", 1)[-1].lower() if "." in filename else "bin"
            )
            user_id = (
                self.get_user_id_from_clerk_id(uploaded_by_user_id)
                if uploaded_by_user_id
                else None
            )
            # Parse the date string — accept ISO 8601
            # parsed_date = datetime.fromisoformat(date).replace(tzinfo=timezone.utc)

            document = Document(
                document_id=document_id,
                file_path=file_path,
                title=title,
                number=number,
                category=category,
                file_extension=extension,
                status=DocumentStatus.PENDING_UPLOAD,
                origin=DocumentOrigin.MANUAL,
                uploaded_by_user_id=user_id,
            )

            db.session.add(document)
            db.session.commit()
            return document

        except AppError:
            db.session.rollback()
            raise
        except Exception as e:
            db.session.rollback()
            raise AppError(f"Failed to create document: {str(e)}", 500) from e

    # ── Update ────────────────────────────────────────────────────────────────

    def update_status(self, document_id, new_status: str) -> Document:
        """Update a document's status enum by string value."""
        try:
            status_enum = DocumentStatus(new_status)
        except ValueError:
            raise AppError(f"Invalid status value: '{new_status}'", 400)

        try:
            document = self.get_document_by_id(document_id)
            if not document:
                raise AppError("Document not found", 404)

            document.status = status_enum
            db.session.commit()
            return document

        except AppError:
            db.session.rollback()
            raise
        except Exception as e:
            db.session.rollback()
            raise AppError(f"Failed to update document status: {str(e)}", 500) from e

    def delete_document(self, document_id) -> None:
        """Delete a document by its UUID primary key."""
        try:
            document = self.get_document_by_id(document_id)
            if not document:
                raise AppError("Document not found", 404)

            db.session.delete(document)
            db.session.commit()

        except AppError:
            db.session.rollback()
            raise
        except Exception as e:
            db.session.rollback()
            raise AppError(f"Failed to delete document: {str(e)}", 500) from e


document_service = DocumentService()
