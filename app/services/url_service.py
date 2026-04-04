import secrets
import string
from peewee import IntegrityError
from app.models.urls import Url

# Define this here so app.services can import it
class UrlConflictError(Exception):
    pass

class UrlService:
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
            return self.serialize_url(url)
        except IntegrityError:
            raise UrlConflictError("Shortcode already exists")

    def list_urls(self, user_id=None, is_active=None):
        query = Url.select()
        if user_id:
            query = query.where(Url.user_id == user_id)
        if is_active is not None:
            # Handle both boolean and string "true"/"false"
            status = str(is_active).lower() == 'true' if isinstance(is_active, str) else bool(is_active)
            query = query.where(Url.is_active == status)
        
        return [self.serialize_url(u) for u in query]

    def get_url_by_id(self, url_id):
        url = Url.get_or_none(Url.id == url_id)
        return self.serialize_url(url) if url else None

    def update_url(self, url_id, data):
        url = Url.get_or_none(Url.id == url_id)
        if not url: 
            return None
        
        if "title" in data: 
            url.title = data["title"]
        if "is_active" in data: 
            url.is_active = data["is_active"]
        
        url.save()
        return self.serialize_url(url)

    def delete_url(self, url_id):
        url = Url.get_or_none(Url.id == url_id)
        if url:
            url.delete_instance()
            return True
        return False

    def resolve_shortcode(self, shortcode):
        url = Url.get_or_none((Url.shortcode == shortcode) & (Url.is_active == True))
        return url.original_url if url else None