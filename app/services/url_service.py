import secrets
import string
import logging
from peewee import IntegrityError
from app.models.urls import Url
from app.services.cache import cache

logger = logging.getLogger(__name__)


def _extract_constraint_name(exc):
    wrapped_exc = getattr(exc, "__cause__", None) or getattr(exc, "orig", None)
    if wrapped_exc is not None:
        diag = getattr(wrapped_exc, "diag", None)
        if diag is not None:
            return getattr(diag, "constraint_name", None)
    return None


# Define this here so app.services can import it
class UrlConflictError(Exception):
    pass

class UrlService:
    def __init__(self):
        self.cache = cache

    def _generate_shortcode(self, length=6):
        chars = string.ascii_letters + string.digits
        return ''.join(secrets.choice(chars) for _ in range(length))

    def serialize_url(self, url):
        return {
            "id": url.id,
            "user_id": url.user_id,
            "shortcode": url.shortcode,
            "short_code": url.shortcode, # Satisfy test expectation
            "original_url": url.original_url,
            "title": url.title,
            "is_active": url.is_active,
            "created_at": url.created_at.isoformat() if url.created_at else None,
            "updated_at": url.updated_at.isoformat() if url.updated_at else None,
        }

    def create_url(self, data):
        original_url = data.get("original_url")
        user_id = data.get("user_id")
        
        if not original_url or not user_id:
            raise ValueError("original_url and user_id are required")

        shortcode = data.get("shortcode") or self._generate_shortcode()

        try:
            url = Url.create(
                user_id=user_id,
                shortcode=shortcode,
                original_url=original_url,
                title=data.get("title")
            )
            serialized_url = self.serialize_url(url)
            self.cache.invalidate_namespace("urls")
            return serialized_url
        except IntegrityError as exc:
            constraint_name = _extract_constraint_name(exc)
            error_text = str(exc).lower()

            # Recover from PK sequence drift and retry once.
            if (constraint_name and "urls_pkey" in constraint_name) or "urls_pkey" in error_text:
                Url._meta.database.execute_sql(
                    """
                    SELECT setval(
                        pg_get_serial_sequence('urls', 'id'),
                        COALESCE((SELECT MAX(id) FROM urls), 1),
                        true
                    )
                    """
                )
                try:
                    url = Url.create(
                        user_id=user_id,
                        shortcode=shortcode,
                        original_url=original_url,
                        title=data.get("title")
                    )
                    return self.serialize_url(url)
                except IntegrityError as retry_exc:
                    raise UrlConflictError("shortcode already exists") from retry_exc

            if (constraint_name and "shortcode" in constraint_name) or "shortcode" in error_text:
                raise UrlConflictError("shortcode already exists") from exc

            raise UrlConflictError("database integrity conflict") from exc

    def list_urls(self, user_id=None, is_active=None):
        normalized_user_id = str(user_id) if user_id is not None else "all"
        normalized_status = "default" if is_active is None else str(is_active).lower()
        cached_urls = self.cache.get_json("urls", "list", normalized_user_id, normalized_status)
        if cached_urls is not None:
            return cached_urls

        try:
            query = Url.select()
            if user_id:
                query = query.where(Url.user_id == user_id)
            
            # Default to only active URLs unless explicitly set
            if is_active is None:
                query = query.where(Url.is_active)
            else:
                # Handle both boolean and string "true"/"false"
                status = str(is_active).lower() == 'true' if isinstance(is_active, str) else bool(is_active)
                if status:
                    query = query.where(Url.is_active)
                else:
                    query = query.where(~Url.is_active)
            
            urls = [self.serialize_url(u) for u in query]
            self.cache.set_json("urls", "list", normalized_user_id, normalized_status, value=urls)
            return urls
        except Exception as exc:
            logger.exception("Failed to list URLs with user_id=%s, is_active=%s", user_id, is_active)
            return []

    def get_url_by_id(self, url_id):
        cached_url = self.cache.get_json("urls", "detail", url_id)
        if cached_url is not None:
            return cached_url

        url = Url.get_or_none(Url.id == url_id)
        if not url:
            return None

        serialized_url = self.serialize_url(url)
        self.cache.set_json("urls", "detail", url_id, value=serialized_url)
        return serialized_url

    def update_url(self, url_id, data):
        url = Url.get_or_none(Url.id == url_id)
        if not url: 
            return None
        
        if "title" in data: 
            url.title = data["title"]
        if "is_active" in data: 
            url.is_active = data["is_active"]
        
        url.save()
        serialized_url = self.serialize_url(url)
        self.cache.invalidate_namespace("urls")
        return serialized_url

    def delete_url(self, url_id):
        url = Url.get_or_none(Url.id == url_id)
        if url:
            url.delete_instance()
            self.cache.invalidate_namespace("urls")
            return True
        return False

    def resolve_shortcode(self, shortcode):
        cached_url = self.cache.get_json("urls", "shortcode", shortcode)
        if cached_url is not None:
            return cached_url

        url = Url.get_or_none((Url.shortcode == shortcode) & (Url.is_active))
        if not url:
            return None

        original_url = url.original_url
        self.cache.set_json("urls", "shortcode", shortcode, value=original_url)
        return original_url