/** Small DOM helpers shared by the front-end modules. */

/** Create an element. `props` supports class, text, dataset, on* handlers and attributes. */
export function el(tag, props = {}, children = []) {
  const node = document.createElement(tag);

  for (const [key, value] of Object.entries(props)) {
    if (value === undefined || value === null) continue;
    if (key === "class") {
      node.className = value;
    } else if (key === "text") {
      node.textContent = value;
    } else if (key === "dataset") {
      Object.assign(node.dataset, value);
    } else if (key.startsWith("on") && typeof value === "function") {
      node.addEventListener(key.slice(2).toLowerCase(), value);
    } else {
      node.setAttribute(key, value);
    }
  }

  for (const child of [].concat(children)) {
    if (child === undefined || child === null || child === false) continue;
    node.append(child.nodeType ? child : document.createTextNode(String(child)));
  }

  return node;
}

/** Remove every child of a node. */
export function clear(node) {
  while (node.firstChild) node.removeChild(node.firstChild);
}

export function showError(container, message) {
  container.textContent = message;
  container.hidden = false;
}

export function hideError(container) {
  container.textContent = "";
  container.hidden = true;
}

export function clearFieldErrors(form) {
  form.querySelectorAll(".field-error").forEach((node) => {
    node.textContent = "";
    node.hidden = true;
  });
  form.querySelectorAll(".invalid").forEach((node) => node.classList.remove("invalid"));
}

/** Paint server-side validation messages (our 422 field errors) onto the form. */
export function applyFieldErrors(form, fields) {
  clearFieldErrors(form);
  let firstInvalid = null;

  for (const [name, message] of Object.entries(fields)) {
    const errorNode = form.querySelector(`[data-error-for="${name}"]`);
    if (errorNode) {
      errorNode.textContent = message;
      errorNode.hidden = false;
    }
    const input = form.elements[name];
    if (input) {
      input.classList.add("invalid");
      if (!firstInvalid) firstInvalid = input;
    }
  }

  if (firstInvalid) firstInvalid.focus();
}
