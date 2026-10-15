import { ApiError, apiFetch } from "./api.js";
import { renderNav } from "./nav.js";
import { applyFieldErrors, clear, clearFieldErrors, el, hideError, showError } from "./ui.js";

const projectId = Number(window.location.pathname.split("/").filter(Boolean).pop());

const state = { project: null, tasks: [], editingTaskId: null };

const errorBox = document.getElementById("global-error");
const notFound = document.getElementById("not-found");
const content = document.getElementById("project-content");

const titleEl = document.getElementById("project-title");
const descEl = document.getElementById("project-description");
const metaEl = document.getElementById("project-meta");

const editBtn = document.getElementById("edit-project-btn");
const deleteBtn = document.getElementById("delete-project-btn");
const projectForm = document.getElementById("project-edit-form");
const cancelProjectEdit = document.getElementById("cancel-project-edit");

const taskList = document.getElementById("task-list");
const tasksEmpty = document.getElementById("tasks-empty");
const newTaskBtn = document.getElementById("new-task-btn");
const taskForm = document.getElementById("task-form");
const taskSubmit = document.getElementById("task-submit");
const cancelTaskForm = document.getElementById("cancel-task-form");

function showNotFound() {
  content.hidden = true;
  notFound.hidden = false;
}

/* --- Project ------------------------------------------------------------- */

function renderProjectHeader() {
  titleEl.textContent = state.project.name;
  if (state.project.description) {
    descEl.textContent = state.project.description;
    descEl.hidden = false;
  } else {
    descEl.textContent = "";
    descEl.hidden = true;
  }
  document.title = `${state.project.name} · TrackIt`;
}

function renderMeta() {
  const total = state.tasks.length;
  const done = state.tasks.filter((task) => task.status === "completed").length;
  metaEl.textContent = total ? `${done} of ${total} tasks completed` : "";
}

/* --- Tasks --------------------------------------------------------------- */

function renderTasks() {
  clear(taskList);
  tasksEmpty.hidden = state.tasks.length > 0;
  for (const task of state.tasks) taskList.append(taskItem(task));
  renderMeta();
}

function taskItem(task) {
  const checkbox = el("input", {
    type: "checkbox",
    class: "task-check",
    "aria-label": `Mark "${task.title}" as completed`,
  });
  checkbox.checked = task.status === "completed";
  checkbox.addEventListener("change", () => toggleTask(task, checkbox));

  const title = el("span", { class: "task-title", text: task.title });
  if (task.status === "completed") title.classList.add("done");

  const main = el("div", { class: "task-main" }, [
    el("div", { class: "task-heading" }, [checkbox, title]),
  ]);
  if (task.description) {
    main.append(el("p", { class: "task-desc", text: task.description }));
  }

  const actions = el("div", { class: "task-actions" }, [
    el("button", {
      class: "btn btn-ghost btn-sm",
      type: "button",
      text: "Edit",
      onclick: () => startEditTask(task),
    }),
    el("button", {
      class: "btn btn-danger-text btn-sm",
      type: "button",
      text: "Delete",
      onclick: () => removeTask(task),
    }),
  ]);

  return el("li", { class: "task" }, [main, actions]);
}

async function loadTasks() {
  const data = await apiFetch(`/api/projects/${projectId}/tasks`);
  state.tasks = data.tasks;
  renderTasks();
}

async function toggleTask(task, checkbox) {
  const status = checkbox.checked ? "completed" : "pending";
  try {
    const data = await apiFetch(`/api/tasks/${task.id}`, {
      method: "PATCH",
      body: { status },
    });
    Object.assign(task, data.task);
    renderTasks();
  } catch (error) {
    checkbox.checked = !checkbox.checked; // roll back the optimistic toggle
    showError(errorBox, error.message);
  }
}

function resetTaskForm() {
  state.editingTaskId = null;
  taskForm.reset();
  taskSubmit.textContent = "Add task";
  cancelTaskForm.hidden = true;
  clearFieldErrors(taskForm);
}

