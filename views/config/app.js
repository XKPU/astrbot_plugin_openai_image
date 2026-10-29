/* Config view for the openai_image plugin, driven by AstrBotPluginView. */
(function () {
  "use strict";

  /* The bridge script is injected after app.js, so resolve it lazily. */
  function sdk() {
    return window.AstrBotPluginView || window.AstrBotPluginPage || null;
  }
  var I18N = {
    "zh-CN": {
      title: "OpenAI 图像插件配置",
      subtitle: "配置 OpenAI 兼容的图像生成与编辑服务。",
      reload: "重新加载",
      save: "保存配置",
      saving: "保存中…",
      loading: "加载中…",
      navSources: "API 来源",
      navModelOrder: "模型顺序",
      navPrompts: "附加提示词",
      navToggles: "功能开关",
      navParams: "生成参数",
      navReturn: "返回信息",
      sectionSources: "API 来源",
      addSource: "+ 添加 API 来源",
      sourcesHint:
        "按来源顺序、来源内按模型顺序与 Key 顺序轮询；失败时按重试次数重试后切换下一项。",
      sourceName: "名称",
      apiBase: "API 地址",
      apiKey: "API Key",
      addKey: "+ 添加 Key",
      enabled: "启用",
      remove: "删除",
      up: "上移",
      down: "下移",
      sectionModels: "模型列表（按序执行）",
      addModel: "+ 添加模型",
      fetchModels: "从 API 获取模型",
      fetchingModels: "获取中…",
      fetchModelsOk: "已获取 N 个模型，请勾选添加。",
      fetchModelsEmpty: "API 未返回任何模型。",
      fetchModelsFailed: "获取模型失败：",
      pickModels: "选择要添加的模型",
      selectAllModels: "全选",
      addSelected: "添加所选",
      modelId: "模型 ID",
      retries: "重试",
      sourceAdvanced: "高级覆盖项（留空使用全局配置）",
      enableGeneration: "参与图像生成",
      enableEdit: "参与图像编辑",
      aspectRatios: "可用宽高比 / 尺寸（每行一项）",
      ratioField: "比例请求字段名",
      validateRatio: "校验比例 / 尺寸取值",
      validateRatioHint: "关闭后任意尺寸原样透传，不再限制枚举。",
      generationPrompt: "生图附加提示词",
      editPrompt: "编辑附加提示词",
      extraBody: "额外请求体参数（JSON）",
      timeout: "超时（秒，0=全局）",
      sectionModelOrder: "模型使用顺序（全局）",
      modelOrderHint:
        "按此列表顺序优先执行模型；未列出的模型按来源与模型列表顺序跟在后面。标签格式：来源名称/模型ID。",
      addTag: "+ 添加标签",
      syncTags: "同步来源模型",
      sectionPrompts: "全局附加提示词",
      sectionToggles: "功能开关",
      enableGenerationTool: "启用图像生成工具",
      enableEditTool: "启用图像编辑工具",
      enablePromptPolish: "启用提示词润色工具",
      sectionParams: "全局生成参数",
      globalRatios: "可用宽高比 / 尺寸（每行一项）",
      globalRatioField: "比例请求字段名",
      responsePath: "响应图片路径",
      globalTimeout: "全局超时（秒）",
      globalExtraBody: "额外请求体参数（JSON，全局）",
      sectionReturn: "工具返回信息",
      returnElapsed: "返回请求用时",
      returnId: "返回请求 ID",
      returnModel: "返回模型（来源/模型ID）",
      returnRetries: "返回重试次数",
      loadFailed: "加载配置失败：",
      saveFailed: "保存失败：",
      saved: "配置已保存并已重载工具。",
      invalidJson: "“额外请求体参数”不是有效的 JSON。",
      confirmRemove: "确定删除该 API 来源？",
      confirmRemoveModel: "确定删除该模型？",
      sourceLabel: "API 来源",
      secretPlaceholder: "sk-…（留空则删除该 Key）",
      revealKey: "显示/隐藏 Key",
    },
    "en-US": {
      title: "OpenAI Image Plugin Config",
      subtitle: "Configure OpenAI-compatible image generation and editing.",
      reload: "Reload",
      save: "Save",
      saving: "Saving…",
      loading: "Loading…",
      navSources: "Sources",
      navModelOrder: "Model order",
      navPrompts: "Additional prompts",
      navToggles: "Switches",
      navParams: "Parameters",
      navReturn: "Return info",
      sectionSources: "Sources",
      addSource: "+ Add source",
      sourcesHint:
        "Sources are tried in order; within a source, models and keys rotate. Failed calls are retried per model before moving on.",
      sourceName: "Name",
      apiBase: "API base",
      apiKey: "API key",
      addKey: "+ Add key",
      enabled: "Enabled",
      remove: "Remove",
      up: "Move up",
      down: "Move down",
      sectionModels: "Models (ordered by priority)",
      addModel: "+ Add model",
      fetchModels: "Fetch models from API",
      fetchingModels: "Fetching…",
      fetchModelsOk: "Fetched N models, pick the ones to add.",
      fetchModelsEmpty: "The API returned no models.",
      fetchModelsFailed: "Failed to fetch models: ",
      pickModels: "Pick models to add",
      selectAllModels: "Select all",
      addSelected: "Add selected",
      modelId: "Model ID",
      retries: "Retries",
      sourceAdvanced: "Source-specific overrides (empty = use global)",
      enableGeneration: "Use for generation",
      enableEdit: "Use for editing",
      aspectRatios: "Aspect ratios (one per line)",
      ratioField: "Ratio request field",
      validateRatio: "Validate aspect ratio values",
      validateRatioHint: "When off, any size is passed through without enum checks.",
      generationPrompt: "Generation additional prompt",
      editPrompt: "Edit additional prompt",
      extraBody: "Extra request body (JSON)",
      timeout: "Timeout (s, 0=global)",
      sectionModelOrder: "Model usage order (global)",
      modelOrderHint:
        "Models listed here run first in this order; unlisted models follow in source and model list order. Tag format: source_name/model_id.",
      addTag: "+ Add tag",
      syncTags: "Sync from sources",
      sectionPrompts: "Global additional prompts",
      sectionToggles: "Feature switches",
      enableGenerationTool: "Enable generation tool",
      enableEditTool: "Enable edit tool",
      enablePromptPolish: "Enable prompt polish tool",
      sectionParams: "Global generation parameters",
      globalRatios: "Aspect ratios (one per line)",
      globalRatioField: "Ratio request field",
      responsePath: "Response image path",
      globalTimeout: "Global timeout (seconds)",
      globalExtraBody: "Extra request body (JSON, global)",
      sectionReturn: "Tool return info",
      returnElapsed: "Return elapsed time",
      returnId: "Return request ID",
      returnModel: "Return model (source/model)",
      returnRetries: "Return retry count",
      loadFailed: "Failed to load config: ",
      saveFailed: "Save failed: ",
      saved: "Config saved and tools reloaded.",
      invalidJson: "“Extra request body” is not valid JSON.",
      confirmRemove: "Remove this source?",
      confirmRemoveModel: "Remove this model?",
      sourceLabel: "Source",
      secretPlaceholder: "sk-… (empty removes this key)",
      revealKey: "Show/hide key",
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
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();