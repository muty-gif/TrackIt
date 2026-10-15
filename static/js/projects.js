import { ApiError, apiFetch } from "./api.js";
import { renderNav } from "./nav.js";
import { applyFieldErrors, clear, clearFieldErrors, el, hideError, showError } from "./ui.js";

const listEl = document.getElementById("project-list");
const emptyEl = document.getElementById("projects-empty");
const errorBox = document.getElementById("global-error");
const form = document.getElementById("project-form");
const newBtn = document.getElementById("new-project-btn");
const cancelBtn = document.getElementById("cancel-project-btn");

renderNav();

function openForm() {
  clearFieldErrors(form);
  hideError(errorBox);
  form.reset();
  form.hidden = false;
  form.elements.name.focus();
}

function closeForm() {
  form.hidden = true;
  clearFieldErrors(form);
}

newBtn.addEventListener("click", openForm);
cancelBtn.addEventListener("click", closeForm);

function projectCard(project) {
  const header = el("div", { class: "card-head" }, [
    el("a", {
      class: "card-title",
      href: `/projects/${project.id}`,
      text: project.name,
    }),
    el("button", {
      class: "btn btn-danger-text btn-sm",
      type: "button",
      text: "Delete",
      onclick: () => removeProject(project),
    }),
  ]);

  const children = [header];
  if (project.description) {
    children.push(el("p", { class: "card-desc", text: project.description }));
  }
  children.push(
    el("p", {
      class: "card-meta muted",
      text: `${project.completed_task_count} of ${project.task_count} tasks completed`,
    })
  );

  return el("li", { class: "card" }, children);
}

function renderProjects(projects) {
  clear(listEl);
  emptyEl.hidden = projects.length > 0;
  for (const project of projects) listEl.append(projectCard(project));
}

async function loadProjects() {
  try {
    const data = await apiFetch("/api/projects");
    renderProjects(data.projects);
  } catch (error) {
    showError(errorBox, error.message);
  }
}

async function removeProject(project) {
  const confirmed = window.confirm(
    `Delete "${project.name}" and all of its tasks? This cannot be undone.`
  );
  if (!confirmed) return;

  try {
    await apiFetch(`/api/projects/${project.id}`, { method: "DELETE" });
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

  try {
    await apiFetch("/api/projects", {
      method: "POST",
      body: {
        name: values.name,
        description: values.description ? values.description : null,
      },
    });
    closeForm();
    await loadProjects();
  } catch (error) {
    if (error instanceof ApiError && Object.keys(error.fields).length) {
      applyFieldErrors(form, error.fields);
    } else {
      showError(errorBox, error.message);
    }
  }
});

loadProjects();
