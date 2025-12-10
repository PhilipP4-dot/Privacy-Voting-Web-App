const api = "http://127.0.0.1:8000";

let pollId = null;
let selectedOption = null;
let voterId = null;
let optionIds = [];
let optionWeights = {};  // option_id → weight
let pollStatus = "open";

// Ensure persistent anonymous voter token
if (!localStorage.getItem("voter_id")) {
    localStorage.setItem("voter_id", crypto.randomUUID());
}
voterId = localStorage.getItem("voter_id");

// DOM elements
const questionEl = document.getElementById("question");
const optionsEl = document.getElementById("options");
const resultsEl = document.getElementById("results");
const submitBtn = document.getElementById("submit");
const pollIdInput = document.getElementById("poll-id-input");
const loadBtn = document.getElementById("load-btn");
const privacySelect = document.getElementById("privacy-select");

// ---- LDP RANDOMIZED RESPONSE ----
function weightedKRR(trueId, optionIds, epsilonUser, optionWeights) {
    const k = optionIds.length;
    if (k < 2) return trueId;

    // Creator-set weight for this option
    const w = optionWeights[trueId] || 1.0;

    // Effective epsilon: lower epsilon = stronger privacy
    const effectiveEpsilon = epsilonUser / w;

    const e = Math.exp(effectiveEpsilon);
    const p = e / (e + k - 1);
    const q = (1 - p) / (k - 1);

    if (Math.random() < p) return trueId;

    const others = optionIds.filter(id => id !== trueId);
    return others[Math.floor(Math.random() * others.length)];
}

// ---- LOAD POLL ----
async function loadPoll(id) {
    pollId = id;
    questionEl.innerText = "Loading...";
    optionsEl.innerHTML = "";
    resultsEl.innerHTML = "";

    const res = await fetch(api + "/poll/" + pollId);
    const data = await res.json();

    if (data.error) {
        questionEl.innerText = "Poll not found.";
        return;
    }

    pollStatus = data.status;
    optionIds = [];
    optionWeights = {};

    questionEl.innerText = data.question +
        (pollStatus === "closed" ? " (Poll closed)" : "");

    data.options.forEach(opt => {
        optionIds.push(opt.id);
        optionWeights[opt.id] = opt.weight;

        const label = document.createElement("label");
        label.innerHTML = `
      <input type="radio" name="vote" value="${opt.id}">
      ${opt.text}
    `;
        optionsEl.appendChild(label);
    });

    document.addEventListener("change", (e) => {
        if (e.target.name === "vote") {
            selectedOption = e.target.value;
        }
    });

    // Disable voting if poll closed
    submitBtn.disabled = pollStatus === "closed";

    startResultsPolling();
}

// ---- POLL RESULTS ----
function startResultsPolling() {
    setInterval(async () => {
        if (!pollId) return;

        const res = await fetch(api + "/results/" + pollId);
        const data = await res.json();

        if (data.status === "hidden") {
            resultsEl.innerHTML = `<p>${data.message}</p>`;
            return;
        }
        if (data.status === "ok") {
            resultsEl.innerHTML = "";
            const results = data.results;

            for (const [name, est] of Object.entries(results)) {
                const rounded = Math.max(0, Math.round(est));
                resultsEl.innerHTML += `<p>${name}: ~${rounded}</p>`;
            }
        }
    }, 1500);
}

// ---- LOAD POLL BUTTON ----
loadBtn.onclick = () => {
    const id = Number(pollIdInput.value);
    if (!id) {
        alert("Enter a poll ID.");
        return;
    }
    loadPoll(id);
};

// Auto-load poll via ?poll=
const params = new URLSearchParams(window.location.search);
const paramPoll = params.get("poll");
if (paramPoll) {
    pollIdInput.value = paramPoll;
    loadPoll(Number(paramPoll));
}

// ---- SUBMIT VOTE ----
submitBtn.onclick = async () => {
    if (!pollId) {
        alert("No poll loaded.");
        return;
    }
    if (!selectedOption) {
        alert("Pick an option.");
        return;
    }
    if (pollStatus === "closed") {
        alert("Poll is closed.");
        return;
    }

    const trueId = Number(selectedOption);
    const epsilonUser = Number(privacySelect.value);

    const reportedId = weightedKRR(trueId, optionIds, epsilonUser, optionWeights);
    const effectiveEpsilon = epsilonUser / (optionWeights[trueId] || 1.0);

    const resp = await fetch(api + "/vote", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            poll_id: pollId,
            option_id: reportedId,
            voter_token: voterId,
            epsilon_used: effectiveEpsilon
        })
    });

    const data = await resp.json();

    if (data.status === "error" && data.message === "Already voted") {
        alert("You have already voted.");
    } else if (data.status === "error") {
        alert(data.message);
    } else {
        alert("Your private vote has been recorded.");
    }
};
