"use strict";

const state = {
    token: null,
    user: null,
    authMode: "login",
    planType: "home",
};

const $ = (selector) => document.querySelector(selector);

const authSection = $("#auth-section");
const dashboard = $("#dashboard");
const authForm = $("#auth-form");
const authMessage = $("#auth-message");
const plannerMessage = $("#planner-message");
const resultSection = $("#result-section");

function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>"']/g, (character) => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;",
    })[character]);
}

function formatRupees(value) {
    return new Intl.NumberFormat("en-IN", {
        style: "currency",
        currency: "INR",
        maximumFractionDigits: 0,
    }).format(Number(value) || 0);
}

function showMessage(element, message, success = false) {
    element.textContent = message;
    element.classList.toggle("success", success);
}

async function api(path, options = {}) {
    const headers = new Headers(options.headers || {});

    if (state.token) {
        headers.set("Authorization", `Bearer ${state.token}`);
    }

    if (options.body && !headers.has("Content-Type")) {
        headers.set("Content-Type", "application/json");
    }

    const response = await fetch(path, {
        ...options,
        headers,
    });

    let data = {};

    try {
        data = await response.json();
    } catch {
        data = {};
    }

    if (!response.ok) {
        if (response.status === 401 && state.token) {
            logout(false);
        }

        let detail = data.detail;

        if (Array.isArray(detail)) {
            detail = detail.map((item) => item.msg).join(", ");
        }

        throw new Error(
            typeof detail === "string"
                ? detail
                : "The request could not be completed."
        );
    }

    return data;
}

function setAuthMode(mode) {
    state.authMode = mode;

    document.querySelectorAll("[data-auth-mode]").forEach((button) => {
        button.classList.toggle(
            "active",
            button.dataset.authMode === mode
        );
    });

    const registering = mode === "register";

    $("#name-group").classList.toggle("hidden", !registering);
    $("#auth-name").required = registering;
    $("#auth-password").autocomplete = registering
        ? "new-password"
        : "current-password";

    $("#auth-submit").textContent = registering
        ? "Create account"
        : "Log in";

    showMessage(authMessage, "");
}

function setAuthenticated(user, token) {
    state.user = user;
    state.token = token;

    // Keep the session in memory instead of localStorage.
    authSection.classList.add("hidden");
    dashboard.classList.remove("hidden");
    $("#logout-btn").classList.remove("hidden");
    $("#user-label").textContent = user.name;

    loadHistory();
}

function logout(showNotice = true) {
    state.token = null;
    state.user = null;

    authSection.classList.remove("hidden");
    dashboard.classList.add("hidden");
    $("#logout-btn").classList.add("hidden");
    $("#user-label").textContent = "";

    resultSection.classList.add("hidden");
    $("#history-list").replaceChildren();

    authForm.reset();
    setAuthMode("login");

    if (showNotice) {
        showMessage(authMessage, "You have logged out.", true);
    }
}

authForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const submitButton = $("#auth-submit");
    submitButton.disabled = true;
    showMessage(authMessage, "Please wait...");

    const formData = new FormData(authForm);

    const payload = {
        email: String(formData.get("email") || "").trim(),
        password: String(formData.get("password") || ""),
    };

    if (state.authMode === "register") {
        payload.name = String(formData.get("name") || "").trim();
    }

    try {
        const endpoint = state.authMode === "register"
            ? "/auth/register"
            : "/auth/login";

        const data = await api(endpoint, {
            method: "POST",
            body: JSON.stringify(payload),
        });

        setAuthenticated(data.user, data.access_token);
        authForm.reset();
        showMessage(plannerMessage, "Welcome to PocketSmart AI.", true);
    } catch (error) {
        showMessage(authMessage, error.message);
    } finally {
        submitButton.disabled = false;
    }
});

document.querySelectorAll("[data-auth-mode]").forEach((button) => {
    button.addEventListener("click", () => {
        setAuthMode(button.dataset.authMode);
    });
});

$("#logout-btn").addEventListener("click", () => logout());

const plannerTitles = {
    home: "Home budget planner",
    party: "Party budget planner",
    jewelry: "Jewelry recommendation planner",
};

function selectPlanner(planType) {
    state.planType = planType;

    document.querySelectorAll("[data-plan-type]").forEach((button) => {
        button.classList.toggle(
            "selected",
            button.dataset.planType === planType
        );
    });

    $("#planner-title").textContent = plannerTitles[planType];

    $("#rooms-group").classList.toggle("hidden", planType !== "home");
    $("#people-group").classList.toggle("hidden", planType !== "party");

    resultSection.classList.add("hidden");
    showMessage(plannerMessage, "");
}

document.querySelectorAll("[data-plan-type]").forEach((button) => {
    button.addEventListener("click", () => {
        selectPlanner(button.dataset.planType);
    });
});

