<template>
  <div class="sender-picker">
    <div class="chip-row">
      <span v-for="item in selected" :key="item.id" class="chip" :title="item.id">
        {{ item.name || item.id }}
        <button type="button" class="chip-close" @click="toggle(item.id)">×</button>
      </span>
      <button type="button" class="btn tonal sm" @click="open">{{ t("senderManage") }}</button>
    </div>

    <div v-if="visible" class="modal-mask" @click.self="close">
      <div class="modal-card">
        <div class="modal-head">
          <h3 class="modal-title">{{ t("senderPickerTitle") }}</h3>
          <button type="button" class="chip-close" @click="close">×</button>
        </div>
        <div class="modal-body">
          <div class="field">
            <input
              v-model="keyword"
              type="text"
              :placeholder="t('senderSearch')"
              @input="onInput"
              @keyup.enter="canAddKeyword && addKeyword()"
            />
          </div>
          <p v-if="error" class="alert err">{{ error }}</p>
          <p v-if="loading" class="hint">{{ t("senderLoading") }}</p>
          <p v-else-if="results.length === 0" class="empty">{{ t("senderEmpty") }}</p>
          <div v-else class="sender-list">
            <label v-for="row in results" :key="row.sender_id" class="sender-row">
              <input
                type="checkbox"
                :checked="indexOf(row.sender_id) >= 0"
                @change="toggle(row.sender_id)"
              />
              <span class="sender-name">{{ row.sender_name || row.sender_id }}</span>
              <span v-if="row.sender_name" class="sender-id">{{ row.sender_id }}</span>
              <span v-if="row.platform" class="sender-platform">{{ row.platform }}</span>
            </label>
          </div>
          <div v-if="canAddKeyword" class="row-actions sender-manual">
            <button type="button" class="btn tonal sm" @click="addKeyword">
              {{ t("senderAddManual") }}
            </button>
          </div>
        </div>
        <div class="modal-foot">
          <button type="button" class="btn primary" @click="close">{{ t("senderDone") }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, reactive, ref, watch } from "vue";
import { t } from "../i18n.js";
import { apiGet } from "../sdk.js";

const props = defineProps({ modelValue: { type: Array, default: () => [] } });
const emit = defineEmits(["update:modelValue"]);

const visible = ref(false);
const keyword = ref("");
const results = ref([]);
const loading = ref(false);
const error = ref("");
const names = reactive({});

const selected = computed(() =>
  (props.modelValue || []).map((id) => ({ id, name: names[id] || "" })),
);

/* Offer the typed keyword as an id when no known sender matches it. */
const canAddKeyword = computed(() => {
  const value = keyword.value.trim();
  if (!value || loading.value) return false;
  if (indexOf(value) >= 0) return false;
  return !results.value.some((row) => String(row.sender_id) === value);
});

function addKeyword() {
  const value = keyword.value.trim();
  if (!value || indexOf(value) >= 0) return;
  emit("update:modelValue", (props.modelValue || []).concat(value));
}

function indexOf(senderId) {
  return (props.modelValue || []).indexOf(senderId);
}

function toggle(senderId) {
  const next = (props.modelValue || []).slice();
  const at = next.indexOf(senderId);
  if (at >= 0) {
    next.splice(at, 1);
  } else {
    next.push(senderId);
  }
  emit("update:modelValue", next);
}

/* Resolve saved ids to names so the chips read as names, not raw ids. */
async function resolveNames(ids) {
  const missing = ids.filter((id) => id && !names[id]);
  if (missing.length === 0) return;
  try {
    const data = await apiGet("senders", { sender_ids: missing, limit: 100 });
    for (const row of (data && data.senders) || []) {
      if (row.sender_name) names[row.sender_id] = row.sender_name;
    }
  } catch (err) {
    /* Names are cosmetic here; raw ids stay visible when this fails. */
  }
}

async function search() {
  loading.value = true;
  error.value = "";
  try {
    const data = await apiGet("senders", { search: keyword.value.trim(), limit: 50 });
    results.value = (data && data.senders) || [];
    for (const row of results.value) {
      if (row.sender_name) names[row.sender_id] = row.sender_name;
    }
  } catch (err) {
    results.value = [];
    error.value = t("senderLoadFailed");
  } finally {
    loading.value = false;
  }
}

let timer = 0;
function onInput() {
  clearTimeout(timer);
  timer = setTimeout(search, 250);
}

function open() {
  visible.value = true;
  keyword.value = "";
  results.value = [];
  resolveNames(props.modelValue || []);
  search();
}

function close() {
  visible.value = false;
}

/* Names follow the saved ids, including ids restored from the server. */
watch(() => props.modelValue, (ids) => resolveNames(ids || []), {
  immediate: true,
  deep: true,
});
</script>
