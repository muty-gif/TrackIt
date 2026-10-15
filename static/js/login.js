import { ApiError, apiFetch } from "./api.js";
import { applyFieldErrors, clearFieldErrors, hideError, showError } from "./ui.js";

const form = document.getElementById("login-form");
const errorBox = document.getElementById("form-error");

function safeNext() {
  const next = new URLSearchParams(window.location.search).get("next");
  // Only allow same-site, absolute paths.
  if (next && next.startsWith("/") && !next.startsWith("//")) return next;
  return "/projects";
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  hideError(errorBox);
  clearFieldErrors(form);

  const values = Object.fromEntries(new FormData(form).entries());

  try {
    await apiFetch("/api/auth/login", {
      method: "POST",
      body: { email: values.email, password: values.password },
      redirectOn401: false, // show the error on this page instead of redirecting
    });
    window.location.assign(safeNext());
  } catch (error) {
    if (error instanceof ApiError && Object.keys(error.fields).length) {
      applyFieldErrors(form, error.fields);
    } else {
      showError(errorBox, error.message);
    }
  }
});
