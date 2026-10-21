/** Renders the top navigation bar: routes, theme toggle and log-out. */

import { apiFetch } from "./api.js";
import { el } from "./ui.js";

async function currentUser() {
  try {
    const data = await apiFetch("/api/auth/me", { redirectOn401: false });
    return data.user;
  } catch {
    return null;
  }
}

function navLink(href, label, active) {
  return el("a", {
    class: "nav-link",
    href,
    text: label,
    ...(active ? { "aria-current": "page" } : {}),
  });
}

function themeToggle() {
  const isDark = document.documentElement.dataset.theme === "dark";
  return el(
    "button",
    {
      class: "icon-btn",
      type: "button",
      "data-theme-toggle": "",
      "aria-label": isDark ? "Switch to light mode" : "Switch to dark mode",
      title: isDark ? "Light mode" : "Dark mode",
    },
    [el("span", { class: "theme-icon", "aria-hidden": "true", text: isDark ? "☀" : "☾" })]
  );
}

export async function renderNav() {
  const host = document.getElementById("app-nav");
  if (!host) return;

  const path = window.location.pathname;
  const onDashboard = path === "/" || path.startsWith("/dashboard");

  host.replaceChildren();
  host.append(
    el("a", { class: "brand", href: "/" }, [
      el("span", { class: "brand-mark", "aria-hidden": "true", text: "✓" }),
      "TrackIt",
    ]),
    el("nav", { class: "nav-links", "aria-label": "Primary" }, [
      navLink("/", "Dashboard", onDashboard),
      navLink("/projects", "Projects", path.startsWith("/projects")),
    ])
  );

  const user = await currentUser();
  if (!user) return;

  const logout = el("button", {
    class: "btn btn-ghost btn-sm",
    type: "button",
    text: "Log out",
    onclick: async () => {
      try {
        await apiFetch("/api/auth/logout", { method: "POST" });
      } finally {
        window.location.assign("/login");
      }
    },
  });

  host.append(
    el("div", { class: "nav-right" }, [
      themeToggle(),
      el("span", { class: "nav-email", text: user.email, title: user.email }),
      logout,
    ])
  );
}
