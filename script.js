const SESSION_ID = (window.crypto && crypto.randomUUID)
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(16).slice(2)}`;

let isSendingChat = false;
let allScenarios = [];
let activeScenarioFilter = "ALL";

function showSection(sectionId) {
    const target = document.getElementById(sectionId);
    if (!target) return;

    document.querySelectorAll(".section").forEach((sec) => {
        sec.classList.remove("active");
    });
    target.classList.add("active");

    document.querySelectorAll(".nav").forEach((btn) => {
        btn.classList.toggle("active", btn.dataset.section === sectionId);
    });

    window.scrollTo({ top: 0, behavior: "smooth" });
}

function appendChatMessage(text, sender, risk = null) {
    const container = document.getElementById("messages");
    const bubble = document.createElement("div");
    bubble.className = `message ${sender}`;

    if (sender === "bot" && (risk === "HIGH" || risk === "MEDIUM")) {
        const badge = document.createElement("span");
        badge.className = `risk-tag ${risk}`;
        badge.textContent = `${risk} RISK`;
        bubble.appendChild(badge);
        bubble.appendChild(document.createElement("br"));
    }

    bubble.appendChild(document.createTextNode(text));
    container.appendChild(bubble);
    container.scrollTop = container.scrollHeight;
    return bubble;
}

function createTypingBubble() {
    const container = document.getElementById("messages");
    const bubble = document.createElement("div");
    bubble.className = "message bot";
    bubble.innerHTML = `<span class="typing-dots" aria-label="Assistant typing"><span></span><span></span><span></span></span>`;
    container.appendChild(bubble);
    container.scrollTop = container.scrollHeight;
    return bubble;
}

async function handleChatSubmit(event) {
    if (event) event.preventDefault();
    if (isSendingChat) return;

    const input = document.getElementById("chatInput");
    const sendBtn = document.getElementById("sendChatBtn");
    const message = input.value.trim();
    if (!message) return;

    appendChatMessage(message, "user");
    input.value = "";
    isSendingChat = true;
    sendBtn.disabled = true;

    const typingBubble = createTypingBubble();

    try {
        const response = await fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                message,
                session_id: SESSION_ID
            })
        });

        const data = await response.json();
        typingBubble.remove();

        if (!response.ok) {
            appendChatMessage(data.error || "Unable to get a response right now.", "bot");
            return;
        }

        appendChatMessage(data.reply, "bot", data.risk);
    } catch {
        typingBubble.remove();
        appendChatMessage("Unable to connect to the server. Please try again.", "bot");
    } finally {
        isSendingChat = false;
        sendBtn.disabled = false;
        input.focus();
    }
}

async function renderCheckResult() {
    const input = document.getElementById("checkInput");
    const out = document.getElementById("checkResult");
    const message = input.value.trim();

    if (!message) {
        out.innerHTML = `<p class="result-explanation">Paste a message above before running the check.</p>`;
        return;
    }

    out.innerHTML = `<p class="result-explanation">Checking message...</p>`;

    try {
        const response = await fetch("/api/check", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message })
        });

        const data = await response.json();

        if (!response.ok) {
            out.innerHTML = `<p class="result-explanation">${data.error || "Unable to analyze message."}</p>`;
            return;
        }

        out.innerHTML = "";

        const box = document.createElement("div");
        box.className = "result-box";

        const riskBadge = document.createElement("span");
        riskBadge.className = `badge ${data.risk}`;
        riskBadge.textContent = `RISK LEVEL: ${data.risk}`;

        const explanation = document.createElement("p");
        explanation.className = "result-explanation";
        explanation.textContent = data.explanation;

        box.append(riskBadge, explanation);

        if (Array.isArray(data.scams) && data.scams.length > 0) {
            const scamHeading = document.createElement("h3");
            scamHeading.className = "result-sub";
            scamHeading.textContent = "Possible Fraud Types";
            box.appendChild(scamHeading);

            const row = document.createElement("div");
            row.className = "keyword-row";
            data.scams.forEach((scam) => {
                const pill = document.createElement("span");
                pill.className = "kw-pill";
                pill.textContent = scam;
                row.appendChild(pill);
            });
            box.appendChild(row);
        }

        if (Array.isArray(data.actions) && data.actions.length > 0) {
            const actionHeading = document.createElement("h3");
            actionHeading.className = "result-sub";
            actionHeading.textContent = "Recommended Actions";
            box.appendChild(actionHeading);

            const list = document.createElement("ul");
            list.className = "action-list";
            data.actions.forEach((act) => {
                const li = document.createElement("li");
                li.textContent = act;
                list.appendChild(li);
            });
            box.appendChild(list);
        }

        out.appendChild(box);
    } catch {
        out.innerHTML = `<p class="result-explanation">Unable to check the message. Please try again.</p>`;
    }
}

function renderScenarios() {
    const grid = document.getElementById("scenarioList");
    const items = activeScenarioFilter === "ALL"
        ? allScenarios
        : allScenarios.filter((s) => (s.risk || "HIGH") === activeScenarioFilter);

    grid.innerHTML = "";

    if (!items.length) {
        grid.innerHTML = `<p class="result-explanation">No scenarios match this filter.</p>`;
        return;
    }

    items.forEach((item) => {
        const riskLevel = item.risk || "HIGH";
        const card = document.createElement("article");
        card.className = "card scenario-card";

        const head = document.createElement("div");
        head.className = "scenario-head";

        const title = document.createElement("h3");
        title.textContent = item.name;

        const badge = document.createElement("span");
        badge.className = `badge ${riskLevel}`;
        badge.textContent = riskLevel;

        head.append(title, badge);

        const desc = document.createElement("p");
        desc.textContent = item.description;

        const warn = document.createElement("p");
        warn.className = "scenario-meta-item";
        warn.innerHTML = `<strong>Warning:</strong> ${item.warning}`;

        const guard = document.createElement("p");
        guard.className = "scenario-meta-item";
        guard.innerHTML = `<strong>How to stay safe:</strong> ${item.protection}`;

        card.append(head, desc, warn, guard);
        grid.appendChild(card);
    });
}

async function loadScenarios() {
    const grid = document.getElementById("scenarioList");
    try {
        const response = await fetch("/api/scenarios");
        const data = await response.json();
        allScenarios = Array.isArray(data) ? data : [];
        renderScenarios();
    } catch {
        grid.innerHTML = `<p class="result-explanation">Unable to load scam scenarios.</p>`;
    }
}

function bindEvents() {
    document.querySelectorAll("[data-section]").forEach((el) => {
        el.addEventListener("click", () => showSection(el.dataset.section));
        if (el.matches(".interactive-card")) {
            el.addEventListener("keydown", (e) => {
                if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    showSection(el.dataset.section);
                }
            });
        }
    });

    document.getElementById("chatForm").addEventListener("submit", handleChatSubmit);

    document.querySelectorAll("[data-quick]").forEach((btn) => {
        btn.addEventListener("click", () => {
            document.getElementById("chatInput").value = btn.dataset.quick;
            handleChatSubmit();
        });
    });

    document.getElementById("clearChatBtn").addEventListener("click", () => {
        const messages = document.getElementById("messages");
        messages.innerHTML = "";
        appendChatMessage("Chat cleared. Ask me about a UPI message, call, or payment request.", "bot");
    });

    document.getElementById("runCheckBtn").addEventListener("click", renderCheckResult);

    document.getElementById("sampleCheckBtn").addEventListener("click", () => {
        document.getElementById("checkInput").value =
            "URGENT: Your bank account KYC will be blocked today. Click the link and share OTP to verify.";
        renderCheckResult();
    });

    document.getElementById("clearCheckBtn").addEventListener("click", () => {
        document.getElementById("checkInput").value = "";
        document.getElementById("checkResult").innerHTML = "";
    });

    document.querySelectorAll(".filter-pill").forEach((pill) => {
        pill.addEventListener("click", () => {
            document.querySelectorAll(".filter-pill").forEach((p) => p.classList.remove("active"));
            pill.classList.add("active");
            activeScenarioFilter = pill.dataset.filter;
            renderScenarios();
        });
    });

    document.getElementById("copyStepsBtn").addEventListener("click", async (e) => {
        const btn = e.currentTarget;
        const steps = Array.from(document.querySelectorAll("#emergencySteps li"))
            .map((li, idx) => `${idx + 1}. ${li.textContent.trim()}`)
            .join("\n");

        try {
            await navigator.clipboard.writeText(steps);
            const prev = btn.textContent;
            btn.textContent = "Copied";
            setTimeout(() => { btn.textContent = prev; }, 1600);
        } catch {
            btn.textContent = "Copy failed";
        }
    });
}

document.addEventListener("DOMContentLoaded", () => {
    bindEvents();
    loadScenarios();
});