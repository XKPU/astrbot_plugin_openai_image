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

    <h2 class="section-title">{{ t("sectionAccess") }}</h2>

    <p class="hint">{{ t("accessHint") }}</p>

    <div class="grid-2">
      <div class="field">
        <label for="access_group_mode">{{ t("accessGroupMode") }}</label>
        <select id="access_group_mode" v-model="store.config.access_group_mode" @change="markDirty">
          <option value="off">{{ t("modeOff") }}</option>
          <option value="whitelist">{{ t("modeWhitelist") }}</option>
          <option value="blacklist">{{ t("modeBlacklist") }}</option>
        </select>
      </div>
      <div class="field">
        <label for="access_user_mode">{{ t("accessUserMode") }}</label>
        <select id="access_user_mode" v-model="store.config.access_user_mode" @change="markDirty">
          <option value="off">{{ t("modeOff") }}</option>
          <option value="whitelist">{{ t("modeWhitelist") }}</option>
          <option value="blacklist">{{ t("modeBlacklist") }}</option>
        </select>
      </div>
    </div>

    <div class="field">
      <label for="access_group_ids">{{ t("accessGroupIds") }}</label>
      <textarea
        v-grow
        id="access_group_ids"
        :value="listLines(store.config.access_group_ids)"
        rows="3"
        @input="setList('access_group_ids', $event.target.value)"
      />
    </div>

    <div class="field">
      <label for="access_user_ids">{{ t("accessUserIds") }}</label>
      <textarea
        v-grow
        id="access_user_ids"
        :value="listLines(store.config.access_user_ids)"
        rows="3"
        @input="setList('access_user_ids', $event.target.value)"
      />
    </div>

    <div class="grid-2">
      <div class="field">
        <label for="quota_daily_limit">{{ t("quotaDailyLimit") }}</label>
        <input
          id="quota_daily_limit"
          v-model.number="store.config.quota_daily_limit"
          type="number"
          min="0"
          @input="markDirty"
        />
      </div>
      <div class="field">
        <label for="checkin_bonus">{{ t("checkinBonus") }}</label>
        <input
          id="checkin_bonus"
          v-model.number="store.config.checkin_bonus"
          type="number"
          min="0"
          @input="markDirty"
        />
      </div>
    </div>

    <label class="switch-row">
      <input v-model="store.config.checkin_enabled" type="checkbox" @change="markDirty" />
      <span>{{ t("checkinEnabled") }}</span>
    </label>

    <p class="hint">{{ t("checkinHint") }}</p>

    <div class="field">
      <label for="checkin_heads">{{ t("checkinHeads") }}</label>
      <textarea
        v-grow
        id="checkin_heads"
        :value="listLines(store.config.checkin_heads)"
        rows="3"
        @input="setList('checkin_heads', $event.target.value)"
      />
    </div>

    <div class="field">
      <label for="checkin_success">{{ t("checkinSuccess") }}</label>
      <textarea
        v-grow
        id="checkin_success"
        v-model="store.config.checkin_success"
        rows="3"
        @input="markDirty"
      />
    </div>

    <div class="field">
      <label for="checkin_fail">{{ t("checkinFail") }}</label>
      <textarea v-grow id="checkin_fail" v-model="store.config.checkin_fail" rows="3" @input="markDirty" />
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
