import { apiFetch } from "./api.js";
import { renderNav } from "./nav.js";
import {
  clear,
  dueMeta,
  el,
  formatDate,
  hideError,
  relativeTime,
  showError,
  statusLabel,
} from "./ui.js";

const errorBox = document.getElementById("global-error");
const metricGrid = document.getElementById("metric-grid");
const statusChart = document.getElementById("status-chart");
const projectProgress = document.getElementById("project-progress");
const upcomingList = document.getElementById("upcoming-list");
const recentList = document.getElementById("recent-list");
const subtitle = document.getElementById("dashboard-subtitle");

const METRICS = [
  { key: "project_count", label: "Projects", hint: "Workspaces you own" },
  { key: "open_task_count", label: "Open tasks", hint: "Still in flight" },
  {
    key: "completed_this_week",
    label: "Done this week",
    hint: "Momentum since Monday",
    tone: "success",
  },
  {
    key: "overdue_task_count",
    label: "Overdue",
    hint: "Need attention",
    tone: "danger",
  },
  {
    key: "due_today_count",
    label: "Due today",
    hint: "On your plate",
    tone: "warning",
  },
];

const STATUSES = [
  { key: "pending", label: "To do", color: "var(--muted)" },
  { key: "in_progress", label: "In progress", color: "var(--info)" },
  { key: "completed", label: "Done", color: "var(--success)" },
];

function renderMetrics(metrics) {
  clear(metricGrid);
  for (const metric of METRICS) {
    metricGrid.append(
      el("article", { class: `metric-card${metric.tone ? ` tone-${metric.tone}` : ""}` }, [
        el("p", { class: "metric-label", text: metric.label }),
        el("p", { class: "metric-value", text: metrics[metric.key] ?? 0 }),
        el("p", { class: "metric-hint", text: metric.hint }),
      ])
    );
  }
}

function renderStatusChart(counts) {
  clear(statusChart);
  const total = STATUSES.reduce((sum, item) => sum + (counts[item.key] || 0), 0);
  const donut = el("div", {
    class: "donut",
    role: "img",
    "aria-label": total
      ? `Task breakdown: ${STATUSES.map(
          (item) => `${counts[item.key] || 0} ${item.label}`
        ).join(", ")}`
      : "No tasks yet",
  });

  if (total > 0) {
    let offset = 0;
    const stops = STATUSES.map((item) => {
      const start = offset;
      const size = ((counts[item.key] || 0) / total) * 100;
      offset += size;
      return `${item.color} ${start}% ${offset}%`;
    });
    donut.style.background = `conic-gradient(${stops.join(", ")})`;
  }

  donut.append(
    el("div", { class: "donut-center" }, [
      el("span", { class: "donut-total", text: total }),
      el("span", { class: "donut-caption", text: total === 1 ? "task" : "tasks" }),
    ])
  );

  const legend = el("ul", { class: "legend" });
  for (const item of STATUSES) {
    const dot = el("span", { class: "legend-dot", "aria-hidden": "true" });
    dot.style.background = item.color;
    legend.append(
      el("li", { class: "legend-item" }, [
        dot,
        el("span", { text: item.label }),
        el("span", { class: "legend-count", text: counts[item.key] || 0 }),
      ])
    );
  }

  statusChart.append(donut, legend);
}

function renderProjectProgress(projects) {
  clear(projectProgress);
  if (!projects.length) {
    projectProgress.append(
      el("p", { class: "quick-empty", text: "Create a project to see its progress here." })
    );
    return;
  }

  for (const project of projects) {
    const total = project.task_count || 0;
    const done = project.completed_task_count || 0;
    const percent = total ? Math.round((done / total) * 100) : 0;

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

    projectProgress.append(
      el("div", { class: "progress-item" }, [
        el("div", { class: "progress-item-head" }, [
          el("a", {
            class: "progress-item-name",
            href: `/projects/${project.id}`,
            text: project.name,
          }),
          el("span", {
            class: "progress-item-meta",
            text: `${done}/${total} · ${percent}%`,
          }),
        ]),
        bar,
      ])
    );
  }
}

function renderUpcoming(tasks) {
  clear(upcomingList);
  if (!tasks.length) {
    upcomingList.append(
      el("li", {
        class: "quick-empty",
        text: "Nothing due yet. Add a due date to a task to see it here.",
      })
    );
    return;
  }

  for (const task of tasks) {
    const due = dueMeta(task.due_date, task.status);
    upcomingList.append(
      el("li", {}, [
        el("a", { class: "quick-item", href: `/projects/${task.project_id}` }, [
          el("span", { class: "quick-icon", "aria-hidden": "true", text: "T" }),
          el("span", { class: "quick-body" }, [
            el("span", { class: "quick-title", text: task.title }),
            el("span", {
              class: "quick-sub",
              text: `${task.project_name} · ${statusLabel(task.status)}`,
            }),
          ]),
          el("span", {
            class: `quick-date${due.overdue ? " is-overdue" : ""}`,
            text: due.text,
          }),
        ]),
      ])
    );
  }
}

function renderRecent(items) {
  clear(recentList);
  if (!items.length) {
    recentList.append(
      el("li", { class: "quick-empty", text: "Your recent work will show up here." })
    );
    return;
  }

  for (const item of items) {
    const isProject = item.kind === "project";
    const meta = isProject
      ? `Project${item.due_date ? ` · due ${formatDate(item.due_date)}` : ""}`
      : `${item.project_name} · ${statusLabel(item.status)}`;

    recentList.append(
      el("li", {}, [
        el(
          "a",
          {
            class: "quick-item",
            href: isProject ? `/projects/${item.project_id}` : `/projects/${item.project_id}`,
          },
          [
            el("span", {
              class: `quick-icon${isProject ? "" : " is-task"}`,
              "aria-hidden": "true",
              text: isProject ? "P" : "T",
            }),
            el("span", { class: "quick-body" }, [
              el("span", { class: "quick-title", text: item.title }),
              el("span", { class: "quick-sub", text: meta }),
            ]),
            el("span", { class: "quick-date", text: relativeTime(item.updated_at) }),
          ]
        ),
      ])
    );
  }
}

async function loadDashboard() {
  hideError(errorBox);
  try {
    const data = await apiFetch("/api/dashboard");
    renderMetrics(data.metrics);
    renderStatusChart(data.status_counts);
    renderProjectProgress(data.projects);
    renderUpcoming(data.upcoming);
    renderRecent(data.recent);
  } catch (error) {
    showError(errorBox, error.message);
  }
}

subtitle.textContent = `${new Intl.DateTimeFormat(undefined, {
  weekday: "long",
  month: "long",
  day: "numeric",
}).format(new Date())} · Here is what needs your attention.`;

renderNav();
loadDashboard();
