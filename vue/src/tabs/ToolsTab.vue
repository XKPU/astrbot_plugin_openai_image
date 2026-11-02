<template>
  <section class="tab-panel">
    <h2 class="section-title">{{ t("sectionToggles") }}</h2>

    <label class="switch-row">
      <input v-model="store.config.enable_generation" type="checkbox" @change="markDirty" />
      <span>{{ t("enableGenerationTool") }}</span>
    </label>

    <label class="switch-row">
      <input v-model="store.config.enable_edit" type="checkbox" @change="markDirty" />
      <span>{{ t("enableEditTool") }}</span>
    </label>

    <label class="switch-row">
      <input v-model="store.config.enable_prompt_polish" type="checkbox" @change="markDirty" />
      <span>{{ t("enablePromptPolish") }}</span>
    </label>

    <h2 class="section-title">{{ t("sectionReturn") }}</h2>

    <label class="switch-row">
      <input v-model="store.config.return_elapsed" type="checkbox" @change="markDirty" />
      <span>{{ t("returnElapsed") }}</span>
    </label>

    <label class="switch-row">
      <input v-model="store.config.return_id" type="checkbox" @change="markDirty" />
      <span>{{ t("returnId") }}</span>
    </label>

    <label class="switch-row">
      <input v-model="store.config.return_model" type="checkbox" @change="markDirty" />
      <span>{{ t("returnModel") }}</span>
    </label>

    <label class="switch-row">
      <input v-model="store.config.return_retries" type="checkbox" @change="markDirty" />
      <span>{{ t("returnRetries") }}</span>
    </label>
  </section>
</template>

<script setup>
import { t } from "../i18n.js";
import { markDirty, store } from "../store.js";
</script>
