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

const grid = document.getElementById("project-grid");
const empty = document.getElementById("projects-empty");
const errorBox = document.getElementById("global-error");
const dialog = document.getElementById("project-dialog");
const form = document.getElementById("project-form");
const submit = document.getElementById("project-submit");
const kicker = document.getElementById("project-dialog-kicker");
const dialogTitle = document.getElementById("project-dialog-title");

let projects = [];

renderNav();
setupDialog(dialog);
setupDialog(document.getElementById("confirm-dialog"));

function projectState(project) {
  const total = project.task_count || 0;
  const done = project.completed_task_count || 0;
  if (!total) return { label: "Not started", className: "badge-pending" };
  if (done === total) return { label: "Done", className: "badge-completed" };
  const due = dueMeta(project.due_date);
  if (due.overdue) return { label: "Overdue", className: "badge-danger" };
  if (done > 0) return { label: "In progress", className: "badge-in_progress" };
  if (project.due_date) {
    return { label: "Due soon", className: "badge-warning" };
  }
  return { label: "To do", className: "badge-pending" };
}

function renderProjectCard(project) {
  const total = project.task_count || 0;
  const done = project.completed_task_count || 0;
  const percent = total ? Math.round((done / total) * 100) : 0;
  const state = projectState(project);
  const due = dueMeta(project.due_date);

  const head = el("div", { class: "project-card-head" }, [
    el("a", {
      class: "project-card-title",
      href: `/projects/${project.id}`,
      text: project.name,
    }),
    el("div", { class: "project-card-actions" }, [
      el("button", {
        class: "icon-btn",
        type: "button",
        text: "✎",
        "aria-label": `Edit ${project.name}`,
        title: "Edit project",
        onclick: () => openEdit(project),
      }),
      el("button", {
        class: "icon-btn",
        type: "button",
        text: "×",
        "aria-label": `Delete ${project.name}`,
        title: "Delete project",
        onclick: () => removeProject(project),
      }),
    ]),
  ]);

  const card = el("article", { class: "project-card" }, [head]);

  if (project.description) {
    card.append(el("p", { class: "project-card-desc", text: project.description }));
  }

  card.append(
    el("div", { class: "project-card-meta" }, [
      el("span", { class: `badge ${state.className}`, text: state.label }),
      project.due_date
        ? el("span", {
            class: `meta-item${due.overdue ? " is-overdue" : ""}`,
            text: due.text,
          })
        : el("span", { class: "meta-item", text: "No due date" }),
    ])
  );

  const bar = el(
    "div",
    {
      class: `progress${percent === 100 && total ? " is-complete" : ""}`,
      role: "progressbar",
      "aria-label": `${project.name} completion`,
      "aria-valuemin": "0",
      "aria-valuemax": "100",
      "aria-valuenow": String(percent),
    },
    [el("span", { class: "progress-fill" })]
  );
  bar.firstChild.style.width = `${percent}%`;

  card.append(
    el("div", { class: "project-card-progress" }, [
      bar,
      el("div", { class: "project-card-progress-label" }, [
        el("span", { text: `${done} of ${total} tasks completed` }),
        el("span", { text: `${percent}%` }),
      ]),
    ])
  );

  return card;
}

function renderProjects() {
  clear(grid);
  empty.hidden = projects.length > 0;
  for (const project of projects) grid.append(renderProjectCard(project));
}

async function loadProjects() {
  hideError(errorBox);
  try {
    const data = await apiFetch("/api/projects");
    projects = data.projects;
    renderProjects();
  } catch (error) {
    showError(errorBox, error.message);
  }
}

function resetForm() {
  form.reset();
  form.elements.project_id.value = "";
  clearFieldErrors(form);
  hideError(errorBox);
}

function openCreate() {
  resetForm();
  kicker.textContent = "New project";
  dialogTitle.textContent = "Create project";
  submit.textContent = "Create project";
  openDialog(dialog, "#name");
}

function openEdit(project) {
  resetForm();
  form.elements.project_id.value = String(project.id);
  form.elements.name.value = project.name;
  form.elements.description.value = project.description || "";
  form.elements.due_date.value = project.due_date || "";
  kicker.textContent = "Project";
  dialogTitle.textContent = "Edit project";
  submit.textContent = "Save changes";
  openDialog(dialog, "#name");
}

async function removeProject(project) {
  const confirmed = await confirmAction({
    title: "Delete project?",
    message: `Delete "${project.name}" and all of its tasks? This cannot be undone.`,
    confirmLabel: "Delete project",
  });
  if (!confirmed) return;

  try {
    await apiFetch(`/api/projects/${project.id}`, { method: "DELETE" });
    showToast("Project deleted");
    await loadProjects();
  } catch (error) {
    showError(errorBox, error.message);
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  hideError(errorBox);
  clearFieldErrors(form);

  const values = Object.fromEntries(new FormData(form).entries());
  const projectId = values.project_id;
  const body = {
    name: values.name,
    description: values.description || null,
    due_date: values.due_date || null,
  };

  try {
    await apiFetch(projectId ? `/api/projects/${projectId}` : "/api/projects", {
      method: projectId ? "PATCH" : "POST",
      body,
    });
    dialog.close();
    showToast(projectId ? "Project updated" : "Project created");
    await loadProjects();
  } catch (error) {
    if (error instanceof ApiError && Object.keys(error.fields).length) {
      applyFieldErrors(form, error.fields);
    } else {
      showError(errorBox, error.message);
    }
  }
});

document.getElementById("new-project-btn").addEventListener("click", openCreate);
document.querySelectorAll("[data-new-project]").forEach((button) => {
  button.addEventListener("click", openCreate);
});

loadProjects();
