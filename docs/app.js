const STORAGE_KEY = "unimail-pages-data";
const APP_VERSION = "1.1.0";

const defaultData = {
  subscribers: [],
  campaigns: [],
};

let state = load();

function load() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return structuredClone(defaultData);
    const parsed = JSON.parse(raw);
    return {
      subscribers: Array.isArray(parsed.subscribers) ? parsed.subscribers : [],
      campaigns: Array.isArray(parsed.campaigns) ? parsed.campaigns : [],
    };
  } catch {
    return structuredClone(defaultData);
  }
}

function save() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  } catch {
    setNotice("Could not save data in browser storage.");
  }
}

function uid() {
  return `${Date.now()}-${Math.floor(Math.random() * 1_000_000)}`;
}

function setNotice(msg) {
  document.getElementById("notice").textContent = msg;
}

function seedDemoData() {
  const timestamp = Date.now();
  state = {
    subscribers: [
      {
        id: `${timestamp}-1`,
        name: "Ada Lovelace",
        email: "ada@university.edu",
        department: "Computer Science",
        isActive: true,
      },
      {
        id: `${timestamp}-2`,
        name: "Grace Hopper",
        email: "grace@university.edu",
        department: "Engineering",
        isActive: true,
      },
      {
        id: `${timestamp}-3`,
        name: "Alan Turing",
        email: "alan@university.edu",
        department: "Mathematics",
        isActive: true,
      },
    ],
    campaigns: [
      {
        id: `${timestamp}-4`,
        name: "Spring Career Fair",
        subject: "Career Fair Registration Open",
        body: "Join us for the annual spring career fair.",
        status: "sent",
        sentCount: 3,
        openedCount: 2,
      },
      {
        id: `${timestamp}-5`,
        name: "Hackathon 2026",
        subject: "Hackathon Kickoff",
        body: "Registration is now live.",
        status: "draft",
        sentCount: 0,
        openedCount: 0,
      },
    ],
  };
  save();
  render();
  setNotice("Demo data loaded.");
}

function clearData() {
  state = structuredClone(defaultData);
  save();
  render();
  setNotice("All local data cleared.");
}

