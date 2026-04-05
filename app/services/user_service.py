from peewee import IntegrityError
from app.models.users import User
import csv
import os
from app.models.users import User
from app.database import db

class UserConflictError(Exception):
    pass


def _extract_constraint_name(exc):
    wrapped_exc = getattr(exc, "__cause__", None) or getattr(exc, "orig", None)
    if wrapped_exc is not None:
        diag = getattr(wrapped_exc, "diag", None)
        if diag is not None:
            return getattr(diag, "constraint_name", None)
    return None


def _classify_user_integrity_error(exc):
    constraint_name = _extract_constraint_name(exc)
    error_text = str(exc).lower()

    if constraint_name and "email" in constraint_name:
        return "email already exists"

    if constraint_name and "users_pkey" in constraint_name:
        return "user id sequence is out of sync"

    if "email" in error_text and "duplicate" in error_text:
        return "email already exists"

    if "users_pkey" in error_text or "duplicate key value" in error_text:
        return "user id sequence is out of sync"

    return "database integrity conflict"

class UserService:
    def serialize_user(self, user):
        return {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "created_at": user.created_at.isoformat() if hasattr(user.created_at, 'isoformat') else str(user.created_at),
            "updated_at": user.updated_at.isoformat() if hasattr(user.updated_at, 'isoformat') else str(user.updated_at),
            "is_active": user.is_active,
        }

    def list_users(self, page=1, per_page=10):
        """
        Updated to handle pagination. Fixes test_get_users_pagination.
        """
        # .paginate(page_number, items_per_page) is built into Peewee
        users = User.select().where(User.is_active).order_by(User.id).paginate(page, per_page)
        return [self.serialize_user(user) for user in users]

    def bulk_create_users(self, file_name, row_count):
        """
        Processes the CSV file. Fixes test_load_users_csv.
        """
        file_path = os.path.join(os.getcwd(), file_name)
        
        if not os.path.exists(file_path):
            # If the file isn't in root, check if it's in a /data folder
            file_path = os.path.join(os.getcwd(), 'data', file_name)
            if not os.path.exists(file_path):
                raise ValueError(f"File {file_name} not found")

        users_to_create = []
        try:
            with open(file_path, mode='r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for i, row in enumerate(reader):
                    if i >= row_count:
                        break
                    
                    # Map CSV columns (handling 'username' alias)
                    users_to_create.append({
                        'name': row.get('name') or row.get('username'),
                        'email': row.get('email'),
                        'password_hash': row.get('password') or 'default_pw_123'
                    })

            # Use bulk insert for speed
            if users_to_create:
                with db.atomic():
                    User.insert_many(users_to_create).on_conflict_ignore().execute()

            return {"message": "Bulk upload successful", "count": len(users_to_create)}
        except Exception as e:
            raise ValueError(f"CSV Error: {str(e)}")

    def get_user(self, user_id):
        user = User.get_or_none((User.id == user_id) & (User.is_active))
        if user is None:
            return None
        return self.serialize_user(user)

    def create_user(self, data):
        name = data.get("name")
        email = data.get("email")
        password = data.get("password")

        if not name or not email or not password:
            raise ValueError("name, email, and password are required")

        try:
            user = User.create(
                name=name,
                email=email,
                password_hash=password,
            )
        except IntegrityError as exc:
            raise UserConflictError(_classify_user_integrity_error(exc)) from exc

        return self.serialize_user(user)

    def update_user(self, user_id, data):
        user = User.get_or_none((User.id == user_id) & (User.is_active))
        if user is None:
            return None

        name = data.get("name")
        email = data.get("email")

        if name is None and email is None:
            raise ValueError("At least one updatable field is required")

        if name is not None:
            user.name = name

        if email is not None:
            user.email = email

        try:
            user.save()
        except IntegrityError as exc:
            raise UserConflictError(_classify_user_integrity_error(exc)) from exc

        return self.serialize_user(user)

    def delete_user(self, user_id):
        user = User.get_or_none((User.id == user_id) & (User.is_active))
        if user is None:
            return False

        user.is_active = False
        user.save()
        return True