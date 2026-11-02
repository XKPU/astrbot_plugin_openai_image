/* Thin wrapper around the bridge SDK injected by the dashboard. */

export function sdk() {
  return window.AstrBotPluginView || window.AstrBotPluginPage || null;
}

/* Unwrap {"status":"ok","data":...} envelopes. */
export function pick(data) {
  return data && data.data ? data.data : data;
}

export async function apiGet(endpoint, params) {
  const bridge = sdk();
  if (!bridge) throw new Error("bridge not ready");
  return await bridge.apiGet(endpoint, params);
}

export async function apiPost(endpoint, body) {
  const bridge = sdk();
  if (!bridge) throw new Error("bridge not ready");
  return await bridge.apiPost(endpoint, body);
}

export async function bridgeReady() {
  const bridge = sdk();
  try {
    if (bridge && typeof bridge.ready === "function") {
      await bridge.ready();
    }
  } catch (err) {
    /* ready() is best-effort; API calls still work after it. */
  }
}