function render() {
  const totalSubscribers = state.subscribers.length;
  const activeSubscribers = state.subscribers.filter((s) => s.isActive).length;
  const totalCampaigns = state.campaigns.length;
  const sentCampaigns = state.campaigns.filter((c) => c.status === "sent");
  const totalSent = sentCampaigns.reduce((n, c) => n + c.sentCount, 0);
  const totalOpened = sentCampaigns.reduce((n, c) => n + c.openedCount, 0);
  const openRate = totalSent ? ((totalOpened / totalSent) * 100).toFixed(1) : "0.0";

  document.getElementById("totalSubscribers").textContent = String(totalSubscribers);
  document.getElementById("activeSubscribers").textContent = String(activeSubscribers);
  document.getElementById("totalCampaigns").textContent = String(totalCampaigns);
  document.getElementById("openRate").textContent = `${openRate}%`;

  const subscriberList = document.getElementById("subscriberList");
  subscriberList.innerHTML = "";
  if (!state.subscribers.length) {
    subscriberList.innerHTML = "<li>No subscribers yet.</li>";
  } else {
    for (const sub of state.subscribers) {
      const li = document.createElement("li");
      li.innerHTML = `
        <strong>${escapeHtml(sub.name)}</strong>
        <div class="meta">${escapeHtml(sub.email)} • ${escapeHtml(sub.department || "No department")}</div>
      `;
      subscriberList.appendChild(li);
    }
  }

  const campaignList = document.getElementById("campaignList");
  campaignList.innerHTML = "";
  if (!state.campaigns.length) {
    campaignList.innerHTML = "<li>No campaigns yet.</li>";
  } else {
    for (const campaign of state.campaigns) {
      const li = document.createElement("li");
      const isDraft = campaign.status === "draft";
      li.innerHTML = `
        <strong>${escapeHtml(campaign.name)}</strong>
        <span class="pill ${isDraft ? "draft" : "sent"}">${escapeHtml(campaign.status)}</span>
        <div class="meta">${escapeHtml(campaign.subject)}</div>
        <div class="meta">Sent: ${campaign.sentCount} • Opened: ${campaign.openedCount}</div>
      `;

      if (isDraft) {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.textContent = "Send Campaign";
        btn.addEventListener("click", () => sendCampaign(campaign.id));
        li.appendChild(btn);
      }

      campaignList.appendChild(li);
    }
  }
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function sendCampaign(id) {
  const campaign = state.campaigns.find((c) => c.id === id);
  if (!campaign) return;

  const recipients = state.subscribers.filter((s) => s.isActive).length;
  const opened = recipients ? Math.floor(recipients * (0.35 + Math.random() * 0.45)) : 0;

  campaign.status = "sent";
  campaign.sentCount = recipients;
  campaign.openedCount = opened;

  save();
  render();
  setNotice(`Campaign sent to ${recipients} subscribers.`);
}

function toCsv(rows) {
  const escapeCell = (val) => {
    const raw = String(val ?? "");
    if (raw.includes(",") || raw.includes("\n") || raw.includes('"')) {
      return `"${raw.replace(/"/g, '""')}"`;
    }
    return raw;
  };

  return rows.map((row) => row.map(escapeCell).join(",")).join("\n");
}

function downloadFile(name, content, type) {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  URL.revokeObjectURL(url);
}

function parseCsvLine(line) {
  const cells = [];
  let current = "";
  let inQuotes = false;

  for (let i = 0; i < line.length; i += 1) {
    const char = line[i];
    const next = line[i + 1];

    if (char === "\"") {
      if (inQuotes && next === "\"") {
        current += "\"";
        i += 1;
      } else {
        inQuotes = !inQuotes;
      }
    } else if (char === "," && !inQuotes) {
      cells.push(current.trim());
      current = "";
    } else {
      current += char;
    }
  }

  cells.push(current.trim());
  return cells;
}

document.getElementById("subscriberForm").addEventListener("submit", (e) => {
  e.preventDefault();
  const form = e.currentTarget;
  const name = form.name.value.trim();
  const email = form.email.value.trim().toLowerCase();
  const department = form.department.value.trim();

  if (!name || !email) {
    setNotice("Name and email are required.");
    return;
  }

  if (state.subscribers.some((s) => s.email === email)) {
    setNotice("Subscriber with this email already exists.");
    return;
  }

  state.subscribers.unshift({
    id: uid(),
    name,
    email,
    department,
    isActive: true,
  });

  save();
  render();
  form.reset();
  setNotice(`Subscriber '${name}' added.`);
});

document.getElementById("campaignForm").addEventListener("submit", (e) => {
  e.preventDefault();
  const form = e.currentTarget;
  const name = form.name.value.trim();
  const subject = form.subject.value.trim();
  const body = form.body.value.trim();

  if (!name || !subject || !body) {
    setNotice("Campaign name, subject, and body are required.");
    return;
  }

  state.campaigns.unshift({
    id: uid(),
    name,
    subject,
    body,
    status: "draft",
    sentCount: 0,
    openedCount: 0,
  });

  save();
  render();
  form.reset();
  setNotice(`Campaign '${name}' created.`);
});

document.getElementById("exportSubscribers").addEventListener("click", () => {
  const rows = [
    ["name", "email", "department", "is_active"],
    ...state.subscribers.map((s) => [s.name, s.email, s.department || "", String(s.isActive)]),
  ];
  downloadFile("subscribers.csv", toCsv(rows), "text/csv;charset=utf-8");
  setNotice("Subscribers exported.");
});

document.getElementById("importSubscribers").addEventListener("change", async (e) => {
  const file = e.target.files?.[0];
  if (!file) return;

  const text = await file.text();
  const lines = text.split(/\r?\n/).filter((line) => line.trim().length > 0);
  if (!lines.length) return;

  const headers = parseCsvLine(lines[0]).map((h) => h.trim().toLowerCase());
  const nameIdx = headers.indexOf("name");
  const emailIdx = headers.indexOf("email");
  const deptIdx = headers.indexOf("department");

  if (nameIdx < 0 || emailIdx < 0) {
    setNotice("CSV must include at least name,email columns.");
    return;
  }

  let added = 0;
  for (const line of lines.slice(1)) {
    const cols = parseCsvLine(line);
    const name = cols[nameIdx] || "";
    const email = (cols[emailIdx] || "").toLowerCase();
    const department = deptIdx >= 0 ? cols[deptIdx] || "" : "";

    if (!name || !email || state.subscribers.some((s) => s.email === email)) {
      continue;
    }

    state.subscribers.push({ id: uid(), name, email, department, isActive: true });
    added += 1;
  }

  save();
  render();
  setNotice(`Imported ${added} subscriber(s).`);
  e.target.value = "";
});

document.getElementById("seedDemoData").addEventListener("click", () => {
  seedDemoData();
});

document.getElementById("clearAllData").addEventListener("click", () => {
  const confirmed = window.confirm("Clear all local UniMail demo data?");
  if (confirmed) {
    clearData();
  }
});

setNotice(`UniMail Pages app ready (v${APP_VERSION}).`);
render();
