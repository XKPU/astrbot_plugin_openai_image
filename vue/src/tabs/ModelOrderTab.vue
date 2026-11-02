<template>
  <section class="tab-panel">
    <div class="panel-head">
      <h2>{{ t("tabModelOrder") }}</h2>
    </div>
    <p class="hint">{{ t("modelOrderHint") }}</p>

    <p v-if="!rows.length" class="empty">{{ t("orderEmpty") }}</p>

    <div v-else class="order-list">
      <div v-for="(row, index) in rows" :key="row.tag" class="order-row">
        <label class="order-toggle">
          <input
            :checked="!row.disabled"
            :title="t('orderEnabled')"
            type="checkbox"
            @change="toggle(row.tag, $event.target.checked)"
          />
          <span class="order-id" :class="{ off: row.disabled }">{{ row.tag }}</span>
        </label>
        <button
          class="btn ghost sm"
          type="button"
          :disabled="index === 0"
          :title="t('up')"
          @click="move(index, -1)"
        >
          ↑
        </button>
        <button
          class="btn ghost sm"
          type="button"
          :disabled="index === rows.length - 1"
          :title="t('down')"
          @click="move(index, 1)"
        >
          ↓
        </button>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed } from "vue";
import { t } from "../i18n.js";
import { markDirty, normalizeList, store } from "../store.js";
import { sourceTags } from "../collect.js";

/* Rows always mirror the models the sources currently define, so the page
 * never drifts from the source list. Only order and the enabled flag are
 * editable here. */
const rows = computed(() => {
  const available = sourceTags(store.config.sources);
  const disabled = normalizeList(store.config.model_disabled, []);
  const order = [];
  normalizeList(store.config.model_order, []).forEach((tag) => {
    if (available.indexOf(tag) >= 0 && order.indexOf(tag) < 0) order.push(tag);
  });
  available.forEach((tag) => {
    if (order.indexOf(tag) < 0) order.push(tag);
  });
  return order.map((tag) => ({ tag: tag, disabled: disabled.indexOf(tag) >= 0 }));
});

function toggle(tag, enabled) {
  const disabled = normalizeList(store.config.model_disabled, []);
  const index = disabled.indexOf(tag);
  if (enabled && index >= 0) disabled.splice(index, 1);
  if (!enabled && index < 0) disabled.push(tag);
  store.config.model_disabled = disabled;
  markDirty();
}

function move(index, step) {
  const order = rows.value.map((row) => row.tag);
  const target = index + step;
  if (target < 0 || target >= order.length) return;
  const [tag] = order.splice(index, 1);
  order.splice(target, 0, tag);
  store.config.model_order = order;
  markDirty();
}
</script>
