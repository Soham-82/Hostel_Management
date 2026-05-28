const currentPath = window.location.pathname;

document.querySelectorAll(".nav a").forEach((link) => {
  const linkPath = new URL(link.href).pathname;
  if (linkPath === currentPath || (linkPath !== "/" && currentPath.startsWith(linkPath))) {
    link.classList.add("active");
  }
});

document.querySelectorAll("form").forEach((form) => {
  form.addEventListener("submit", () => {
    const button = form.querySelector("button[type='submit']");
    if (button) {
      button.disabled = true;
      button.dataset.originalText = button.textContent;
      button.textContent = "Saving...";
    }
  });
});
