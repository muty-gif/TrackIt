/**
 * Thin fetch wrapper for the TrackIt JSON API.
 *
 * - Always talks JSON in and JSON out.
 * - Turns error responses into ApiError instances carrying `fields` for
 *   per-field validation feedback.
 * - Redirects to the login page when a protected request returns 401.
 */

export class ApiError extends Error {
  constructor(message, { status = 0, code = "error", fields = {} } = {}) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.fields = fields;
  }
}

export async function apiFetch(path, { method = "GET", body, redirectOn401 = true } = {}) {
  const options = { method, headers: { Accept: "application/json" } };

  if (body !== undefined) {
    options.headers["Content-Type"] = "application/json";
    options.body = JSON.stringify(body);
  }

  let response;
  try {
    response = await fetch(path, options);
  } catch {
    throw new ApiError("Network error. Please check your connection.", { status: 0 });
  }

  if (response.status === 401 && redirectOn401) {
    const next = encodeURIComponent(window.location.pathname);
    window.location.assign(`/login?next=${next}`);
    throw new ApiError("Your session has expired. Please log in again.", { status: 401 });
  }

  const text = await response.text();
  let data = null;
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = null;
    }
  }

  if (!response.ok) {
    const error = (data && data.error) || {};
    throw new ApiError(error.message || `Request failed (${response.status}).`, {
      status: response.status,
      code: error.code || "error",
      fields: error.fields || {},
    });
  }

  return data;
}
