<template>
  <div class="layout">
    <aside class="side-nav">
      <div class="brand">
        <h1>{{ t("title") }}</h1>
      </div>
      <nav class="nav-group">
        <button
          v-for="item in tabs"
          :key="item.id"
          class="nav-item"
          :class="{ active: store.tab === item.id }"
          type="button"
          @click="store.tab = item.id"
        >
          {{ t(item.label) }}
        </button>
      </nav>
      <div class="nav-foot">
        <div class="actions">
          <button class="btn ghost" type="button" :disabled="store.busy" @click="loadAll()">
            {{ t("reload") }}
          </button>
          <button
            v-if="store.dirty"
            class="btn ghost"
            type="button"
            :disabled="store.busy"
            @click="discard()"
          >
            {{ t("cancelEdit") }}
          </button>
          <button
            v-if="store.dirty"
            class="btn primary"
            type="button"
            :disabled="store.busy"
            @click="save()"
          >
            {{ store.busy ? t("saving") : t("save") }}
          </button>
        </div>
        <div v-if="store.version" class="version">{{ store.version }}</div>
      </div>
    </aside>

    <main class="content">
      <div v-if="store.alert" class="alert" :class="store.alert.kind">
        <span>{{ store.alert.text }}</span>
        <button class="close" type="button" @click="store.alert = null">×</button>
      </div>

      <SourcesTab v-show="store.tab === 'sources'" />
      <ModelOrderTab v-show="store.tab === 'model-order'" />
      <ParamsTab v-show="store.tab === 'params'" />
      <ToolsTab v-show="store.tab === 'tools'" />
      <CommandsTab v-show="store.tab === 'commands'" />
      <LimitsTab v-show="store.tab === 'limits'" />

      <datalist id="provider-list">
        <option v-for="provider in store.providers" :key="provider.id" :value="provider.id">
          {{ provider.label || provider.id }}
        </option>
      </datalist>
    </main>
  </div>
</template>

<script setup>
import { onMounted } from "vue";
import { t } from "./i18n.js";
import { discardEdits, loadAll, saveConfig, store } from "./store.js";
import { collectConfig } from "./collect.js";
import SourcesTab from "./tabs/SourcesTab.vue";
import ModelOrderTab from "./tabs/ModelOrderTab.vue";
import ParamsTab from "./tabs/ParamsTab.vue";
import ToolsTab from "./tabs/ToolsTab.vue";
import CommandsTab from "./tabs/CommandsTab.vue";
import LimitsTab from "./tabs/LimitsTab.vue";

const tabs = [
  { id: "sources", label: "tabSources" },
  { id: "model-order", label: "tabModelOrder" },
  { id: "params", label: "tabParams" },
  { id: "tools", label: "tabTools" },
  { id: "commands", label: "tabCommands" },
  { id: "limits", label: "tabLimits" },
];

function discard() {
  discardEdits();
}

async function save() {
  const result = collectConfig(store.config);
  if (result.error) {
    store.alert = { kind: "err", text: result.error };
    return;
  }
  await saveConfig(result.config);
}

onMounted(() => loadAll());
</script>
