<template>
  <section class="tab-panel">
    <div class="panel-head">
      <h2>{{ t("tabSources") }}</h2>
      <button class="btn tonal sm" type="button" @click="addSource()">{{ t("addSource") }}</button>
    </div>
    <p class="hint">{{ t("sourcesHint") }}</p>
    <p v-if="!sources.length" class="empty">{{ t("noSources") }}</p>

    <article v-for="(source, index) in sources" :key="index" class="source-card">
      <div class="source-head">
        <span class="source-title">{{ t("sourceLabel") }} {{ index + 1 }}</span>
        <label class="enabled-row">
          <input v-model="source.enabled" type="checkbox" @change="markDirty" />
          <span>{{ t("enabled") }}</span>
        </label>
        <button
          class="btn sm danger-text"
          type="button"
          :title="t('remove')"
          :aria-label="t('remove')"
          @click="removeSource(index)"
        >
          ✕
        </button>
      </div>

      <div class="field-row">
        <div class="field">
          <label :for="'source-name-' + index">{{ t("sourceName") }}</label>
          <input
            :id="'source-name-' + index"
            v-model="source.name"
            type="text"
            @input="markDirty"
          />
        </div>
        <div class="field">
          <label :for="'source-base-' + index">{{ t("apiBase") }}</label>
          <input
            :id="'source-base-' + index"
            v-model="source.api_base"
            type="text"
            placeholder="https://api.openai.com/v1"
            @input="markDirty"
          />
        </div>
      </div>

      <div class="field">
        <label>{{ t("apiKey") }}</label>
        <div class="keys-list">
          <div v-for="(key, keyIndex) in source.api_keys" :key="keyIndex" class="key-row">
            <input
              v-model="source.api_keys[keyIndex]"
              :type="isRevealed(index, keyIndex) ? 'text' : 'password'"
              autocomplete="off"
              :placeholder="t('secretPlaceholder')"
              @input="markDirty"
            />
            <button
              class="btn sm ghost"
              type="button"
              :title="t('revealKey')"
              :aria-label="t('revealKey')"
              @click="toggleReveal(index, keyIndex)"
            >
              👁
            </button>
            <button
              class="btn sm danger-text"
              type="button"
              :title="t('removeKey')"
              :aria-label="t('removeKey')"
              @click="removeKey(source, keyIndex)"
            >
              ✕
            </button>
          </div>
        </div>
        <button class="btn sm" type="button" @click="addKey(source)">{{ t("addKey") }}</button>
      </div>

      <div class="field models-block">
        <label>{{ t("sectionModels") }}</label>
        <p v-if="!source.models.length" class="empty">{{ t("noModels") }}</p>
        <div class="models-list">
          <div v-for="(model, modelIndex) in source.models" :key="modelIndex" class="model-row">
            <input
              v-model="model.id"
              class="model-id"
              type="text"
              placeholder="gpt-image-1"
              :title="t('modelId')"
              list="provider-list"
              @input="markDirty"
            />
            <label class="retry-wrap">
              <span>{{ t("retries") }}</span>
              <input
                v-model.number="model.retries"
                type="number"
                min="0"
                max="10"
                @input="markDirty"
              />
            </label>
            <button
              class="btn sm ghost"
              type="button"
              :disabled="modelIndex === 0"
              :title="t('up')"
              :aria-label="t('up')"
              @click="moveItem(source.models, modelIndex, -1)"
            >
              ↑
            </button>
            <button
              class="btn sm ghost"
              type="button"
              :disabled="modelIndex === source.models.length - 1"
              :title="t('down')"
              :aria-label="t('down')"
              @click="moveItem(source.models, modelIndex, 1)"
            >
              ↓
            </button>
            <button
              class="btn sm danger-text"
              type="button"
              :title="t('remove')"
              :aria-label="t('remove')"
              @click="removeModel(source, modelIndex)"
            >
              ✕
            </button>
          </div>
        </div>
        <div class="row-actions">
          <button class="btn sm" type="button" @click="addModel(source)">{{ t("addModel") }}</button>
          <button
            class="btn sm"
            type="button"
            :disabled="fetching[index]"
            @click="fetchModels(source, index)"
          >
            {{ fetching[index] ? t("fetchingModels") : t("fetchModels") }}
          </button>
        </div>

        <div v-if="pickers[index]" class="model-picker">
          <label class="picker-title">{{ t("pickModels") }}</label>
          <div class="picker-options">
            <label v-for="id in pickers[index].ids" :key="id" class="picker-option">
              <input v-model="pickers[index].checked" type="checkbox" :value="id" />
              <span>{{ id }}</span>
            </label>
          </div>
          <div class="picker-actions">
            <button class="btn sm" type="button" @click="toggleAll(index)">
              {{ t("selectAllModels") }}
            </button>
            <button class="btn sm primary" type="button" @click="addSelected(source, index)">
              {{ t("addSelected") }}
            </button>
          </div>
        </div>
      </div>

      <details class="source-advanced">
        <summary>{{ t("sourceAdvanced") }}</summary>
        <div class="switch-grid">
          <label class="switch-row">
            <input v-model="source.enable_generation" type="checkbox" @change="markDirty" />
            <span>{{ t("enableGeneration") }}</span>
          </label>
          <label class="switch-row">
            <input v-model="source.enable_edit" type="checkbox" @change="markDirty" />
            <span>{{ t("enableEdit") }}</span>
          </label>
          <label class="switch-row">
            <input v-model="source.validate_aspect_ratio" type="checkbox" @change="markDirty" />
            <span>{{ t("validateRatio") }}</span>
          </label>
        </div>
        <p class="hint">{{ t("validateRatioHint") }}</p>

        <div class="adv-fields">
          <div class="field">
            <label :for="'source-ratios-' + index">{{ t("aspectRatios") }}</label>
            <textarea
              v-grow
              :id="'source-ratios-' + index"
              :value="listLines(source.aspect_ratios)"
              rows="3"
              placeholder="1024x1024&#10;1536x1024"
              @input="setRatios(source, $event.target.value)"
            />
          </div>
          <div class="field">
            <label :for="'source-field-' + index">{{ t("ratioField") }}</label>
            <input
              :id="'source-field-' + index"
              v-model="source.aspect_ratio_field"
              type="text"
              placeholder="size"
              @input="markDirty"
            />
          </div>
          <div class="field">
            <label :for="'source-path-' + index">{{ t("responsePath") }}</label>
            <input
              :id="'source-path-' + index"
              v-model="source.response_image_path"
              type="text"
              placeholder="data"
              @input="markDirty"
            />
          </div>
          <div class="field">
            <label :for="'source-gen-' + index">{{ t("generationPrompt") }}</label>
            <textarea
              v-grow
              :id="'source-gen-' + index"
              v-model="source.generation_prompt"
              rows="2"
              @input="markDirty"
            />
          </div>
          <div class="field">
            <label :for="'source-edit-' + index">{{ t("editPrompt") }}</label>
            <textarea
              v-grow
              :id="'source-edit-' + index"
              v-model="source.edit_prompt"
              rows="2"
              @input="markDirty"
            />
          </div>
          <div class="field">
            <label :for="'source-extra-' + index">{{ t("extraBody") }}</label>
            <textarea
              v-grow
              :id="'source-extra-' + index"
              v-model="source.extra_request_body"
              rows="4"
              placeholder='{ "quality": "high" }'
              @input="markDirty"
            />
          </div>
          <div class="field">
            <label :for="'source-timeout-' + index">{{ t("timeout") }}</label>
            <input
              :id="'source-timeout-' + index"
              v-model.number="source.timeout"
              type="number"
              min="0"
              placeholder="0"
              @input="markDirty"
            />
          </div>
        </div>
      </details>
    </article>
  </section>
