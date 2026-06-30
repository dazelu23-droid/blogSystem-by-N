const ALLOWED_TAGS = new Set([
  "p", "br", "strong", "b", "em", "i", "u", "s", "strike",
  "h1", "h2", "h3", "ol", "ul", "li", "a", "blockquote", "pre", "code",
]);

const ALLOWED_ATTRS = {
  a: new Set(["href", "target", "rel"]),
};

const SAFE_URL_RE = /^(https?:|mailto:|#|\/)/i;

function stripDangerousBlocks(html) {
  return html
    .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, "")
    .replace(/<style\b[^<]*(?:(?!<\/style>)<[^<]*)*<\/style>/gi, "")
    .replace(/<iframe\b[^<]*(?:(?!<\/iframe>)<[^<]*)*<\/iframe>/gi, "");
}

function sanitizeAttrs(tag, attrs) {
  const allowed = ALLOWED_ATTRS[tag];
  if (!allowed) return "";
  const parts = [];
  for (const match of attrs.matchAll(/([a-z][a-z0-9-]*)\s*=\s*("([^"]*)"|'([^']*)'|([^\s>]+))/gi)) {
    const name = match[1].toLowerCase();
    if (!allowed.has(name)) continue;
    const value = (match[3] ?? match[4] ?? match[5] ?? "").trim();
    if (name === "href" && value && !SAFE_URL_RE.test(value)) continue;
    if (name === "target" && value !== "_blank") continue;
    if (name === "rel" && value !== "noopener noreferrer") continue;
    parts.push(`${name}="${value.replace(/"/g, "&quot;")}"`);
  }
  if (tag === "a" && parts.some((p) => p.startsWith('href="'))) {
    if (!parts.some((p) => p.startsWith('target="'))) {
      parts.push('target="_blank"');
    }
    if (!parts.some((p) => p.startsWith('rel="'))) {
      parts.push('rel="noopener noreferrer"');
    }
  }
  return parts.length ? " " + parts.join(" ") : "";
}

export function sanitizeHtml(dirty) {
  let html = stripDangerousBlocks(String(dirty || ""));
  html = html.replace(/\s+on\w+\s*=\s*("[^"]*"|'[^']*'|[^\s>]+)/gi, "");
  html = html.replace(/href\s*=\s*["']?\s*javascript:[^"'>]*/gi, 'href="#"');

  return html.replace(/<\/?([a-z][a-z0-9]*)\b([^>]*)>/gi, (full, tagName, attrs) => {
    const tag = tagName.toLowerCase();
    if (!ALLOWED_TAGS.has(tag)) {
      return full.startsWith("</") ? "" : "";
    }
    if (full.startsWith("</")) {
      return `</${tag}>`;
    }
    if (tag === "br") return "<br>";
    return `<${tag}${sanitizeAttrs(tag, attrs)}>`;
  });
}

export function stripHtml(text) {
  return String(text || "").replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim();
}

export function isBodyEmpty(html) {
  return stripHtml(html).length === 0;
}

export function looksLikeHtml(text) {
  return /<[a-z][\s\S]*>/i.test(String(text || ""));
}

export function renderPostBody(body) {
  if (looksLikeHtml(body)) {
    return sanitizeHtml(body);
  }
  return String(body || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
