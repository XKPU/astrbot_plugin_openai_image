<template>
  <section class="tab-panel">
    <h2 class="section-title">{{ t("sectionCommands") }}</h2>

    <label class="switch-row">
      <input v-model="store.config.enable_commands" type="checkbox" @change="markDirty" />
      <span>{{ t("enableCommands") }}</span>
    </label>

    <p class="hint">{{ t("commandsHint") }}</p>
    <p class="hint">{{ t("commandHeadsEmpty") }}</p>

    <div class="grid-2">
      <div class="field">
        <label for="command_generation_head">{{ t("commandGenerationHead") }}</label>
        <textarea
          v-grow
          id="command_generation_head"
          :value="listLines(store.config.command_generation_head)"
          rows="3"
          @input="setList('command_generation_head', $event.target.value)"
        />
      </div>
      <div class="field">
        <label for="command_edit_head">{{ t("commandEditHead") }}</label>
        <textarea
          v-grow
          id="command_edit_head"
          :value="listLines(store.config.command_edit_head)"
          rows="3"
          @input="setList('command_edit_head', $event.target.value)"
        />
      </div>
    </div>

    <div class="grid-2">
      <div class="field">
        <label for="command_prefix">{{ t("commandPrefix") }}</label>
        <input
          id="command_prefix"
          v-model="store.config.command_prefix"
          type="text"
          placeholder="/"
          @input="markDirty"
        />
      </div>
      <div class="field">
        <label for="command_arg_mode">{{ t("commandArgMode") }}</label>
        <select id="command_arg_mode" v-model="store.config.command_arg_mode" @change="markDirty">
          <option value="off">{{ t("commandArgModeOff") }}</option>
          <option value="all">{{ t("commandArgModeAll") }}</option>
          <option value="listed">{{ t("commandArgModeListed") }}</option>
        </select>
      </div>
    </div>

    <div class="field">
      <label for="command_allowed_args">{{ t("commandAllowedArgs") }}</label>
      <textarea
        v-grow
        id="command_allowed_args"
        :value="listLines(store.config.command_allowed_args)"
        rows="3"
        :disabled="!argModeEnabled(store.config)"
        @input="setList('command_allowed_args', $event.target.value)"
      />
    </div>

    <p class="hint">{{ t("commandArgsHint") }}</p>

    <h2 class="section-title">{{ t("sectionPromptPolish") }}</h2>

    <label class="switch-row">
      <input v-model="store.config.command_enable_polish" type="checkbox" @change="markDirty" />
      <span>{{ t("commandEnablePolish") }}</span>
    </label>

    <div class="field">
      <label for="command_polish_provider">{{ t("commandPolishProvider") }}</label>
      <select
        id="command_polish_provider"
        v-model="store.config.command_polish_provider"
        @change="markDirty"
      >
        <option value="">{{ t("commandPolishDefault") }}</option>
        <option v-for="provider in store.providers" :key="provider.id" :value="provider.id">
          {{ provider.label || provider.id }}
        </option>
      </select>
    </div>
  </section>
</template>

<script setup>
import { t } from "../i18n.js";
import { markDirty, store } from "../store.js";
import { argModeEnabled, listLines, splitLines } from "../collect.js";

/* Heads and lists stay arrays in the config, so their textareas are bound by hand. */
function setList(key, value) {
  store.config[key] = splitLines(value);
  markDirty();
}
</script>