function openTaskForm() {
  resetTaskForm();
  hideError(errorBox);
  taskForm.hidden = false;
  taskForm.elements.title.focus();
}

function startEditTask(task) {
  state.editingTaskId = task.id;
  taskForm.elements.title.value = task.title;
  taskForm.elements.description.value = task.description || "";
  taskSubmit.textContent = "Save task";
  cancelTaskForm.hidden = false;
  taskForm.hidden = false;
  clearFieldErrors(taskForm);
  hideError(errorBox);
  taskForm.elements.title.focus();
}

newTaskBtn.addEventListener("click", openTaskForm);
cancelTaskForm.addEventListener("click", () => {
  resetTaskForm();
  taskForm.hidden = true;
});

taskForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  hideError(errorBox);
  clearFieldErrors(taskForm);

  const body = {
    title: taskForm.elements.title.value,
    description: taskForm.elements.description.value || null,
  };

  try {
    if (state.editingTaskId) {
      await apiFetch(`/api/tasks/${state.editingTaskId}`, { method: "PATCH", body });
    } else {
      await apiFetch(`/api/projects/${projectId}/tasks`, { method: "POST", body });
    }
    resetTaskForm();
    taskForm.hidden = true;
    await loadTasks();
  } catch (error) {
    if (error instanceof ApiError && Object.keys(error.fields).length) {
      applyFieldErrors(taskForm, error.fields);
    } else {
      showError(errorBox, error.message);
    }
  }
});

async function removeTask(task) {
  if (!window.confirm(`Delete task "${task.title}"?`)) return;
  try {
    await apiFetch(`/api/tasks/${task.id}`, { method: "DELETE" });
    if (state.editingTaskId === task.id) {
      resetTaskForm();
      taskForm.hidden = true;
    }
    await loadTasks();
  } catch (error) {
    showError(errorBox, error.message);
  }
}

/* --- Project edit / delete ---------------------------------------------- */

editBtn.addEventListener("click", () => {
  projectForm.elements.name.value = state.project.name;
  projectForm.elements.description.value = state.project.description || "";
  clearFieldErrors(projectForm);
  hideError(errorBox);
  projectForm.hidden = false;
  projectForm.elements.name.focus();
});

cancelProjectEdit.addEventListener("click", () => {
  projectForm.hidden = true;
  clearFieldErrors(projectForm);
});

projectForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  hideError(errorBox);
  clearFieldErrors(projectForm);

  const body = {
    name: projectForm.elements.name.value,
    description: projectForm.elements.description.value || null,
  };

  try {
    const data = await apiFetch(`/api/projects/${projectId}`, {
      method: "PATCH",
      body,
    });
    state.project = data.project;
    renderProjectHeader();
    projectForm.hidden = true;
  } catch (error) {
    if (error instanceof ApiError && Object.keys(error.fields).length) {
      applyFieldErrors(projectForm, error.fields);
    } else {
      showError(errorBox, error.message);
    }
  }
});

deleteBtn.addEventListener("click", async () => {
  const confirmed = window.confirm(
    `Delete "${state.project.name}" and all of its tasks? This cannot be undone.`
  );
  if (!confirmed) return;

  try {
    await apiFetch(`/api/projects/${projectId}`, { method: "DELETE" });
    window.location.assign("/projects");
  } catch (error) {
    showError(errorBox, error.message);
  }
});

/* --- Boot ----------------------------------------------------------------- */

async function init() {
  renderNav();

  if (!Number.isInteger(projectId) || projectId <= 0) {
    showNotFound();
    return;
  }

  try {
    const data = await apiFetch(`/api/projects/${projectId}`);
    state.project = data.project;
    renderProjectHeader();
    content.hidden = false;
    notFound.hidden = true;
    await loadTasks();
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      showNotFound();
      return;
    }
    showError(errorBox, error.message);
  }
}

init();
