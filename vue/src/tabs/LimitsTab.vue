<template>
  <section class="tab-panel">
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
        <label class="field-sub" for="access_group_ids">{{ t("accessGroupIds") }}</label>
        <textarea
          v-grow
          id="access_group_ids"
          :value="listLines(store.config.access_group_ids)"
          rows="3"
          @input="setList('access_group_ids', $event.target.value)"
        />
      </div>
      <div class="field">
        <label for="access_user_mode">{{ t("accessUserMode") }}</label>
        <select id="access_user_mode" v-model="store.config.access_user_mode" @change="markDirty">
          <option value="off">{{ t("modeOff") }}</option>
          <option value="whitelist">{{ t("modeWhitelist") }}</option>
          <option value="blacklist">{{ t("modeBlacklist") }}</option>
        </select>
        <label class="field-sub" for="access_user_ids">{{ t("accessUserIds") }}</label>
        <textarea
          v-grow
          id="access_user_ids"
          :value="listLines(store.config.access_user_ids)"
          rows="3"
          @input="setList('access_user_ids', $event.target.value)"
        />
      </div>
    </div>

    <h2 class="section-title">{{ t("sectionQuota") }}</h2>

    <p class="hint">{{ t("quotaHint") }}</p>

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
      <label>{{ t("quotaExemptUsers") }}</label>
      <SenderPicker
        :model-value="store.config.quota_exempt_user_ids"
        @update:model-value="setExemptUsers"
      />
    </div>

    <label class="switch-row">
      <input v-model="store.config.checkin_enabled" type="checkbox" @change="markDirty" />
      <span>{{ t("checkinEnabled") }}</span>
    </label>

    <p class="hint">{{ t("checkinHint") }}</p>

    <div class="grid-2">
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
    </div>

    <div class="grid-2">
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
        <textarea
          v-grow
          id="checkin_fail"
          v-model="store.config.checkin_fail"
          rows="3"
          @input="markDirty"
        />
      </div>
    </div>
  </section>
</template>

<script setup>
import { markDirty, store } from "../store.js";
import { t } from "../i18n.js";
import { listLines, splitLines } from "../collect.js";
import SenderPicker from "../components/SenderPicker.vue";

/* Lists stay arrays in the config, so their textareas are bound by hand. */
function setList(key, value) {
  store.config[key] = splitLines(value);
  markDirty();
}

function setExemptUsers(ids) {
  store.config.quota_exempt_user_ids = ids.slice();
  markDirty();
}
</script>
