const api = "http://127.0.0.1:8000";

let newOptions = [];      // {text, weight}
let loadedPollId = null;

// DOM references
const qInput = document.getElementById("new-question");
const optInput = document.getElementById("new-option");
const weightInput = document.getElementById("option-weight");
const optList = document.getElementById("option-list");
const createBtn = document.getElementById("create-poll");
const createdInfo = document.getElementById("created-info");

const loadId = document.getElementById("load-id");
const loadBtn = document.getElementById("load-poll");
const loadedInfo = document.getElementById("loaded-info");
const loadedOptions = document.getElementById("loaded-options");

const closePollBtn = document.getElementById("close-poll");
const resultsDiv = document.getElementById("poll-results");

// ---- ADD OPTION LOCALLY BEFORE CREATION ----
document.getElementById("add-option").onclick = () => {
    const text = optInput.value.trim();
    const weight = Number(weightInput.value) || 1.0;

    if (!text) return;

    newOptions.push({ text, weight });

    const li = document.createElement("li");
    li.textContent = `${text} (weight = ${weight})`;
    optList.appendChild(li);

    optInput.value = "";
    weightInput.value = "";
};

// ---- CREATE POLL ----
createBtn.onclick = async () => {
    const question = qInput.value.trim();

    if (!question || newOptions.length < 2) {
        alert("Enter a question and at least two options.");
        return;
    }

    // 1. create poll
    const pollRes = await fetch(api + "/create_poll", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question })
    });

    const pollData = await pollRes.json();
    const pollId = pollData.poll_id;

    // 2. send options with weights
    for (const opt of newOptions) {
        await fetch(api + "/add_option", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                poll_id: pollId,
                text: opt.text,
                weight: opt.weight
            })
        });
    }

    // display link
    const link = `${window.location.origin}/index.html?poll=${pollId}`;
    createdInfo.innerHTML = `
    <p><strong>Poll Created!</strong> ID: ${pollId}</p>
    <p>Voting Link:</p>
    <code>${link}</code>
  `;

    loadedPollId = pollId;

    // reset
    newOptions = [];
    optList.innerHTML = "";
    qInput.value = "";
};

// ---- LOAD EXISTING POLL ----
loadBtn.onclick = async () => {
    const id = Number(loadId.value);
    if (!id) return;

    const res = await fetch(api + "/poll/" + id);
    const data = await res.json();

    if (data.error) {
        loadedInfo.innerHTML = "<p>Poll not found.</p>";
        return;
    }

    loadedPollId = id;
    loadedInfo.innerHTML = `<p><strong>${data.question}</strong> (ID: ${id}) -- Status: ${data.status}</p>`;
    loadedOptions.innerHTML = "";

    data.options.forEach(opt => {
        const li = document.createElement("li");
        li.textContent = `${opt.text} (weight = ${opt.weight})`;
        loadedOptions.appendChild(li);
    });

    resultsDiv.innerHTML = "";
};

// ---- CLOSE POLL ----
closePollBtn.onclick = async () => {
    if (!loadedPollId) {
        alert("Load a poll first.");
        return;
    }

    const res = await fetch(api + "/close_poll", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ poll_id: loadedPollId })
    });

    const data = await res.json();
    alert(data.message || "Poll closed.");

    loadResults();
};

// ---- LOAD DEBIASED RESULTS ----
async function loadResults() {
    if (!loadedPollId) return;

    const res = await fetch(api + "/results/" + loadedPollId);
    const data = await res.json();

    if (data.status === "hidden") {
        resultsDiv.innerHTML = `<p>${data.message}</p>`;
        return;
    }

    if (data.status === "ok") {
        resultsDiv.innerHTML = "";
        for (const [optText, est] of Object.entries(data.results)) {
            const rounded = Math.max(0, Math.round(est));
            resultsDiv.innerHTML += `<p>${optText}: ~${rounded}</p>`;
        }
    }
}
