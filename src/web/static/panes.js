// Pane handles (D-46): drag a handle to resize a pane, keep the widths of a page in the browser
// (localStorage), and reset them with the sidebar button. Events are delegated on `document`,
// so a handle that HTMX swaps in works at once.

const STORAGE_PREFIX = "design-kb.panes.";
const DEFAULT_PANE_MIN = 240;

let keptWidths = {};
let drag = null;

/** Return the localStorage key of this page. */
function storageKey() {
  return STORAGE_PREFIX + document.body.dataset.page;
}

/** Return the saved widths of this page, or an empty object when the storage is blocked or empty. */
function loadWidths() {
  try {
    return JSON.parse(window.localStorage.getItem(storageKey())) || {};
  } catch (error) {
    return {};
  }
}

/** Save the widths of this page; a blocked storage is ignored, so the widths last for the visit. */
function saveWidths() {
  try {
    window.localStorage.setItem(storageKey(), JSON.stringify(keptWidths));
  } catch (error) {
    // No storage: keptWidths in memory is all there is.
  }
}

/** Delete the saved widths of this page. */
function deleteWidths() {
  try {
    window.localStorage.removeItem(storageKey());
  } catch (error) {
    // No storage: nothing to delete.
  }
}

/** Return the smallest width of a pane in pixels, read from --pane-min on :root. */
function paneMin() {
  const value = getComputedStyle(document.documentElement).getPropertyValue("--pane-min");
  return parseFloat(value) || DEFAULT_PANE_MIN;
}

/** Put the kept widths on the fixed panes of the page. */
function applyWidths() {
  document.querySelectorAll("[data-pane]:not([data-pane-flex])").forEach(setKeptWidth);
}

/** Put the kept width on one pane, if the page kept one for it. */
function setKeptWidth(pane) {
  const width = keptWidths[pane.dataset.pane];
  if (typeof width === "number") {
    pane.style.setProperty("--pane-width", width + "px");
  }
}

/** Show the reset button only when the page has a handle. */
function updateResetButton() {
  const button = document.querySelector("[data-pane-reset]");
  if (button !== null) {
    button.hidden = document.querySelector("[data-pane-handle]") === null;
  }
}

/** Return the pane that a handle resizes: the left one, or the right one when the left is flexible. */
function paneToResize(handle) {
  const left = handle.previousElementSibling;
  const right = handle.nextElementSibling;
  return left.hasAttribute("data-pane-flex") ? right : left;
}

/** Start a drag when the pointer goes down on a handle. */
function onPointerDown(event) {
  const handle = event.target.closest("[data-pane-handle]");
  if (handle === null) {
    return;
  }
  const target = paneToResize(handle);
  const other = target === handle.previousElementSibling ? handle.nextElementSibling : handle.previousElementSibling;
  drag = {
    handle: handle,
    target: target,
    startX: event.clientX,
    startWidth: target.getBoundingClientRect().width,
    otherWidth: other.getBoundingClientRect().width,
    direction: target === handle.previousElementSibling ? 1 : -1,
  };
  handle.setPointerCapture(event.pointerId);
  handle.classList.add("dragging");
  event.preventDefault();
}

/** Move the edge of the pane with the pointer, and stop where a neighbour gets narrower than --pane-min. */
function onPointerMove(event) {
  if (drag === null) {
    return;
  }
  const min = paneMin();
  const wanted = drag.startWidth + (event.clientX - drag.startX) * drag.direction;
  const largest = drag.startWidth + drag.otherWidth - min;
  const width = Math.max(min, Math.min(wanted, largest));
  drag.target.style.setProperty("--pane-width", width + "px");
}

/** End the drag and keep the new width of the pane. */
function onPointerUp() {
  if (drag === null) {
    return;
  }
  const width = parseFloat(drag.target.style.getPropertyValue("--pane-width"));
  if (!Number.isNaN(width)) {
    keptWidths[drag.target.dataset.pane] = Math.round(width);
    saveWidths();
  }
  drag.handle.classList.remove("dragging");
  drag = null;
}

/** Remove the dragged width of one pane, so that the default of app.css applies. */
function clearPaneWidth(pane) {
  pane.style.removeProperty("--pane-width");
}

/** Reset the widths of the page to the defaults when the reset button is clicked. */
function onClick(event) {
  if (event.target.closest("[data-pane-reset]") === null) {
    return;
  }
  keptWidths = {};
  deleteWidths();
  document.querySelectorAll("[data-pane]").forEach(clearPaneWidth);
}

/** Apply the kept widths and show the reset button, at load and after an HTMX swap. */
function refreshPanes() {
  applyWidths();
  updateResetButton();
}

keptWidths = loadWidths();
refreshPanes();
document.addEventListener("pointerdown", onPointerDown);
document.addEventListener("pointermove", onPointerMove);
document.addEventListener("pointerup", onPointerUp);
document.addEventListener("pointercancel", onPointerUp);
document.addEventListener("click", onClick);
document.addEventListener("htmx:afterSwap", refreshPanes);