$("#planner-form").addEventListener("submit", async (event) => {
    event.preventDefault();

    if (!state.token) {
        showMessage(plannerMessage, "Please log in first.");
        return;
    }

    const button = $("#generate-btn");
    button.disabled = true;
    button.textContent = "Generating...";
    showMessage(plannerMessage, "Creating your budget plan...");

    const payload = {
        plan_type: state.planType,
        budget: Number($("#budget").value),
        currency: "INR",
        rooms: Number($("#rooms").value || 1),
        people: Number($("#people").value || 10),
        style: $("#style").value,
        occasion: $("#occasion").value.trim(),
        requirements: $("#requirements").value.trim(),
    };

    try {
        const result = await api("/api/planners", {
            method: "POST",
            body: JSON.stringify(payload),
        });

        renderPlan(result);
        showMessage(plannerMessage, "Your plan has been saved.", true);
        await loadHistory();
    } catch (error) {
        showMessage(plannerMessage, error.message);
    } finally {
        button.disabled = false;
        button.textContent = "Generate my plan";
    }
});

function renderPlan(plan) {
    const result = plan.result;

    $("#result-title").textContent = result.title;
    $("#result-summary").textContent = result.summary || "";

    $("#result-budget").textContent = formatRupees(result.budget);
    $("#result-total").textContent = formatRupees(result.total_estimated);
    $("#result-remaining").textContent = formatRupees(
        result.remaining_budget
    );

    $("#provider-label").textContent =
        plan.ai_provider === "gemini"
            ? "Gemini AI"
            : "Sample recommendations";

    const tbody = $("#items-body");
    tbody.replaceChildren();

    for (const item of result.items || []) {
        const row = document.createElement("tr");

        const itemCell = document.createElement("td");
        const name = document.createElement("strong");
        name.textContent = item.name;

        const details = document.createElement("div");
        details.className = "muted";
        details.textContent = item.reason || item.category || "";

        itemCell.append(name, details);

        const quantityCell = document.createElement("td");
        quantityCell.textContent = String(item.quantity);

        const unitCell = document.createElement("td");
        unitCell.textContent = formatRupees(item.unit_price);

        const totalCell = document.createElement("td");
        totalCell.textContent = formatRupees(item.total_price);

        const linkCell = document.createElement("td");
        const link = document.createElement("a");
        link.className = "search-link";
        link.textContent = "Search";
        link.href =
            "https://www.google.com/search?q=" +
            encodeURIComponent(item.search_query || item.name);
        link.target = "_blank";
        link.rel = "noopener noreferrer";

        linkCell.append(link);
        row.append(itemCell, quantityCell, unitCell, totalCell, linkCell);
        tbody.append(row);
    }

    const tipsList = $("#tips-list");
    tipsList.replaceChildren();

    for (const tip of result.tips || []) {
        const li = document.createElement("li");
        li.textContent = tip;
        tipsList.append(li);
    }

    resultSection.classList.remove("hidden");
    resultSection.scrollIntoView({
        behavior: "smooth",
        block: "start",
    });
}

async function loadHistory() {
    if (!state.token) return;

    const history = $("#history-list");
    history.replaceChildren();

    const loading = document.createElement("p");
    loading.className = "muted";
    loading.textContent = "Loading saved plans...";
    history.append(loading);

    try {
        const plans = await api("/api/planners?limit=20");
        history.replaceChildren();

        if (!plans.length) {
            const empty = document.createElement("p");
            empty.className = "muted";
            empty.textContent = "Your saved plans will appear here.";
            history.append(empty);
            return;
        }

        for (const plan of plans) {
            const item = document.createElement("article");
            item.className = "history-item";

            const info = document.createElement("div");
            const title = document.createElement("strong");
            title.textContent = plan.title;

            const detail = document.createElement("p");
            detail.textContent =
                `${plan.plan_type} · ${formatRupees(plan.budget)} · ` +
                new Date(plan.created_at).toLocaleString();

            info.append(title, detail);

            const actions = document.createElement("div");
            actions.className = "history-actions";

            const viewButton = document.createElement("button");
            viewButton.className = "small-button";
            viewButton.type = "button";
            viewButton.textContent = "View";
            viewButton.addEventListener("click", () => renderPlan(plan));

            const deleteButton = document.createElement("button");
            deleteButton.className = "small-button";
            deleteButton.type = "button";
            deleteButton.textContent = "Delete";
            deleteButton.addEventListener("click", async () => {
                if (!window.confirm("Delete this saved plan?")) return;

                deleteButton.disabled = true;

                try {
                    await api(`/api/planners/${plan.id}`, {
                        method: "DELETE",
                    });

                    await loadHistory();
                } catch (error) {
                    window.alert(error.message);
                    deleteButton.disabled = false;
                }
            });

            actions.append(viewButton, deleteButton);
            item.append(info, actions);
            history.append(item);
        }
    } catch (error) {
        history.replaceChildren();

        const errorMessage = document.createElement("p");
        errorMessage.className = "message";
        errorMessage.textContent = error.message;
        history.append(errorMessage);
    }
}

$("#refresh-history").addEventListener("click", loadHistory);

setAuthMode("login");
selectPlanner("home");