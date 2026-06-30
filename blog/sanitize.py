import re

import bleach
from markupsafe import Markup

ALLOWED_TAGS = [
    "p", "br", "strong", "b", "em", "i", "u", "s", "strike",
    "h1", "h2", "h3", "ol", "ul", "li", "a", "blockquote", "pre", "code",
]
ALLOWED_ATTRS = {"a": ["href", "target", "rel"]}
ALLOWED_PROTOCOLS = ["http", "https", "mailto"]


def sanitize_html(dirty):
    return bleach.clean(
        dirty or "",
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRS,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
    )


def strip_html(text):
    return bleach.clean(text or "", tags=[], strip=True).strip()


def is_body_empty(html):
    return not strip_html(html)


def looks_like_html(text):
    return bool(re.search(r"<[a-z][\s\S]*>", text or "", re.I))


def render_post_body(body):
    if looks_like_html(body):
        return Markup(sanitize_html(body))
    return body
