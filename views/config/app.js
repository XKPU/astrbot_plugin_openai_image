/* Config view for the openai_image plugin, driven by AstrBotPluginView. */
(function () {
  "use strict";

  /* The bridge script is injected after app.js, so resolve it lazily. */
  function sdk() {
    return window.AstrBotPluginView || window.AstrBotPluginPage || null;
  }
  var I18N = {
    "zh-CN": {
      title: "图像生成与编辑插件配置",
      subtitle: "配置 OpenAI 兼容服务来源、请求参数与访问策略。",
      reload: "重新加载",
      save: "保存配置",
      saving: "保存中…",
      navSources: "服务来源",
      navModelOrder: "模型顺序",
      navPrompts: "附加提示词",
      navCommands: "聊天命令",
      navAccess: "区域管理",
      navToggles: "功能开关",
      navParams: "生成参数",
      navReturn: "返回信息",
      sectionSources: "服务来源",
      addSource: "+ 新增来源",
      sourcesHint:
        "来源按列表顺序调用；同一来源内按模型顺序与密钥顺序轮换，单个密钥失败时按重试次数重试后再切换下一项。",
      sourceName: "名称",
      apiBase: "接口地址",
      apiKey: "API 密钥",
      addKey: "+ 新增密钥",
      enabled: "启用",
      remove: "删除",
      up: "上移",
      down: "下移",
      sectionModels: "模型列表（按调用顺序）",
      addModel: "+ 新增模型",
      fetchModels: "从接口获取模型",
      fetchingModels: "获取中…",
      fetchModelsOk: "已获取 N 个模型，请选择需要添加的项。",
      fetchModelsEmpty: "接口未返回任何模型。",
      fetchModelsFailed: "获取模型失败：",
      pickModels: "选择需要添加的模型",
      selectAllModels: "全选",
      addSelected: "添加所选",
      modelId: "模型 ID",
      retries: "重试次数",
      sourceAdvanced: "来源高级配置（留空则沿用全局值）",
      enableGeneration: "参与图像生成",
      enableEdit: "参与图像编辑",
      aspectRatios: "可用宽高比 / 尺寸（每行一项）",
      ratioField: "宽高比写入字段",
      validateRatio: "校验宽高比 / 尺寸取值",
      validateRatioHint: "关闭后任意取值原样透传，不再限制为枚举项。",
      generationPrompt: "图像生成附加提示词",
      editPrompt: "编辑附加提示词",
      extraBody: "额外请求体字段（JSON）",
      timeout: "超时（秒，0 = 沿用全局）",
      sectionModelOrder: "全局模型调用顺序",
      modelOrderHint:
        "列表中的模型按此顺序优先调用；未列出的模型按来源与模型列表顺序排在后面。标签格式为「来源名称/模型ID」。",
      addTag: "+ 新增标签",
      syncTags: "同步来源模型",
      sectionPrompts: "全局附加提示词",
      sectionCommands: "聊天命令",
      commandsHint:
        "命令由插件直接处理，不经过 LLM。命令头每行一项，可配置多个；命中命令头之后的全部内容均为提示词，支持多行与空格。",
      enableCommands: "启用聊天命令",
      commandEnablePolish: "命令提示词润色",
      commandPrefix: "命令触发前缀",
      commandGenerationHead: "图像生成命令头（每行一项）",
      commandEditHead: "图像编辑命令头（每行一项）",
      commandPolishProvider: "命令润色模型",
      commandPolishDefault: "（使用当前会话模型）",
      commandArgMode: "追加参数模式",
      commandArgModeOff: "禁止追加参数",
      commandArgModeAll: "允许追加任意参数",
      commandArgModeListed: "仅允许追加已配置的参数",
      commandAllowedArgs: "允许追加的参数字段（每行一项）",
      commandArgsHint:
        "追加参数写作 --字段:值，例如 --size:512x512，会原样并入请求体；第一个参数之后的任何内容都不再作为提示词。「仅允许追加已配置的参数」时只向图像接口传递下方列出的字段，其余字段会被丢弃。",
      sectionAccess: "区域管理",
      accessHint:
        "黑白名单与每日调用上限对聊天命令和 LLM 工具调用同时生效；名单为空时对应模式不拦截任何会话。",
      accessGroupMode: "群聊名单模式",
      accessUserMode: "用户名单模式",
      accessGroupIds: "群聊名单（每行一个群号）",
      accessUserIds: "用户名单（每行一个用户 ID）",
      modeOff: "不限制",
      modeWhitelist: "仅白名单可用",
      modeBlacklist: "黑名单不可用",
      quotaDailyLimit: "每人每日调用上限（0 = 不限）",
      checkinEnabled: "启用签到补充额度",
      checkinHeads: "签到命令头（每行一项）",
      checkinBonus: "每次签到补充的次数",
      checkinSuccess: "签到成功回复",
      checkinFail: "重复签到回复",
      checkinHint:
        "回复可使用占位符：{{count}} 本次获得次数、{{remaining}} 今日剩余次数、{{limit}} 每日上限。签到命令与图像生成命令共用触发前缀。",
      sectionToggles: "功能开关",
      enableGenerationTool: "启用图像生成工具",
      enableEditTool: "启用图像编辑工具",
      enablePromptPolish: "启用提示词润色工具",
      sectionParams: "全局生成参数",
      globalRatios: "可用宽高比 / 尺寸（每行一项）",
      globalRatioField: "宽高比写入字段",
      responsePath: "响应图像路径",
      globalTimeout: "全局超时（秒）",
      globalExtraBody: "全局额外请求体字段（JSON）",
      sectionReturn: "工具返回信息",
      returnElapsed: "返回请求耗时",
      returnId: "返回请求 ID",
      returnModel: "返回模型标签",
      returnRetries: "返回重试次数",
      loadFailed: "加载配置失败：",
      saveFailed: "保存失败：",
      saved: "配置已保存，工具已重新加载。",
      invalidJson: "「额外请求体字段」不是有效的 JSON。",
      confirmRemove: "确定删除该来源？",
      confirmRemoveModel: "确定删除该模型？",
      sourceLabel: "服务来源",
      secretPlaceholder: "sk-…（留空则删除该密钥）",
      revealKey: "显示或隐藏密钥",
    },
    "en-US": {
      title: "Image Generation and Editing Plugin",
      subtitle: "Configure OpenAI-compatible sources, request parameters and access policy.",
      reload: "Reload",
      save: "Save config",
      saving: "Saving…",
      navSources: "Service sources",
      navModelOrder: "Model order",
      navPrompts: "Prompts",
      navCommands: "Commands",
      navAccess: "Access control",
      navToggles: "Feature switches",
      navParams: "Parameters",
      navReturn: "Return details",
      sectionSources: "Service sources",
      addSource: "+ Add source",
      sourcesHint:
        "Sources are called in list order; within a source, models and keys rotate. A failing key is retried per its retry count before moving on.",
      sourceName: "Name",
      apiBase: "API base URL",
      apiKey: "API key",
      addKey: "+ Add key",
      enabled: "Enabled",
      remove: "Remove",
      up: "Move up",
      down: "Move down",
      sectionModels: "Models (in call order)",
      addModel: "+ Add model",
      fetchModels: "Fetch models from the API",
      fetchingModels: "Fetching…",
      fetchModelsOk: "Fetched N models. Select the ones to add.",
      fetchModelsEmpty: "The API returned no models.",
      fetchModelsFailed: "Failed to fetch models: ",
      pickModels: "Select models to add",
      selectAllModels: "Select all",
      addSelected: "Add selected",
      modelId: "Model ID",
      retries: "Retries",
      sourceAdvanced: "Source overrides (blank inherits the global value)",
      enableGeneration: "Use for generation",
      enableEdit: "Use for editing",
      aspectRatios: "Aspect ratios / sizes (one per line)",
      ratioField: "Aspect ratio field",
      validateRatio: "Validate aspect ratio values",
      validateRatioHint: "When off, any value is passed through without enumeration.",
      generationPrompt: "Image generation additional prompt",
      editPrompt: "Edit additional prompt",
      extraBody: "Extra request body fields (JSON)",
      timeout: "Timeout (seconds, 0 = inherit global)",
      sectionModelOrder: "Global model call order",
      modelOrderHint:
        "Listed models are called first in this order; unlisted models follow in source and model list order. Tag format: source_name/model_id.",
      addTag: "+ Add tag",
      syncTags: "Sync from sources",
      sectionPrompts: "Global additional prompts",
      sectionCommands: "Chat commands",
      commandsHint:
        "Commands are handled by the plugin directly and bypass the LLM. Use one command head per line; everything after the matched head is prompt text and may span multiple lines.",
      enableCommands: "Enable chat commands",
      commandEnablePolish: "Polish command prompts",
      commandPrefix: "Command trigger prefix",
      commandGenerationHead: "Image generation command heads (one per line)",
      commandEditHead: "Edit command heads (one per line)",
      commandPolishProvider: "Command polish model",
      commandPolishDefault: "(use the current chat model)",
      commandArgMode: "Extra arguments",
      commandArgModeOff: "No extra arguments",
      commandArgModeAll: "Allow any extra argument",
      commandArgModeListed: "Allow configured arguments only",
      commandAllowedArgs: "Allowed argument fields (one per line)",
      commandArgsHint:
        "Extra arguments are written as --key:value, e.g. --size:512x512, and are merged into the request body; nothing after the first argument is treated as prompt text. With configured-arguments-only, only the fields listed below are forwarded and the rest are dropped.",
      sectionAccess: "Access control",
      accessHint:
        "The black/white lists and the daily call limit apply to both chat commands and LLM tool calls. An empty list never blocks anyone.",
      accessGroupMode: "Group list mode",
      accessUserMode: "User list mode",
      accessGroupIds: "Group IDs (one per line)",
      accessUserIds: "User IDs (one per line)",
      modeOff: "Unrestricted",
      modeWhitelist: "Whitelist only",
      modeBlacklist: "Blacklisted",
      quotaDailyLimit: "Daily call limit per user (0 = unlimited)",
      checkinEnabled: "Enable check-in bonus",
      checkinHeads: "Check-in command heads (one per line)",
      checkinBonus: "Calls granted per check-in",
      checkinSuccess: "Check-in success reply",
      checkinFail: "Duplicate check-in reply",
      checkinHint:
        "Replies support {{count}} (granted calls), {{remaining}} (left today) and {{limit}} (daily limit). Check-in shares the command trigger prefix.",
      sectionToggles: "Feature switches",
      enableGenerationTool: "Enable generation tool",
      enableEditTool: "Enable edit tool",
      enablePromptPolish: "Enable prompt polishing tool",
      sectionParams: "Global generation parameters",
      globalRatios: "Aspect ratios / sizes (one per line)",
      globalRatioField: "Aspect ratio field",
      responsePath: "Response image path",
      globalTimeout: "Global timeout (seconds)",
      globalExtraBody: "Global extra request body fields (JSON)",
      sectionReturn: "Tool return details",
      returnElapsed: "Return request elapsed time",
      returnId: "Return request ID",
      returnModel: "Return model tag",
      returnRetries: "Return retry count",
      loadFailed: "Failed to load config: ",
      saveFailed: "Save failed: ",
      saved: "Config saved and tools reloaded.",
      invalidJson: "The extra request body fields are not valid JSON.",
      confirmRemove: "Delete this source?",
      confirmRemoveModel: "Delete this model?",
      sourceLabel: "Source",
      secretPlaceholder: "sk-… (leave empty to remove this key)",
      revealKey: "Show or hide the key",
    },
  };

  var state = { config: {}, locale: "zh-CN" };

  function t(key, fallback) {
    var dict = I18N[state.locale] || I18N["zh-CN"];
    if (Object.prototype.hasOwnProperty.call(dict, key)) return dict[key];
    var fallbackDict = I18N["zh-CN"];
    if (Object.prototype.hasOwnProperty.call(fallbackDict, key)) {
      return fallbackDict[key];
    }
    return fallback !== undefined ? fallback : key;
  }

  function $(selector, root) {
    return (root || document).querySelector(selector);
  }

  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function showAlert(message, kind) {
    var box = $("#alert");
    box.textContent = message;
    box.className = "alert " + (kind || "error");
  }

  function hideAlert() {
    $("#alert").className = "alert hidden";
  }

  function splitLines(value) {
    return String(value || "")
      .split(/[\n,]/)
      .map(function (item) {
        return item.trim();
      })
      .filter(Boolean);
  }

  function normalizeArgMode(value) {
    var mode = String(value || "").trim().toLowerCase();
    return mode === "off" || mode === "all" || mode === "listed"
      ? mode
      : "listed";
  }

  function syncArgModeState() {
    var listed = $("#command_arg_mode").value === "listed";
    $("#command_allowed_args").disabled = !listed;
  }

  /* ---------- rendering ---------- */

  function renderStatic() {
    document.querySelectorAll("[data-i18n]").forEach(function (node) {
      var key = node.getAttribute("data-i18n");
      var text = t(key);
      if (text) node.textContent = text;
    });
    document.title = t("title");
  }

  function textField(labelText, value, placeholder, datasetField) {
    var field = el("div", "field");
    if (labelText) field.appendChild(el("label", null, labelText));
    var input = el("input");
    input.type = "text";
    input.value = value === undefined || value === null ? "" : String(value);
    if (placeholder) input.placeholder = placeholder;
    input.dataset.field = datasetField;
    field.appendChild(input);
    return field;
  }

  function areaField(labelText, value, placeholder, datasetField, rows) {
    var field = el("div", "field");
    if (labelText) field.appendChild(el("label", null, labelText));
    var area = el("textarea");
    area.rows = rows || 3;
    area.value = value === undefined || value === null ? "" : String(value);
    if (placeholder) area.placeholder = placeholder;
    area.dataset.field = datasetField;
    field.appendChild(area);
    return field;
  }

  function switchRow(labelText, checked, datasetField) {
    var row = el("label", "switch-item");
    var input = el("input");
    input.type = "checkbox";
    input.checked = checked;
    input.dataset.field = datasetField;
    row.appendChild(input);
    row.appendChild(el("span", null, labelText));
    return row;
  }

  function parseExtra(value) {
    try {
      return value ? JSON.parse(value) : {};
    } catch (err) {
      return { __invalid__: value };
    }
  }

  function extraText(value) {
    if (!value || typeof value !== "object") return "";
    if (value.__invalid__ !== undefined) return String(value.__invalid__);
    return JSON.stringify(value, null, 2);
  }

  function keyRow(value) {
    var row = el("div", "key-row");
    var input = el("input");
    /* Masked display only: the real value round-trips in the form. */
    input.type = "password";
    input.autocomplete = "off";
    input.value = value || "";
    input.placeholder = t("secretPlaceholder");
    input.dataset.field = "api_key";
    row.appendChild(input);
    var reveal = el("button", "btn icon");
    reveal.type = "button";
    reveal.title = t("revealKey");
    reveal.setAttribute("aria-label", t("revealKey"));
    reveal.textContent = "👁";
    reveal.addEventListener("click", function () {
      input.type = input.type === "password" ? "text" : "password";
    });
    row.appendChild(reveal);
    return row;
  }

  function moveButton(label, icon, getRow) {
    var button = el("button", "btn small icon", icon);
    button.type = "button";
    button.title = t(label);
    button.addEventListener("click", function () {
      var row = getRow();
      if (label === "up") {
        var prev = row.previousElementSibling;
        if (prev) row.parentNode.insertBefore(row, prev);
      } else {
        var next = row.nextElementSibling;
        if (next) row.parentNode.insertBefore(next, row);
      }
    });
    return button;
  }

  function removeButton(confirmKey, getRow) {
    var button = el("button", "btn small danger icon", "✕");
    button.type = "button";
    button.title = t("remove");
    button.setAttribute("aria-label", t("remove"));
    button.addEventListener("click", function () {
      if (confirmKey && !window.confirm(t(confirmKey))) return;
      var row = getRow();
      var list = row.parentNode;
      row.remove();
      if (list && list.classList.contains("source-list")) renumberSources();
    });
    return button;
  }

  function modelRow(model) {
    /* Accept the same entry forms as the backend parser: dicts, plain ids,
       and "id:retries" strings. */
    if (typeof model === "string") {
      var parts = model.split(":");
      model = {
        id: parts[0].trim(),
        retries: parseInt(parts[1], 10) || 0,
      };
    }
    if (!model || !model.id) return null;
    var row = el("div", "model-row");

    var idInput = el("input");
    idInput.type = "text";
    idInput.value = model.id || "";
    idInput.placeholder = "gpt-image-1";
    idInput.title = t("modelId");
    idInput.setAttribute("aria-label", t("modelId"));
    idInput.dataset.field = "model_id";
    idInput.className = "model-id";
    row.appendChild(idInput);

    var retryWrap = el("label", "retry-wrap");
    retryWrap.appendChild(el("span", null, t("retries")));
    var retryInput = el("input");
    retryInput.type = "number";
    retryInput.min = "0";
    retryInput.max = "10";
    retryInput.value = String(model.retries || 0);
    retryInput.dataset.field = "model_retries";
    retryWrap.appendChild(retryInput);
    row.appendChild(retryWrap);

    row.appendChild(moveButton("up", "↑", function () { return row; }));
    row.appendChild(moveButton("down", "↓", function () { return row; }));
    row.appendChild(removeButton("confirmRemoveModel", function () { return row; }));

    return row;
  }

  function collectKeyValues(card) {
    var keys = [];
    card.querySelectorAll('[data-field="api_key"]').forEach(function (input) {
      var value = input.value.trim();
      if (value) keys.push(value);
    });
    return keys;
  }

  async function fetchModelList(card, button) {
    var baseNode = card.querySelector('[data-field="api_base"]');
    var apiBase = (baseNode ? baseNode.value : "").trim().replace(/\/+$/, "");
    if (!apiBase) {
      showAlert(t("fetchModelsFailed") + t("apiBase"));
      return;
    }
    button.disabled = true;
    var original = button.textContent;
    button.textContent = t("fetchingModels");
    try {
      var data = await sdk().apiPost("models", {
        api_base: apiBase,
        api_keys: collectKeyValues(card),
      });
      showModelPicker(card, (data && data.models) || []);
    } catch (err) {
      showAlert(t("fetchModelsFailed") + (err && err.message ? err.message : err));
    } finally {
      button.disabled = false;
      button.textContent = original;
    }
  }

  function showModelPicker(card, modelIds) {
    var block = card.querySelector(".models-block");
    if (!block) return;
    var old = block.querySelector(".model-picker");
    if (old) old.remove();
    if (!modelIds.length) {
      showAlert(t("fetchModelsEmpty"));
      return;
    }
    showAlert(t("fetchModelsOk").replace("N", String(modelIds.length)), "success");
    var picker = el("div", "model-picker");
    picker.appendChild(el("label", "picker-title", t("pickModels")));
    var optionList = el("div", "picker-options");
    var boxes = [];
    modelIds.forEach(function (id) {
      var row = el("label", "picker-option");
      var box = el("input");
      box.type = "checkbox";
      box.value = id;
      row.appendChild(box);
      row.appendChild(el("span", null, id));
      boxes.push(box);
      optionList.appendChild(row);
    });
    picker.appendChild(optionList);
    var actions = el("div", "picker-actions");
    var toggle = el("button", "btn small", t("selectAllModels"));
    toggle.type = "button";
    toggle.addEventListener("click", function () {
      var allChecked = boxes.every(function (box) { return box.checked; });
      boxes.forEach(function (box) { box.checked = !allChecked; });
    });
    actions.appendChild(toggle);
    var addBtn = el("button", "btn small primary", t("addSelected"));
    addBtn.type = "button";
    addBtn.addEventListener("click", function () {
      var list = block.querySelector(".models-list");
      var existing = {};
      list.querySelectorAll('[data-field="model_id"]').forEach(function (input) {
        existing[input.value.trim()] = true;
      });
      boxes.forEach(function (box) {
        if (!box.checked || existing[box.value]) return;
        list.appendChild(modelRow({ id: box.value, retries: 0 }));
      });
      picker.remove();
      syncModelOrder();
    });
    actions.appendChild(addBtn);
    picker.appendChild(actions);
    block.appendChild(picker);
  }

  function modelsBlock(models, card) {
    var block = el("div", "field models-block");
    block.appendChild(el("label", null, t("sectionModels")));
    var list = el("div", "models-list");
    (models || []).forEach(function (model) {
      var row = modelRow(model);
      if (row) list.appendChild(row);
    });
    block.appendChild(list);

    var actions = el("div", "model-actions");
    var addModel = el("button", "btn small", t("addModel"));
    addModel.type = "button";
    addModel.addEventListener("click", function () {
      list.appendChild(modelRow({ id: "", retries: 0 }));
    });
    actions.appendChild(addModel);

    var fetchBtn = el("button", "btn small", t("fetchModels"));
    fetchBtn.type = "button";
    fetchBtn.addEventListener("click", function () {
      fetchModelList(card, fetchBtn);
    });
    actions.appendChild(fetchBtn);
    block.appendChild(actions);
    return block;
  }

  function sourceCard(source, index) {
    var card = el("div", "source-card");
    card.dataset.index = String(index);

    var head = el("div", "source-head");
    var title = el("span", "source-title", t("sourceLabel") + " " + (index + 1));
    head.appendChild(title);

    var enabledRow = el("label", "enabled-row");
    var enabled = el("input");
    enabled.type = "checkbox";
    enabled.checked = source.enabled !== false;
    enabled.dataset.field = "enabled";
    enabledRow.appendChild(enabled);
    enabledRow.appendChild(el("span", null, t("enabled")));
    head.appendChild(enabledRow);
    card.appendChild(head);

    var body = el("div", "field-row");
    body.appendChild(textField(t("sourceName"), source.name, "", "name"));
    body.appendChild(
      textField(t("apiBase"), source.api_base, "https://api.openai.com/v1", "api_base"),
    );
    card.appendChild(body);

    /* keys */
    var keyBlock = el("div", "field");
    keyBlock.appendChild(el("label", null, t("apiKey")));
    var keys = el("div", "keys-list");
    var keyValues = Array.isArray(source.api_keys) ? source.api_keys.slice() : [];
    if (!keyValues.length) keyValues = [""];
    keyValues.forEach(function (value) {
      keys.appendChild(keyRow(value));
    });
    keyBlock.appendChild(keys);

    var addKey = el("button", "btn small", t("addKey"));
    addKey.type = "button";
    addKey.addEventListener("click", function () {
      keys.appendChild(keyRow(""));
    });
    keyBlock.appendChild(addKey);
    card.appendChild(keyBlock);

    /* models */
    card.appendChild(modelsBlock(source.models || [], card));

    /* per-source overrides */
    var details = el("details", "source-advanced");
    details.appendChild(el("summary", null, t("sourceAdvanced")));
    var advGrid = el("div", "switch-grid adv");
    advGrid.appendChild(
      switchRow(
        t("enableGeneration"),
        source.enable_generation !== false,
        "enable_generation",
      ),
    );
    advGrid.appendChild(
      switchRow(t("enableEdit"), source.enable_edit !== false, "enable_edit"),
    );
    advGrid.appendChild(
      switchRow(
        t("validateRatio"),
        source.validate_aspect_ratio !== false,
        "validate_aspect_ratio",
      ),
    );
    details.appendChild(advGrid);
    details.appendChild(el("p", "hint adv-hint", t("validateRatioHint")));
    var adv = el("div", "adv-fields");
    adv.appendChild(
      areaField(
        t("aspectRatios"),
        (source.aspect_ratios || []).join("\n"),
        "1024x1024\n1536x1024",
        "aspect_ratios",
      ),
    );
    adv.appendChild(
      textField(t("ratioField"), source.aspect_ratio_field, "size", "aspect_ratio_field"),
    );
    adv.appendChild(
      textField(
        t("responsePath"),
        source.response_image_path,
        "data",
        "response_image_path",
      ),
    );
    adv.appendChild(
      areaField(t("generationPrompt"), source.generation_prompt, "", "generation_prompt"),
    );
    adv.appendChild(areaField(t("editPrompt"), source.edit_prompt, "", "edit_prompt"));
    adv.appendChild(
      areaField(
        t("extraBody"),
        extraText(source.extra_request_body),
        '{ "quality": "high" }',
        "extra_request_body",
        4,
      ),
    );
    adv.appendChild(
      textField(t("timeout"), source.timeout > 0 ? source.timeout : 0, "0", "timeout"),
    );
    details.appendChild(adv);
    card.appendChild(details);

    head.appendChild(removeButton("confirmRemove", function () { return card; }));

    return card;
  }

  function renumberSources() {
    document.querySelectorAll("#sources .source-title").forEach(function (node, i) {
      node.textContent = t("sourceLabel") + " " + (i + 1);
    });
  }

  /* ---------- global model order ---------- */

  function orderRow(tag) {
    var row = el("div", "order-row");
    var input = el("input");
    input.type = "text";
    input.value = tag || "";
    input.placeholder = "OpenAI/gpt-image-1";
    input.dataset.field = "model_order_tag";
    row.appendChild(input);
    row.appendChild(moveButton("up", "↑", function () { return row; }));
    row.appendChild(moveButton("down", "↓", function () { return row; }));
    row.appendChild(removeButton(null, function () { return row; }));
    return row;
  }

  function renderModelOrder(tags) {
    var list = $("#model-order-list");
    list.textContent = "";
    (tags || []).forEach(function (tag) {
      list.appendChild(orderRow(tag));
    });
  }

  function currentSourceTags() {
    var tags = [];
    document.querySelectorAll("#sources .source-card").forEach(function (card) {
      var name = card.querySelector('[data-field="name"]').value.trim();
      card.querySelectorAll(".model-row").forEach(function (row) {
        var id = row.querySelector('[data-field="model_id"]').value.trim();
        if (!name || !id) return;
        var tag = name + "/" + id;
        if (tags.indexOf(tag) < 0) tags.push(tag);
      });
    });
    return tags;
  }

  function syncModelOrder() {
    var existing = [];
    document
      .querySelectorAll('#model-order-list [data-field="model_order_tag"]')
      .forEach(function (input) {
        var value = input.value.trim();
        if (value && existing.indexOf(value) < 0) existing.push(value);
      });
    currentSourceTags().forEach(function (tag) {
      if (existing.indexOf(tag) < 0) existing.push(tag);
    });
    renderModelOrder(existing);
  }

  function collectModelOrder() {
    var tags = [];
    document
      .querySelectorAll('#model-order-list [data-field="model_order_tag"]')
      .forEach(function (input) {
        var value = input.value.trim();
        if (value && tags.indexOf(value) < 0) tags.push(value);
      });
    return tags;
  }

  /* ---------- collect ---------- */

  function collectModels(card) {
    /* Entries as "id" or "id:retries" strings: the declarative settings
       page renders list items verbatim, so dicts would show [object Object]. */
    var models = [];
    card.querySelectorAll(".model-row").forEach(function (row) {
      var id = row.querySelector('[data-field="model_id"]').value.trim();
      if (!id) return;
      var retries = parseInt(row.querySelector('[data-field="model_retries"]').value, 10);
      if (!isNaN(retries) && retries > 0) {
        models.push(id + ":" + retries);
      } else {
        models.push(id);
      }
    });
    return models;
  }

  function collectSources() {
    var sources = [];
    document.querySelectorAll("#sources .source-card").forEach(function (card) {
      var get = function (field) {
        var node = card.querySelector('[data-field="' + field + '"]');
        return node ? node.value : "";
      };
      var keys = collectKeyValues(card);
      sources.push({
        name: get("name").trim(),
        api_base: get("api_base").trim().replace(/\/+$/, ""),
        models: collectModels(card),
        api_keys: keys,
        enable_generation: card.querySelector('[data-field="enable_generation"]').checked,
        enable_edit: card.querySelector('[data-field="enable_edit"]').checked,
        aspect_ratios: splitLines(get("aspect_ratios")),
        aspect_ratio_field: get("aspect_ratio_field").trim(),
        validate_aspect_ratio: card.querySelector('[data-field="validate_aspect_ratio"]').checked,
        response_image_path: get("response_image_path").trim(),
        generation_prompt: get("generation_prompt"),
        edit_prompt: get("edit_prompt"),
        extra_request_body: parseExtra(get("extra_request_body")),
        timeout: parseInt(get("timeout"), 10) || 0,
        enabled: card.querySelector('[data-field="enabled"]').checked,
      });
    });
    return sources;
  }

  function collectConfig() {
    var globalExtraRaw = $("#extra_request_body").value.trim();
    var globalExtra = {};
    if (globalExtraRaw) {
      try {
        globalExtra = JSON.parse(globalExtraRaw);
      } catch (err) {
        return { error: t("invalidJson") };
      }
    }
    var sources = collectSources();
    for (var i = 0; i < sources.length; i++) {
      var extra = sources[i].extra_request_body;
      if (extra && extra.__invalid__ !== undefined) {
        return { error: t("invalidJson") };
      }
    }
    return {
      config: {
        sources: sources,
        model_order: collectModelOrder(),
        generation_prompt: $("#generation_prompt").value,
        edit_prompt: $("#edit_prompt").value,
        enable_generation: $("#enable_generation").checked,
        enable_edit: $("#enable_edit").checked,
        enable_prompt_polish: $("#enable_prompt_polish").checked,
        available_aspect_ratios: splitLines($("#available_aspect_ratios").value),
        aspect_ratio_field: $("#aspect_ratio_field").value.trim() || "size",
        response_image_path: $("#response_image_path").value.trim() || "data",
        timeout: parseInt($("#timeout").value, 10) || 300,
        extra_request_body: globalExtra,
        return_elapsed: $("#return_elapsed").checked,
        return_id: $("#return_id").checked,
        return_model: $("#return_model").checked,
        return_retries: $("#return_retries").checked,
        enable_commands: $("#enable_commands").checked,
        command_prefix: $("#command_prefix").value.trim() || "/",
        command_generation_head:
          splitLines($("#command_generation_head").value).length > 0
            ? splitLines($("#command_generation_head").value)
            : ["t2i"],
        command_edit_head:
          splitLines($("#command_edit_head").value).length > 0
            ? splitLines($("#command_edit_head").value)
            : ["i2i"],
        command_enable_polish: $("#command_enable_polish").checked,
        command_arg_mode: $("#command_arg_mode").value,
        command_allowed_args: splitLines($("#command_allowed_args").value),
        command_polish_provider: $("#command_polish_provider").value,
        access_group_mode: normalizeListMode($("#access_group_mode").value),
        access_user_mode: normalizeListMode($("#access_user_mode").value),
        access_group_ids: splitLines($("#access_group_ids").value),
        access_user_ids: splitLines($("#access_user_ids").value),
        quota_daily_limit: parseInt($("#quota_daily_limit").value, 10) || 0,
        checkin_enabled: $("#checkin_enabled").checked,
        checkin_heads:
          splitLines($("#checkin_heads").value).length > 0
            ? splitLines($("#checkin_heads").value)
            : ["checkin"],
        checkin_bonus: parseInt($("#checkin_bonus").value, 10) || 0,
        checkin_success: $("#checkin_success").value.trim(),
        checkin_fail: $("#checkin_fail").value.trim(),
      },
    };
  }

  /* ---------- load / save ---------- */

  function applyConfig(config) {
    state.config = config || {};
    renderSources(state.config.sources || []);
    var order = [];
    (state.config.model_order || []).forEach(function (entry) {
      var tag = typeof entry === "string" ? entry : (entry && (entry.tag || entry.id)) || "";
      tag = String(tag).trim();
      if (tag && order.indexOf(tag) < 0) order.push(tag);
    });
    currentSourceTags().forEach(function (tag) {
      if (order.indexOf(tag) < 0) order.push(tag);
    });
    renderModelOrder(order);
    $("#generation_prompt").value = state.config.generation_prompt || "";
    $("#edit_prompt").value = state.config.edit_prompt || "";
    $("#enable_generation").checked = state.config.enable_generation !== false;
    $("#enable_edit").checked = state.config.enable_edit !== false;
    $("#enable_prompt_polish").checked = state.config.enable_prompt_polish !== false;
    $("#available_aspect_ratios").value = (state.config.available_aspect_ratios || []).join("\n");
    $("#aspect_ratio_field").value = state.config.aspect_ratio_field || "size";
    $("#response_image_path").value = state.config.response_image_path || "data";
    $("#timeout").value = state.config.timeout || 300;
    $("#extra_request_body").value = extraText(state.config.extra_request_body);
    $("#return_elapsed").checked = !!state.config.return_elapsed;
    $("#return_id").checked = !!state.config.return_id;
    $("#return_model").checked = !!state.config.return_model;
    $("#return_retries").checked = !!state.config.return_retries;
    $("#enable_commands").checked = state.config.enable_commands !== false;
    $("#command_prefix").value = state.config.command_prefix || "/";
    $("#command_generation_head").value = (
      Array.isArray(state.config.command_generation_head)
        ? state.config.command_generation_head
        : splitLines(state.config.command_generation_head || "t2i")
    ).join("\n");
    $("#command_edit_head").value = (
      Array.isArray(state.config.command_edit_head)
        ? state.config.command_edit_head
        : splitLines(state.config.command_edit_head || "i2i")
    ).join("\n");
    $("#command_enable_polish").checked = !!state.config.command_enable_polish;
    $("#command_arg_mode").value = normalizeArgMode(state.config.command_arg_mode);
    $("#command_allowed_args").value = (
      Array.isArray(state.config.command_allowed_args)
        ? state.config.command_allowed_args
        : splitLines(state.config.command_allowed_args || "size")
    ).join("\n");
    selectProvider(state.config.command_polish_provider || "");
    syncArgModeState();
    $("#access_group_mode").value = normalizeListMode(state.config.access_group_mode);
    $("#access_user_mode").value = normalizeListMode(state.config.access_user_mode);
    $("#access_group_ids").value = (
      Array.isArray(state.config.access_group_ids)
        ? state.config.access_group_ids
        : splitLines(state.config.access_group_ids || "")
    ).join("\n");
    $("#access_user_ids").value = (
      Array.isArray(state.config.access_user_ids)
        ? state.config.access_user_ids
        : splitLines(state.config.access_user_ids || "")
    ).join("\n");
    $("#quota_daily_limit").value = state.config.quota_daily_limit || 0;
    $("#checkin_enabled").checked = !!state.config.checkin_enabled;
    $("#checkin_heads").value = (
      Array.isArray(state.config.checkin_heads)
        ? state.config.checkin_heads
        : splitLines(state.config.checkin_heads || "checkin")
    ).join("\n");
    $("#checkin_bonus").value =
      state.config.checkin_bonus === undefined ? 1 : state.config.checkin_bonus;
    $("#checkin_success").value = state.config.checkin_success || "";
    $("#checkin_fail").value = state.config.checkin_fail || "";
  }

  function normalizeListMode(value) {
    return value === "whitelist" || value === "blacklist" ? value : "off";
  }

  function selectProvider(providerId) {
    var select = $("#command_polish_provider");
    if (!select) return;
    var found = false;
    Array.prototype.forEach.call(select.options, function (option) {
      if (option.value === providerId) found = true;
    });
    if (providerId && !found) {
      var extra = el("option", null, providerId);
      extra.value = providerId;
      select.appendChild(extra);
    }
    select.value = providerId;
  }

  async function loadProviders() {
    var select = $("#command_polish_provider");
    if (!select) return;
    try {
      var data = await sdk().apiGet("providers");
      var providers = (data && (data.providers || (data.data && data.data.providers))) || [];
      select.textContent = "";
      var auto = el("option", null, t("commandPolishDefault"));
      auto.value = "";
      select.appendChild(auto);
      providers.forEach(function (provider) {
        var option = el("option", null, provider.label || provider.id);
        option.value = provider.id;
        select.appendChild(option);
      });
      selectProvider(state.config.command_polish_provider || "");
    } catch (err) {
      /* The provider list is optional; keep the field usable without it. */
      select.textContent = "";
      var fallback = el("option", null, t("commandPolishDefault"));
      fallback.value = "";
      select.appendChild(fallback);
    }
  }

  function renderSources(sources) {
    var wrap = $("#sources");
    wrap.textContent = "";
    (sources || []).forEach(function (source, index) {
      wrap.appendChild(sourceCard(source, index));
    });
  }

  async function loadConfig() {
    hideAlert();
    try {
      var data = await sdk().apiGet("config");
      applyConfig(data && data.config ? data.config : data);
    } catch (err) {
      showAlert(t("loadFailed") + (err && err.message ? err.message : err));
    }
  }

  async function saveConfig() {
    hideAlert();
    var body = collectConfig();
    if (body.error) {
      showAlert(body.error);
      return;
    }
    var button = $("#btn-save");
    button.disabled = true;
    button.textContent = t("saving");
    try {
      var data = await sdk().apiPost("config", body);
      applyConfig(data && data.config ? data.config : data);
      showAlert(t("saved"), "success");
    } catch (err) {
      showAlert(t("saveFailed") + (err && err.message ? err.message : err));
    } finally {
      button.disabled = false;
      button.textContent = t("save");
    }
  }

  /* ---------- side nav ---------- */

  function setupNav() {
    var links = document.querySelectorAll(".side-nav a");
    links.forEach(function (link) {
      link.addEventListener("click", function (event) {
        event.preventDefault();
        var target = document.querySelector(link.getAttribute("href"));
        if (target) target.scrollIntoView({ behavior: "smooth", block: "start" });
      });
    });
    var sections = [];
    links.forEach(function (link) {
      var section = document.querySelector(link.getAttribute("href"));
      if (section) sections.push({ link: link, section: section });
    });
    if (!("IntersectionObserver" in window) || !sections.length) return;
    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          sections.forEach(function (item) {
            item.link.classList.toggle("active", item.section === entry.target);
          });
        });
      },
      { rootMargin: "-20% 0px -70% 0px" },
    );
    sections.forEach(function (item) {
      observer.observe(item.section);
    });
  }

  /* ---------- init ---------- */

  function init() {
    var bridge = sdk();
    if (bridge && bridge.getLocale) {
      state.locale = bridge.getLocale() || "zh-CN";
    }
    renderStatic();
    if (!bridge) {
      showAlert("Bridge SDK unavailable (must run inside the dashboard).");
      return;
    }
    $("#btn-reload").addEventListener("click", loadConfig);
    $("#btn-save").addEventListener("click", saveConfig);
    $("#btn-add-source").addEventListener("click", function () {
      $("#sources").appendChild(
        sourceCard(
          {
            name: "",
            api_base: "",
            models: [],
            api_keys: [""],
            enabled: true,
          },
          0,
        ),
      );
      renumberSources();
      syncModelOrder();
    });
    $("#btn-add-tag").addEventListener("click", function () {
      $("#model-order-list").appendChild(orderRow(""));
    });
    $("#btn-sync-tags").addEventListener("click", syncModelOrder);
    $("#command_arg_mode").addEventListener("change", syncArgModeState);
    if (bridge.onContext) {
      bridge.onContext(function (ctx) {
        if (ctx && ctx.locale && ctx.locale !== state.locale) {
          state.locale = ctx.locale;
          renderStatic();
        }
      });
    }
    setupNav();
    bridge.ready();
    loadConfig();
    loadProviders();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
