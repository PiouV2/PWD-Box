const terminalOutput = document.getElementById("terminal-output");
const sectionLinks = [...document.querySelectorAll(".nav-link[data-target]")];

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

typeTerminalPreview();
registerActiveNavObserver();
