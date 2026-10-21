import { ApiError, apiFetch } from "./api.js";
import { renderNav } from "./nav.js";
import {
  applyFieldErrors,
  clear,
  clearFieldErrors,
  confirmAction,
  dueMeta,
  el,
  hideError,
  openDialog,
  setupDialog,
  showError,
  showToast,
} from "./ui.js";

const projectId = Number(window.location.pathname.split("/").filter(Boolean).pop());

const state = { project: null, tasks: [], filter: "all" };

const errorBox = document.getElementById("global-error");
const notFound = document.getElementById("not-found");
const content = document.getElementById("project-content");

const titleEl = document.getElementById("project-title");
const descEl = document.getElementById("project-description");
const statusBadge = document.getElementById("project-status-badge");
const dueDateEl = document.getElementById("project-due-date");
const progressEl = document.getElementById("project-progress");
const progressFill = document.getElementById("project-progress-fill");
const progressLabel = document.getElementById("project-progress-label");

const editBtn = document.getElementById("edit-project-btn");
const deleteBtn = document.getElementById("delete-project-btn");
const projectDialog = document.getElementById("project-dialog");
const projectForm = document.getElementById("project-edit-form");

const taskForm = document.getElementById("task-form");
const taskList = document.getElementById("task-list");
const tasksEmpty = document.getElementById("tasks-empty");
const taskPanel = document.getElementById("task-panel");
const taskPanelForm = document.getElementById("task-panel-form");
const taskPanelTitle = document.getElementById("task-panel-title");
const taskDelete = document.getElementById("task-delete");

renderNav();
setupDialog(document.getElementById("confirm-dialog"));
setupDialog(projectDialog);
setupDialog(taskPanel);

/* --- Project ------------------------------------------------------------- */

function projectState() {
  const total = state.tasks.length;
  const done = state.tasks.filter((task) => task.status === "completed").length;
  const active = state.tasks.filter((task) => task.status === "in_progress").length;

  if (!total) return { label: "Not started", className: "badge-pending" };
  if (done === total) return { label: "Done", className: "badge-completed" };
  if (active > 0 || done > 0) {
    return { label: "In progress", className: "badge-in_progress" };
  }
  return { label: "To do", className: "badge-pending" };
}

function renderProject() {
  if (!state.project) return;

  titleEl.textContent = state.project.name;
  document.title = `${state.project.name} · TrackIt`;

  if (state.project.description) {
    descEl.textContent = state.project.description;
    descEl.hidden = false;
  } else {
    descEl.textContent = "";
    descEl.hidden = true;
  }

  const status = projectState();
  statusBadge.className = `badge ${status.className}`;
  statusBadge.textContent = status.label;

  if (state.project.due_date) {
    const done = state.tasks.length && state.tasks.every((task) => task.status === "completed");
    const due = dueMeta(state.project.due_date, done ? "completed" : "pending");
    dueDateEl.textContent = due.text;
    dueDateEl.classList.toggle("is-overdue", due.overdue);
  } else {
    dueDateEl.textContent = "No due date";
    dueDateEl.classList.remove("is-overdue");
  }

  const total = state.tasks.length;
  const done = state.tasks.filter((task) => task.status === "completed").length;
  const percent = total ? Math.round((done / total) * 100) : 0;

  progressFill.style.width = `${percent}%`;
  progressEl.classList.toggle("is-complete", percent === 100 && total > 0);
  progressEl.setAttribute("aria-valuenow", String(percent));
  progressLabel.textContent = total
    ? `${done} of ${total} tasks completed`
    : "No tasks yet";
}

function renderFilterCounts() {
  const counts = { all: state.tasks.length, pending: 0, in_progress: 0, completed: 0 };
  for (const task of state.tasks) counts[task.status] = (counts[task.status] || 0) + 1;

  for (const [key, value] of Object.entries(counts)) {
    const node = document.getElementById(`filter-${key}-count`);
    if (node) node.textContent = value;
  }

  document.querySelectorAll("[data-filter]").forEach((button) => {
    const active = button.dataset.filter === state.filter;
    button.classList.toggle("is-active", active);
    button.setAttribute("aria-pressed", String(active));
  });
}

/* --- Tasks --------------------------------------------------------------- */

function setControlClass(select, kind) {
  select.className = `inline-select ${kind}-${select.value}`;
}

