import { reactive } from "vue";
import { t } from "./i18n.js";
import { apiGet, apiPost, bridgeReady, pick } from "./sdk.js";
import { jsonText, splitLines } from "./utils.js";

/* Defaults mirror _conf_schema.json so the page works against an older
 * persisted config that predates some keys. */
export const DEFAULT_CONFIG = {
  sources: [],
  model_order: [],
  model_disabled: [],
  generation_prompt: "",
  edit_prompt: "",
  enable_generation: true,
  enable_edit: true,
  enable_prompt_polish: true,
  available_aspect_ratios: ["1024x1024", "1536x1024", "1024x1536"],
  aspect_ratio_field: "size",
  response_image_path: "data",
  timeout: 300,
  extra_request_body: "",
  return_elapsed: false,
  return_id: false,
  return_model: false,
  return_retries: false,
  enable_commands: true,
  command_prefix: "/",
  command_generation_head: ["t2i"],
  command_edit_head: ["i2i"],
  command_enable_polish: false,
  command_polish_provider: "",
  command_arg_mode: "listed",
  command_allowed_args: ["size"],
  access_group_mode: "off",
  access_group_ids: [],
  access_user_mode: "off",
  access_user_ids: [],
  quota_daily_limit: 0,
  checkin_enabled: false,
  checkin_heads: ["checkin"],
  checkin_bonus: 1,
  checkin_success: "签到成功，获得 {{count}} 次调用次数，今日剩余 {{remaining}} 次。",
  checkin_fail: "今天已经签到过了，明天再来吧。",
};

export const store = reactive({
  tab: "sources",
  config: JSON.parse(JSON.stringify(DEFAULT_CONFIG)),
  baseline: null,
  providers: [],
  version: "",
  dirty: false,
  busy: false,
  alert: null,
});

export function markDirty() {
  store.dirty = true;
}

export function showAlert(kind, text) {
  store.alert = { kind, text };
}

/* Model entries are persisted as "id" or "id:retries" strings because the
 * declarative settings page renders list items verbatim; the editor keeps
 * them as objects so each field stays reactive. */
export function toEditableModel(entry) {
  if (entry && typeof entry === "object") {
    return {
      id: String(entry.id == null ? "" : entry.id).trim(),
      retries: Number(entry.retries) > 0 ? Number(entry.retries) : 0,
    };
  }
  const text = String(entry == null ? "" : entry).trim();
  if (!text) return { id: "", retries: 0 };
  const index = text.lastIndexOf(":");
  if (index > 0) {
    const retries = parseInt(text.slice(index + 1), 10);
    if (!isNaN(retries) && retries > 0) {
      return { id: text.slice(0, index).trim(), retries };
    }
  }
  return { id: text, retries: 0 };
}

export function toEditableSource(source) {
  const item = source && typeof source === "object" ? source : {};
  return {
    name: String(item.name == null ? "" : item.name),
    api_base: String(item.api_base == null ? "" : item.api_base),
    api_keys: Array.isArray(item.api_keys)
      ? item.api_keys.map((key) => String(key == null ? "" : key))
      : splitLines(item.api_keys),
    models: (Array.isArray(item.models) ? item.models : splitLines(item.models)).map(
      toEditableModel,
    ),
    enable_generation: item.enable_generation !== false,
    enable_edit: item.enable_edit !== false,
    aspect_ratios: Array.isArray(item.aspect_ratios)
      ? item.aspect_ratios.map((value) => String(value))
      : splitLines(item.aspect_ratios),
    aspect_ratio_field: String(item.aspect_ratio_field == null ? "" : item.aspect_ratio_field),
    validate_aspect_ratio: item.validate_aspect_ratio !== false,
    response_image_path: String(item.response_image_path == null ? "" : item.response_image_path),
    generation_prompt: String(item.generation_prompt == null ? "" : item.generation_prompt),
    edit_prompt: String(item.edit_prompt == null ? "" : item.edit_prompt),
    extra_request_body: jsonText(item.extra_request_body),
    timeout: Number(item.timeout) > 0 ? Number(item.timeout) : 0,
    enabled: item.enabled !== false,
  };
}

export function applyConfig(config) {
  const merged = JSON.parse(JSON.stringify(DEFAULT_CONFIG));
  if (config && typeof config === "object") {
    Object.keys(config).forEach((key) => {
      if (config[key] !== undefined && config[key] !== null) merged[key] = config[key];
    });
  }
  merged.sources = (Array.isArray(merged.sources) ? merged.sources : []).map(toEditableSource);
  /* The dict field is edited as JSON text, so it must leave the editor as a string. */
  merged.extra_request_body = jsonText(merged.extra_request_body);
  store.config = merged;
  store.baseline = JSON.stringify(merged);
  store.dirty = false;
}

/* Restore the config as it was loaded, dropping every unsaved edit. */
export function discardEdits() {
  if (!store.baseline) return;
  const restored = JSON.parse(store.baseline);
  restored.sources = (Array.isArray(restored.sources) ? restored.sources : []).map(toEditableSource);
  store.config = restored;
  store.dirty = false;
  store.alert = null;
}

function normalizeVersion(value) {
  const text = String(value == null ? "" : value).trim();
  if (!text) return "";
  return "v" + text.replace(/^v+/i, "");
}

export async function loadAll() {
  store.busy = true;
  try {
    await bridgeReady();
    const [config, providers, version] = await Promise.all([
      apiGet("config").catch(() => null),
      apiGet("providers").catch(() => null),
      apiGet("version").catch(() => null),
    ]);
    const configData = pick(config);
    if (!configData) {
      // Keep the current form instead of blanking it on a failed read.
      showAlert("err", t("loadEmpty"));
      return;
    }
    applyConfig(configData);
    const providerData = pick(providers);
    store.providers = (providerData && providerData.providers) || [];
    const versionData = pick(version);
    store.version = normalizeVersion(versionData && versionData.version);
    store.alert = null;
  } catch (err) {
    showAlert("err", t("loadFailed") + (err && err.message ? err.message : String(err)));
  } finally {
    store.busy = false;
  }
}

export async function saveConfig(config) {
  store.busy = true;
  try {
    const response = await apiPost("config", { config: JSON.parse(JSON.stringify(config)) });
    if (response && response.status === "error") {
      throw new Error(response.message || "save failed");
    }
    const fresh = await apiGet("config").catch(() => null);
    const data = pick(fresh);
    if (data) applyConfig(data);
    else store.dirty = false;
    showAlert("ok", t("saved"));
  } catch (err) {
    showAlert("err", t("saveFailed") + (err && err.message ? err.message : String(err)));
  } finally {
    store.busy = false;
  }
}

/* Normalisers keep the persisted shape stable: list fields always store an
 * array, enum fields fall back to the documented default. */
export function normalizeList(value, fallback) {
  const list = Array.isArray(value) ? value : splitLines(value);
  const cleaned = list.map((item) => String(item).trim()).filter(Boolean);
  return cleaned.length ? cleaned : fallback.slice();
}

export function normalizeMode(value, allowed, fallback) {
  const mode = String(value == null ? "" : value).trim().toLowerCase();
  return allowed.indexOf(mode) >= 0 ? mode : fallback;
}
