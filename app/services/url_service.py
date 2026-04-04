from peewee import IntegrityError

from app.models.urls import Url


class UrlConflictError(Exception):
    pass


def _extract_constraint_name(exc):
    wrapped_exc = getattr(exc, "__cause__", None) or getattr(exc, "orig", None)
    if wrapped_exc is not None:
        diag = getattr(wrapped_exc, "diag", None)
        if diag is not None:
            return getattr(diag, "constraint_name", None)
    return None


def _classify_url_integrity_error(exc):
    constraint_name = _extract_constraint_name(exc)
    error_text = str(exc).lower()

    if constraint_name and "shortcode" in constraint_name:
        return "shortcode already exists"

    if constraint_name and "urls_pkey" in constraint_name:
        return "url id sequence is out of sync"

    if "shortcode" in error_text and "duplicate" in error_text:
        return "shortcode already exists"

    if "urls_pkey" in error_text or "duplicate key value" in error_text:
        return "url id sequence is out of sync"

    return "database integrity conflict"


class UrlService:
    def serialize_url(self, url):
        return {
            "id": url.id,
            "user_id": url.user_id,
            "shortcode": url.shortcode,
            "original_url": url.original_url,
            "title": url.title,
            "is_active": url.is_active,
            "created_at": url.created_at.isoformat(),
            "updated_at": url.updated_at.isoformat(),
        }

    def create_url(self, data):
        user_id = data.get("user_id")
        shortcode = data.get("shortcode")
        original_url = data.get("original_url")

        if not user_id or not shortcode or not original_url:
            raise ValueError("user_id, shortcode, and original_url are required")

        try:
            url = Url.create(
                user_id=user_id,
                shortcode=shortcode,
                original_url=original_url,
                title=data.get("title"),
            )
        except IntegrityError as exc:
            raise UrlConflictError(_classify_url_integrity_error(exc)) from exc

        return self.serialize_url(url)

    def resolve_shortcode(self, shortcode):
        url = Url.get_or_none((Url.shortcode == shortcode) & (Url.is_active == True))
        if url is None:
            return None
        return url.original_url