function taskItem(task) {
  const checkbox = el("input", {
    type: "checkbox",
    class: "task-check",
    "aria-label":
      task.status === "completed"
        ? `Reopen "${task.title}"`
        : `Mark "${task.title}" as completed`,
  });
  checkbox.checked = task.status === "completed";
  checkbox.addEventListener("change", () => toggleTask(task));

  const title = el("button", {
    class: "task-title",
    type: "button",
    text: task.title,
    title: "Click to rename",
    onclick: () => startTitleEdit(task, title),
  });

  const meta = el("div", { class: "task-meta" });

  const status = el(
    "select",
    { class: "inline-select", "aria-label": `Status for "${task.title}"` },
    [
      el("option", { value: "pending", text: "To do" }),
      el("option", { value: "in_progress", text: "In progress" }),
      el("option", { value: "completed", text: "Done" }),
    ]
  );
  status.value = task.status;
  setControlClass(status, "status");
  status.addEventListener("change", () => patchTask(task, { status: status.value }));

  const priority = el(
    "select",
    { class: "inline-select", "aria-label": `Priority for "${task.title}"` },
    [
      el("option", { value: "low", text: "Low" }),
      el("option", { value: "medium", text: "Medium" }),
      el("option", { value: "high", text: "High" }),
    ]
  );
  priority.value = task.priority;
  setControlClass(priority, "priority");
  priority.addEventListener("change", () =>
    patchTask(task, { priority: priority.value })
  );

  const due = el("input", {
    type: "date",
    class: "task-due",
    "aria-label": `Due date for "${task.title}"`,
    title: "Due date",
  });
  due.value = task.due_date || "";
  const dueInfo = dueMeta(task.due_date, task.status);
  due.classList.toggle("is-overdue", dueInfo.overdue);
  due.addEventListener("change", () =>
    patchTask(task, { due_date: due.value || null })
  );

  meta.append(status, priority, due);

  const main = el("div", { class: "task-main" }, [
    el("div", { class: "task-heading" }, [title]),
  ]);
  if (task.description) {
    main.append(el("p", { class: "task-desc", text: task.description }));
  }
  main.append(meta);

  const actions = el("div", { class: "task-actions" }, [
    el("button", {
      class: "icon-btn",
      type: "button",
      text: "⋯",
      "aria-label": `Open details for "${task.title}"`,
      title: "Task details",
      onclick: () => openTaskPanel(task),
    }),
    el("button", {
      class: "icon-btn",
      type: "button",
      text: "×",
      "aria-label": `Delete "${task.title}"`,
      title: "Delete task",
      onclick: () => removeTask(task),
    }),
  ]);

  const row = el(
    "li",
    {
      class: `task${task.status === "completed" ? " is-completed" : ""}`,
      id: `task-${task.id}`,
    },
    [checkbox, main, actions]
  );

  return row;
}

function visibleTasks() {
  if (state.filter === "all") return state.tasks;
  return state.tasks.filter((task) => task.status === state.filter);
}

function renderTasks() {
  renderFilterCounts();
  renderProject();

  clear(taskList);
  const tasks = visibleTasks();

  if (!tasks.length) {
    tasksEmpty.hidden = false;
    tasksEmpty.textContent = state.tasks.length
      ? "No tasks in this view."
      : "No tasks yet. Add your first one above.";
  } else {
    tasksEmpty.hidden = true;
    for (const task of tasks) taskList.append(taskItem(task));
  }
}

async function patchTask(task, body, { toast = "" } = {}) {
  hideError(errorBox);
  try {
    const data = await apiFetch(`/api/tasks/${task.id}`, { method: "PATCH", body });
    Object.assign(task, data.task);
    if (toast) showToast(toast);
    renderTasks();
    return true;
  } catch (error) {
    showError(errorBox, error.message);
    renderTasks();
    return false;
  }
}

async function toggleTask(task) {
  const completing = task.status !== "completed";
  await patchTask(task, { status: completing ? "completed" : "pending" }, {
    toast: completing ? "Task completed" : "Task reopened",
  });
}

function startTitleEdit(task, button) {
  const input = el("input", {
    class: "task-title-input",
    type: "text",
    value: task.title,
    "aria-label": "Task title",
  });
  button.replaceWith(input);
  input.focus();
  input.select();

  let settled = false;

  async function finish(save) {
    if (settled) return;
    settled = true;

    if (!save) {
      renderTasks();
      return;
    }

    const value = input.value.trim();
    if (!value) {
      settled = false;
      input.focus();
      return;
    }
    if (value === task.title) {
      renderTasks();
      return;
    }

    try {
      const data = await apiFetch(`/api/tasks/${task.id}`, {
        method: "PATCH",
        body: { title: value },
      });
      Object.assign(task, data.task);
      showToast("Task renamed");
      renderTasks();
    } catch (error) {
      showError(errorBox, error.message);
      renderTasks();
    }
  }

  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      input.blur();
    } else if (event.key === "Escape") {
      event.preventDefault();
      settled = true;
      renderTasks();
    }
  });
  input.addEventListener("blur", () => finish(true));
}

function openTaskPanel(task) {
  taskPanelForm.reset();
  clearFieldErrors(taskPanelForm);
  hideError(errorBox);

  taskPanelForm.elements.task_id.value = String(task.id);
  taskPanelForm.elements.title.value = task.title;
  taskPanelForm.elements.description.value = task.description || "";
  taskPanelForm.elements.status.value = task.status;
  taskPanelForm.elements.priority.value = task.priority;
  taskPanelForm.elements.due_date.value = task.due_date || "";
  taskPanelTitle.textContent = task.title;

  openDialog(taskPanel, "#task-panel-title-input");
}

