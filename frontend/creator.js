const api = "http://127.0.0.1:8000";

let newOptions = [];
let loadedPollId = null;

// DOM elements
const qInput = document.getElementById("new-question");
const optInput = document.getElementById("new-option");
const optList = document.getElementById("option-list");
const createBtn = document.getElementById("create-poll");
const createdInfo = document.getElementById("created-info");

const loadId = document.getElementById("load-id");
const loadBtn = document.getElementById("load-poll");
const loadedInfo = document.getElementById("loaded-info");
const loadedOptions = document.getElementById("loaded-options");
const closePollBtn = document.getElementById("close-poll");
const resultsDiv = document.getElementById("poll-results");


// Add new option to local list
document.getElementById("add-option").onclick = () => {
    const text = optInput.value.trim();
    if (!text) return;

    newOptions.push(text);

    const li = document.createElement("li");
    li.textContent = text;
    optList.appendChild(li);

    optInput.value = "";
};


// Create poll flow
createBtn.onclick = async () => {
    const question = qInput.value.trim();
    if (!question || newOptions.length < 2) {
        alert("Enter question and at least 2 options.");
        return;
    }

    // 1. Create poll
    const res = await fetch(api + "/create_poll", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question })
    });

    const data = await res.json();
    const pollId = data.poll_id;

    // 2. Add options
    for (const text of newOptions) {
        await fetch(api + "/add_option", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ poll_id: pollId, text })
        });
    }

    // Show info
    const link = `${window.location.origin}/index.html?poll=${pollId}`;
    createdInfo.innerHTML = `
    <p><strong>Poll Created!</strong> ID: ${pollId}</p>
    <p>Voting Link:</p>
    <code>${link}</code>
  `;

    // reset
    newOptions = [];
    optList.innerHTML = "";
    qInput.value = "";
};


// Load existing poll
loadBtn.onclick = async () => {
    const id = Number(loadId.value);
    if (!id) return;

    const res = await fetch(api + "/poll/" + id);
    const data = await res.json();

    if (data.error) {
        loadedInfo.innerHTML = `<p>Poll not found.</p>`;
        return;
    }

    loadedPollId = id;
    loadedInfo.innerHTML = `<p><strong>${data.question}</strong> (ID: ${id})</p>`;
    loadedOptions.innerHTML = "";

    data.options.forEach(opt => {
        const li = document.createElement("li");
        li.textContent = opt.text;
        loadedOptions.appendChild(li);
    });

    resultsDiv.innerHTML = "";
};


// Close poll
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

    loadPollResults();
};


// Load results (only visible if poll is closed)
async function loadPollResults() {
    if (!loadedPollId) return;

    const res = await fetch(api + "/results/" + loadedPollId);
    const data = await res.json();

    if (data.status === "hidden") {
        resultsDiv.innerHTML = `<p>${data.message}</p>`;
        return;
    }

    if (data.status === "ok") {
        resultsDiv.innerHTML = "";
        for (const [name, count] of Object.entries(data.results)) {
            resultsDiv.innerHTML += `<p>${name}: ${count}</p>`;
        }
    }
}
