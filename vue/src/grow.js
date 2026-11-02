/* Fit a textarea to its content. min-height and max-height in style.css keep
 * it inside the allowed range, so an over-long text scrolls instead of
 * growing further. */
function fit(element) {
  /* A hidden panel reports a zero height, which would collapse the field. */
  if (!element.offsetParent) return;
  element.style.height = "auto";
  element.style.height = `${element.scrollHeight}px`;
}

/* Vue directive that keeps textareas content-sized without allowing manual
 * resizing. */
export const vGrow = {
  mounted(element) {
    const handler = () => fit(element);
    element.__growFit = handler;
    element.addEventListener("input", handler);
    /* v-show only toggles the display style, so a field must refit itself once
     * its panel becomes visible again. Only width changes are honoured: height
     * changes come from this very handler and would otherwise loop. */
    if (typeof ResizeObserver === "function") {
      let width = element.clientWidth;
      element.__growObserver = new ResizeObserver(() => {
        if (element.clientWidth === width) return;
        width = element.clientWidth;
        handler();
      });
      element.__growObserver.observe(element);
    }
    fit(element);
  },
  updated(element) {
    fit(element);
  },
  unmounted(element) {
    element.removeEventListener("input", element.__growFit);
    if (element.__growObserver) element.__growObserver.disconnect();
  },
};
