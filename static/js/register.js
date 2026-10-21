import { ApiError, apiFetch } from "./api.js";
import { applyFieldErrors, clearFieldErrors, hideError, showError } from "./ui.js";

const form = document.getElementById("register-form");
const errorBox = document.getElementById("form-error");

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  hideError(errorBox);
  clearFieldErrors(form);

  const values = Object.fromEntries(new FormData(form).entries());

  if (values.password !== values.confirm_password) {
    applyFieldErrors(form, { confirm_password: "Passwords do not match." });
    return;
  }

  try {
    await apiFetch("/api/auth/register", {
      method: "POST",
      body: { email: values.email, password: values.password },
      redirectOn401: false,
    });
    window.location.assign("/");
  } catch (error) {
    if (error instanceof ApiError && Object.keys(error.fields).length) {
      applyFieldErrors(form, error.fields);
    } else {
      showError(errorBox, error.message);
    }
  }
});
