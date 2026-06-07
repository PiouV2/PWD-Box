const terminalOutput = document.getElementById("terminal-output");
const sectionLinks = [...document.querySelectorAll(".nav-link[data-target]")];
const themeToggle = document.getElementById("theme-toggle");

const terminalLines = [
  "$ sudo ./start-monitoring --interface wlan1",
  "> passive scanning enabled",
  "> deauth attack detection active",
  "> data logging to /logs/pwd-box.log"
];

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function typeTerminalPreview() {
  if (!terminalOutput) {
    return;
  }

  terminalOutput.textContent = "";

  for (const line of terminalLines) {
    for (const character of line) {
      terminalOutput.textContent += character;
      await sleep(16);
    }

    terminalOutput.textContent += "\n";
    await sleep(220);
  }

  terminalOutput.innerHTML += '<span class="cursor">|</span>';
}

function setActiveLink(targetId) {
  sectionLinks.forEach((link) => {
    const isActive = link.dataset.target === targetId;
    link.classList.toggle("active", isActive);
  });
}

function registerActiveNavObserver() {
  const observedSections = ["home", "features", "documentation"]
    .map((id) => document.getElementById(id))
    .filter(Boolean);

  if (!observedSections.length) {
    return;
  }

  const observer = new IntersectionObserver(
    (entries) => {
      entries
        .filter((entry) => entry.isIntersecting)
        .sort((a, b) => b.intersectionRatio - a.intersectionRatio)
        .forEach((entry) => setActiveLink(entry.target.id));
    },
    {
      rootMargin: "-30% 0px -55% 0px",
      threshold: [0.3, 0.6]
    }
  );

  observedSections.forEach((section) => observer.observe(section));
}

function applyTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme);

  if (themeToggle) {
    themeToggle.textContent = theme === "dark" ? "Light Mode" : "Dark Mode";
  }
}

function initializeThemeToggle() {
  const storedTheme = localStorage.getItem("pwd-box-theme");
  const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  const initialTheme = storedTheme || (prefersDark ? "dark" : "light");

  applyTheme(initialTheme);

  if (!themeToggle) {
    return;
  }

  themeToggle.addEventListener("click", () => {
    const currentTheme = document.documentElement.getAttribute("data-theme") || "light";
    const nextTheme = currentTheme === "dark" ? "light" : "dark";
    applyTheme(nextTheme);
    localStorage.setItem("pwd-box-theme", nextTheme);
  });
}

initializeThemeToggle();
typeTerminalPreview();
registerActiveNavObserver();
