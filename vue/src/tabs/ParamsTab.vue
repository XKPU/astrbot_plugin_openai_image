<template>
  <section class="tab-panel">
    <h2 class="section-title">{{ t("sectionPrompts") }}</h2>

    <div class="field">
      <label for="generation_prompt">{{ t("generationPrompt") }}</label>
      <textarea
        v-grow
        id="generation_prompt"
        v-model="store.config.generation_prompt"
        rows="3"
        @input="markDirty"
      />
    </div>

    <div class="field">
      <label for="edit_prompt">{{ t("editPrompt") }}</label>
      <textarea v-grow id="edit_prompt" v-model="store.config.edit_prompt" rows="3" @input="markDirty" />
    </div>

    <h2 class="section-title">{{ t("sectionParams") }}</h2>

    <div class="grid-2">
      <div class="field">
        <label for="available_aspect_ratios">{{ t("globalRatios") }}</label>
        <textarea
          v-grow
          id="available_aspect_ratios"
          :value="listLines(store.config.available_aspect_ratios)"
          rows="3"
          @input="setList('available_aspect_ratios', $event.target.value)"
        />
      </div>
      <div class="field">
        <label for="aspect_ratio_field">{{ t("globalRatioField") }}</label>
        <input
          id="aspect_ratio_field"
          v-model="store.config.aspect_ratio_field"
          type="text"
          placeholder="size"
          @input="markDirty"
        />
      </div>
    </div>

    <div class="grid-2">
      <div class="field">
        <label for="response_image_path">{{ t("responsePath") }}</label>
        <input
          id="response_image_path"
          v-model="store.config.response_image_path"
          type="text"
          placeholder="data"
          @input="markDirty"
        />
      </div>
      <div class="field">
        <label for="timeout">{{ t("globalTimeout") }}</label>
        <input
          id="timeout"
          v-model.number="store.config.timeout"
          type="number"
          min="1"
          @input="markDirty"
        />
      </div>
    </div>

    <div class="field">
      <label for="extra_request_body">{{ t("globalExtraBody") }}</label>
      <textarea
        v-grow
        id="extra_request_body"
        v-model="store.config.extra_request_body"
        rows="4"
        placeholder='{ "quality": "high" }'
        @input="markDirty"
      />
    </div>
  </section>
</template>

<script setup>
import { t } from "../i18n.js";
import { markDirty, store } from "../store.js";
import { listLines, splitLines } from "../collect.js";

/* Ratios stay a list in the config, so the textarea is bound by hand. */
function setList(key, value) {
  store.config[key] = splitLines(value);
  markDirty();
}
</script>