async function removeTask(task) {
  const confirmed = await confirmAction({
    title: "Delete task?",
    message: `Delete "${task.title}"? This cannot be undone.`,
    confirmLabel: "Delete task",
  });
  if (!confirmed) return;

  try {
    await apiFetch(`/api/tasks/${task.id}`, { method: "DELETE" });
    showToast("Task deleted");
    state.tasks = state.tasks.filter((item) => item.id !== task.id);
    renderTasks();
  } catch (error) {
    showError(errorBox, error.message);
  }
}

/* --- Events -------------------------------------------------------------- */

taskForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  hideError(errorBox);
  clearFieldErrors(taskForm);

  const body = {
    title: taskForm.elements.title.value,
    priority: taskForm.elements.priority.value,
    due_date: taskForm.elements.due_date.value || null,
  };

  try {
    const data = await apiFetch(`/api/projects/${projectId}/tasks`, {
      method: "POST",
      body,
    });
    state.tasks.push(data.task);
    taskForm.reset();
    renderTasks();
    taskForm.elements.title.focus();
    showToast("Task added");
  } catch (error) {
    if (error instanceof ApiError && Object.keys(error.fields).length) {
      applyFieldErrors(taskForm, error.fields);
    } else {
      showError(errorBox, error.message);
    }
  }
});

document.querySelectorAll("[data-filter]").forEach((button) => {
  button.addEventListener("click", () => {
    state.filter = button.dataset.filter;
    renderTasks();
  });
});

taskPanelForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  hideError(errorBox);
  clearFieldErrors(taskPanelForm);

  const taskId = Number(taskPanelForm.elements.task_id.value);
  const body = {
    title: taskPanelForm.elements.title.value,
    description: taskPanelForm.elements.description.value || null,
    status: taskPanelForm.elements.status.value,
    priority: taskPanelForm.elements.priority.value,
    due_date: taskPanelForm.elements.due_date.value || null,
  };

  try {
    const data = await apiFetch(`/api/tasks/${taskId}`, { method: "PATCH", body });
    const task = state.tasks.find((item) => item.id === taskId);
    if (task) Object.assign(task, data.task);
    taskPanel.close();
    showToast("Task updated");
    renderTasks();
  } catch (error) {
    if (error instanceof ApiError && Object.keys(error.fields).length) {
      applyFieldErrors(taskPanelForm, error.fields);
    } else {
      showError(errorBox, error.message);
    }
  }
});

taskDelete.addEventListener("click", async () => {
  const taskId = Number(taskPanelForm.elements.task_id.value);
  const task = state.tasks.find((item) => item.id === taskId);
  if (!task) return;

  const confirmed = await confirmAction({
    title: "Delete task?",
    message: `Delete "${task.title}"? This cannot be undone.`,
    confirmLabel: "Delete task",
  });
  if (!confirmed) return;

  try {
    await apiFetch(`/api/tasks/${task.id}`, { method: "DELETE" });
    taskPanel.close();
    state.tasks = state.tasks.filter((item) => item.id !== task.id);
    showToast("Task deleted");
    renderTasks();
  } catch (error) {
    showError(errorBox, error.message);
  }
});

/* --- Project edit / delete ---------------------------------------------- */

editBtn.addEventListener("click", () => {
  projectForm.reset();
  clearFieldErrors(projectForm);
  hideError(errorBox);
  projectForm.elements.name.value = state.project.name;
  projectForm.elements.description.value = state.project.description || "";
  projectForm.elements.due_date.value = state.project.due_date || "";
  openDialog(projectDialog, "#project-name");
});

projectForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  hideError(errorBox);
  clearFieldErrors(projectForm);

  const body = {
    name: projectForm.elements.name.value,
    description: projectForm.elements.description.value || null,
    due_date: projectForm.elements.due_date.value || null,
  };

  try {
    const data = await apiFetch(`/api/projects/${projectId}`, {
      method: "PATCH",
      body,
    });
    state.project = data.project;
    projectDialog.close();
    showToast("Project updated");
    renderProject();
  } catch (error) {
    if (error instanceof ApiError && Object.keys(error.fields).length) {
      applyFieldErrors(projectForm, error.fields);
    } else {
      showError(errorBox, error.message);
    }
  }
});

deleteBtn.addEventListener("click", async () => {
  const confirmed = await confirmAction({
    title: "Delete project?",
    message: `Delete "${state.project.name}" and all of its tasks? This cannot be undone.`,
    confirmLabel: "Delete project",
  });
  if (!confirmed) return;

  try {
    await apiFetch(`/api/projects/${projectId}`, { method: "DELETE" });
    window.location.assign("/projects");
  } catch (error) {
    showError(errorBox, error.message);
  }
});

/* --- Boot ---------------------------------------------------------------- */

async function init() {
  if (!Number.isInteger(projectId) || projectId <= 0) {
    showNotFound();
    return;
  }

  try {
    const data = await apiFetch(`/api/projects/${projectId}`);
    state.project = data.project;
    state.tasks = data.project.tasks || [];
    content.hidden = false;
    notFound.hidden = true;
    renderProject();
    renderTasks();
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      showNotFound();
      return;
    }
    showError(errorBox, error.message);
  }
}

function showNotFound() {
  content.hidden = true;
  notFound.hidden = false;
}

init();
