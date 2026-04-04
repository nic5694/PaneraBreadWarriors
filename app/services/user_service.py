from peewee import IntegrityError

from app.models.users import User


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
            "created_at": user.created_at.isoformat(),
            "updated_at": user.updated_at.isoformat(),
            "is_active": user.is_active,
        }

    def list_users(self):
        users = User.select().order_by(User.id)
        return [self.serialize_user(user) for user in users]

    def get_user(self, user_id):
        user = User.get_or_none((User.id == user_id) & (User.is_active == True))
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
        user = User.get_or_none((User.id == user_id) & (User.is_active == True))
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
        user = User.get_or_none((User.id == user_id) & (User.is_active == True))
        if user is None:
            return False

        user.is_active = False
        user.save()
        return True