</template>

<script setup>
import { computed, reactive } from "vue";
import { t } from "../i18n.js";
import { markDirty, showAlert, store, toEditableModel, toEditableSource } from "../store.js";
import { listLines, splitLines, syncModelOrder } from "../collect.js";
import { apiPost } from "../sdk.js";

/* Read through a computed so the tab survives the store swapping the whole
 * config object when the backend reloads or saves. */
const sources = computed(() => store.config.sources);
const revealed = reactive({});
const fetching = reactive({});
const pickers = reactive({});

function isRevealed(index, keyIndex) {
  return !!revealed[`${index}:${keyIndex}`];
}

function toggleReveal(index, keyIndex) {
  const key = `${index}:${keyIndex}`;
  revealed[key] = !revealed[key];
}

function moveItem(list, index, step) {
  const target = index + step;
  if (target < 0 || target >= list.length) return;
  const [item] = list.splice(index, 1);
  list.splice(target, 0, item);
  markDirty();
}

function addSource() {
  sources.value.push(toEditableSource({}));
  markDirty();
}

function removeSource(index) {
  if (!window.confirm(t("confirmRemove"))) return;
  sources.value.splice(index, 1);
  markDirty();
}

function addKey(source) {
  source.api_keys.push("");
  markDirty();
}

/* Ratios stay a list in the config, so the textarea is bound by hand. */
function setRatios(source, value) {
  source.aspect_ratios = splitLines(value);
  markDirty();
}

function removeKey(source, index) {
  source.api_keys.splice(index, 1);
  markDirty();
}

function addModel(source) {
  source.models.push(toEditableModel(""));
  markDirty();
}

function removeModel(source, index) {
  if (!window.confirm(t("confirmRemoveModel"))) return;
  source.models.splice(index, 1);
  markDirty();
}

async function fetchModels(source, index) {
  const apiBase = String(source.api_base || "").trim().replace(/\/+$/, "");
  if (!apiBase) {
    showAlert("err", t("fetchModelsFailed") + t("apiBase"));
    return;
  }
  fetching[index] = true;
  try {
    const data = await apiPost("models", {
      api_base: apiBase,
      api_keys: (source.api_keys || []).map((key) => String(key || "").trim()).filter(Boolean),
    });
    const ids = (data && data.models) || [];
    if (!ids.length) {
      showAlert("err", t("fetchModelsEmpty"));
      return;
    }
    showAlert("ok", t("fetchModelsOk").replace("N", String(ids.length)));
    pickers[index] = { ids: ids, checked: [] };
  } catch (err) {
    showAlert("err", t("fetchModelsFailed") + (err && err.message ? err.message : err));
  } finally {
    fetching[index] = false;
  }
}

function toggleAll(index) {
  const picker = pickers[index];
  if (!picker) return;
  picker.checked =
    picker.checked.length === picker.ids.length ? [] : picker.ids.slice();
}

function addSelected(source, index) {
  const picker = pickers[index];
  if (!picker) return;
  const existing = {};
  source.models.forEach((model) => {
    existing[String(model.id || "").trim()] = true;
  });
  picker.checked.forEach((id) => {
    if (existing[id]) return;
    source.models.push(toEditableModel({ id: id, retries: 0 }));
  });
  delete pickers[index];
  syncModelOrder(store.config);
  markDirty();
}
</script>
