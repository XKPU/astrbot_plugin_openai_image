import { t } from "./i18n.js";
import { normalizeList, normalizeMode } from "./store.js";
import { parseJsonObject, splitLines } from "./utils.js";

export const ARG_MODES = ["off", "all", "listed"];
export const LIST_MODES = ["off", "whitelist", "blacklist"];

function collectSource(source) {
  const models = [];
  (Array.isArray(source.models) ? source.models : []).forEach((item) => {
    const id = String(item.id == null ? "" : item.id).trim();
    if (!id) return;
    const retries = parseInt(item.retries, 10);
    models.push(!isNaN(retries) && retries > 0 ? `${id}:${retries}` : id);
  });
  return {
    name: String(source.name || "").trim(),
    api_base: String(source.api_base || "").trim().replace(/\/+$/, ""),
    models: models,
    api_keys: (Array.isArray(source.api_keys) ? source.api_keys : [])
      .map((key) => String(key == null ? "" : key))
      .filter((key) => key.length > 0),
    enable_generation: source.enable_generation !== false,
    enable_edit: source.enable_edit !== false,
    aspect_ratios: (Array.isArray(source.aspect_ratios) ? source.aspect_ratios : []).map((value) =>
      String(value).trim(),
    ).filter(Boolean),
    aspect_ratio_field: String(source.aspect_ratio_field || "").trim(),
    validate_aspect_ratio: source.validate_aspect_ratio !== false,
    response_image_path: String(source.response_image_path || "").trim(),
    generation_prompt: String(source.generation_prompt || ""),
    edit_prompt: String(source.edit_prompt || ""),
    extra_request_body: parseJsonObject(source.extra_request_body).value,
    timeout: parseInt(source.timeout, 10) || 0,
    enabled: source.enabled !== false,
  };
}

/* Build the persisted config payload. Returns {error} when a JSON field is
 * invalid so nothing is written to the backend. */
export function collectConfig(config) {
  const globalExtra = parseJsonObject(config.extra_request_body);
  if (!globalExtra.ok) return { error: t("invalidJson") };

  const sources = [];
  for (const source of Array.isArray(config.sources) ? config.sources : []) {
    const parsed = parseJsonObject(source.extra_request_body);
    if (!parsed.ok) return { error: t("invalidJson") };
    sources.push(collectSource(source));
  }

  /* The order list always mirrors the current sources: known tags keep their
   * position, new tags are appended, stale tags are dropped. */
  const available = sourceTags(config.sources);
  const order = [];
  normalizeList(config.model_order, []).forEach((tag) => {
    if (available.indexOf(tag) >= 0 && order.indexOf(tag) < 0) order.push(tag);
  });
  available.forEach((tag) => {
    if (order.indexOf(tag) < 0) order.push(tag);
  });

  return {
    config: {
      sources: sources,
      model_order: order,
      model_disabled: normalizeList(config.model_disabled, []).filter(
        (tag) => available.indexOf(tag) >= 0,
      ),
      generation_prompt: String(config.generation_prompt || ""),
      edit_prompt: String(config.edit_prompt || ""),
      enable_generation: config.enable_generation !== false,
      enable_edit: config.enable_edit !== false,
      enable_prompt_polish: config.enable_prompt_polish !== false,
      available_aspect_ratios: normalizeList(config.available_aspect_ratios, []),
      aspect_ratio_field: String(config.aspect_ratio_field || "").trim() || "size",
      response_image_path: String(config.response_image_path || "").trim() || "data",
      timeout: parseInt(config.timeout, 10) || 300,
      extra_request_body: globalExtra.value,
      return_elapsed: !!config.return_elapsed,
      return_id: !!config.return_id,
      return_model: !!config.return_model,
      return_retries: !!config.return_retries,
      enable_commands: config.enable_commands !== false,
      command_prefix: String(config.command_prefix || "").trim() || "/",
      command_generation_head: normalizeList(config.command_generation_head, []),
      command_edit_head: normalizeList(config.command_edit_head, []),
      command_enable_polish: !!config.command_enable_polish,
      command_arg_mode: normalizeMode(config.command_arg_mode, ARG_MODES, "listed"),
      command_allowed_args: normalizeList(config.command_allowed_args, []),
      command_polish_provider: String(config.command_polish_provider || "").trim(),
      access_group_mode: normalizeMode(config.access_group_mode, LIST_MODES, "off"),
      access_user_mode: normalizeMode(config.access_user_mode, LIST_MODES, "off"),
      access_group_ids: normalizeList(config.access_group_ids, []),
      access_user_ids: normalizeList(config.access_user_ids, []),
      quota_daily_limit: parseInt(config.quota_daily_limit, 10) || 0,
      quota_exempt_user_ids: normalizeList(config.quota_exempt_user_ids, []),
      checkin_enabled: !!config.checkin_enabled,
      checkin_heads: normalizeList(config.checkin_heads, []),
      checkin_bonus: parseInt(config.checkin_bonus, 10) || 0,
      checkin_success: String(config.checkin_success || "").trim(),
      checkin_fail: String(config.checkin_fail || "").trim(),
    },
  };
}

/* Tags are "source_name/model_id" for every model the sources currently
 * define, deduplicated in source and model list order. */
export function sourceTags(sources) {
  const tags = [];
  (Array.isArray(sources) ? sources : []).forEach((source) => {
    const name = String(source.name || "").trim();
    (Array.isArray(source.models) ? source.models : []).forEach((item) => {
      const id = String((item && item.id) || "").trim();
      if (!name || !id) return;
      const tag = `${name}/${id}`;
      if (tags.indexOf(tag) < 0) tags.push(tag);
    });
  });
  return tags;
}

/* Rebuild the order list from the current sources, keeping the manual order
 * for tags that still exist and dropping the ones that no longer do. */
export function syncModelOrder(config) {
  const available = sourceTags(config.sources);
  const order = [];
  normalizeList(config.model_order, []).forEach((tag) => {
    if (available.indexOf(tag) >= 0 && order.indexOf(tag) < 0) order.push(tag);
  });
  available.forEach((tag) => {
    if (order.indexOf(tag) < 0) order.push(tag);
  });
  config.model_order = order;
  config.model_disabled = normalizeList(config.model_disabled, []).filter(
    (tag) => available.indexOf(tag) >= 0,
  );
}

export function argModeEnabled(config) {
  return normalizeMode(config.command_arg_mode, ARG_MODES, "listed") === "listed";
}

export function listLines(value) {
  return normalizeList(value, []).join("\n");
}

export { splitLines };
