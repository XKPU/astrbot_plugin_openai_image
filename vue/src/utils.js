/* Shared helpers for list and dict typed config fields. */

export function splitLines(value) {
  return String(value == null ? "" : value)
    .split(/[\n,]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

export function jsonText(value) {
  /* Already-edited fields hold JSON text, so the conversion stays idempotent. */
  if (typeof value === "string") return value.trim();
  if (!value || typeof value !== "object" || Array.isArray(value)) return "";
  return Object.keys(value).length ? JSON.stringify(value, null, 2) : "";
}

export function parseJsonObject(text) {
  const raw = String(text == null ? "" : text).trim();
  if (!raw) return { ok: true, value: {} };
  try {
    const parsed = JSON.parse(raw);
    if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
      return { ok: true, value: parsed };
    }
  } catch (err) {
    /* Report the failure to the caller, which shows the localised message. */
  }
  return { ok: false, value: {} };
}
