/** Small DOM, formatting and dialog helpers shared by the front-end modules. */

/** Create an element. `props` supports class, text, dataset, on* handlers and attributes. */
export function el(tag, props = {}, children = []) {
  const node = document.createElement(tag);

  for (const [key, value] of Object.entries(props)) {
    if (value === undefined || value === null) continue;
    if (key === "class") {
      node.className = value;
    } else if (key === "text") {
      node.textContent = value;
    } else if (key === "dataset") {
      Object.assign(node.dataset, value);
    } else if (key.startsWith("on") && typeof value === "function") {
      node.addEventListener(key.slice(2).toLowerCase(), value);
    } else {
      node.setAttribute(key, value);
    }
  }

  for (const child of [].concat(children)) {
    if (child === undefined || child === null || child === false) continue;
    node.append(child.nodeType ? child : document.createTextNode(String(child)));
  }

  return node;
}

/** Remove every child of a node. */
export function clear(node) {
  while (node.firstChild) node.removeChild(node.firstChild);
}

export function showError(container, message) {
  container.textContent = message;
  container.hidden = false;
}

export function hideError(container) {
  container.textContent = "";
  container.hidden = true;
}

export function clearFieldErrors(form) {
  form.querySelectorAll(".field-error").forEach((node) => {
    node.textContent = "";
    node.hidden = true;
  });
  form.querySelectorAll(".invalid").forEach((node) => node.classList.remove("invalid"));
}

/** Paint server-side validation messages (our 422 field errors) onto the form. */
export function applyFieldErrors(form, fields) {
  clearFieldErrors(form);
  let firstInvalid = null;

  for (const [name, message] of Object.entries(fields)) {
    const errorNode = form.querySelector(`[data-error-for="${name}"]`);
    if (errorNode) {
      errorNode.textContent = message;
      errorNode.hidden = false;
    }
    const input = form.elements[name];
    if (input) {
      input.classList.add("invalid");
      if (!firstInvalid) firstInvalid = input;
    }
  }

  if (firstInvalid) firstInvalid.focus();
}

/* --- Formatting ---------------------------------------------------------- */

const STATUS_LABELS = {
  pending: "To do",
  in_progress: "In progress",
  completed: "Done",
};

const PRIORITY_LABELS = {
  low: "Low",
  medium: "Medium",
  high: "High",
};

export function statusLabel(status) {
  return STATUS_LABELS[status] || status;
}

export function priorityLabel(priority) {
  return PRIORITY_LABELS[priority] || priority;
}

/** Parse an ISO calendar date as local midnight (avoids UTC day shifts). */
export function parseDate(value) {
  if (!value) return null;
  const [year, month, day] = String(value).split("-").map(Number);
  if (!year || !month || !day) return null;
  return new Date(year, month - 1, day);
}

function startOfDay(date) {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate());
}

export function formatDate(value, { year = true } = {}) {
  const date = value instanceof Date ? value : parseDate(value);
  if (!date) return "";
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    ...(year ? { year: "numeric" } : {}),
  }).format(date);
}

/** "Today", "Tomorrow", "Overdue · Oct 20" or a normal date. */
export function dueMeta(value, status = "pending") {
  const date = parseDate(value);
  if (!date) return { text: "", overdue: false };

  if (status === "completed") {
    return { text: `Due ${formatDate(date)}`, overdue: false };
  }

  const today = startOfDay(new Date());
  const diff = Math.round((date - today) / 86_400_000);
  if (diff < 0) {
    return {
      text: `${Math.abs(diff) === 1 ? "1 day" : `${Math.abs(diff)} days`} overdue`,
      overdue: true,
    };
  }
  if (diff === 0) return { text: "Due today", overdue: false };
  if (diff === 1) return { text: "Due tomorrow", overdue: false };
  return { text: `Due ${formatDate(date)}`, overdue: false };
}

export function relativeTime(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";

  const seconds = Math.round((Date.now() - date.getTime()) / 1000);
  if (seconds < 60) return "Just now";
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.round(hours / 24);
  if (days === 1) return "Yesterday";
  if (days < 7) return `${days}d ago`;
  return formatDate(date);
}

/* --- Feedback ------------------------------------------------------------ */

export function showToast(message, { tone = "success" } = {}) {
  const region = document.getElementById("toast-region");
  if (!region) return;

  const toast = el("div", {
    class: `toast${tone === "error" ? " is-error" : ""}`,
    role: "status",
    text: message,
  });
  region.append(toast);

  window.setTimeout(() => {
    toast.classList.add("is-leaving");
    window.setTimeout(() => toast.remove(), 180);
  }, 2600);
}

/* --- Dialogs ------------------------------------------------------------- */

export function openDialog(dialog, focusSelector = null) {
  document.body.classList.add("dialog-open");
  if (!dialog.open) dialog.showModal();
  if (focusSelector) {
    const target = dialog.querySelector(focusSelector);
    if (target) window.setTimeout(() => target.focus(), 0);
  }
}

export function closeDialog(dialog) {
  if (dialog.open) dialog.close();
}

/** Wire close buttons, backdrop clicks and body scroll locking for a dialog. */
export function setupDialog(dialog) {
  if (!dialog) return;

  dialog.querySelectorAll("[data-close-dialog]").forEach((button) => {
    button.addEventListener("click", () => dialog.close());
  });

  dialog.addEventListener("click", (event) => {
    if (event.target === dialog) dialog.close();
  });

  dialog.addEventListener("close", () => {
    if (!document.querySelector("dialog[open]")) {
      document.body.classList.remove("dialog-open");
    }
  });
}

/**
 * Ask for confirmation with the shared dialog. Resolves true only when the
 * primary action was clicked.
 */
export function confirmAction({
  title = "Are you sure?",
  message = "",
  confirmLabel = "Delete",
} = {}) {
  const dialog = document.getElementById("confirm-dialog");
  const messageEl = document.getElementById("confirm-message");
  const titleEl = document.getElementById("confirm-title");
  const accept = document.getElementById("confirm-accept");
  const cancel = document.getElementById("confirm-cancel");

  if (!dialog || !messageEl || !titleEl || !accept || !cancel) {
    return Promise.resolve(window.confirm(message));
  }

  titleEl.textContent = title;
  messageEl.textContent = message;
  accept.textContent = confirmLabel;

  return new Promise((resolve) => {
    dialog.returnValue = "";
    dialog.addEventListener("close", () => resolve(dialog.returnValue === "confirm"), {
      once: true,
    });
    accept.onclick = () => dialog.close("confirm");
    cancel.onclick = () => dialog.close("cancel");
    openDialog(dialog, "#confirm-cancel");
  });
}
