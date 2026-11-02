import { createApp } from "vue";
import App from "./App.vue";
import { vGrow } from "./grow.js";
import { setLocale } from "./i18n.js";
import { sdk } from "./sdk.js";

/* Follow the dashboard language and keep tracking later switches. */
const bridge = sdk();
if (bridge) {
  if (typeof bridge.onContext === "function") {
    bridge.onContext((context) => {
      if (context && context.locale) setLocale(context.locale);
    });
  }
  if (typeof bridge.getLocale === "function") {
    setLocale(bridge.getLocale());
  }
}

createApp(App).directive("grow", vGrow).mount("#app");
