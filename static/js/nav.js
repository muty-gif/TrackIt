/** Renders the top navigation bar, including the log-out control. */

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

export async function renderNav() {
  const host = document.getElementById("app-nav");
  if (!host) return;

  host.replaceChildren();
  host.append(el("a", { class: "brand", href: "/projects", text: "TrackIt" }));

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
      el("span", { class: "muted", text: user.email }),
      logout,
    ])
  );
}
