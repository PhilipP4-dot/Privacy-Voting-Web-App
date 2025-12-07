const api = "http://127.0.0.1:8000";

let pollId = null;
let selectedOption = null;
let voterId = null;
let resultsIntervalId = null;

// Ensure a stable anonymous voter token per browser
if (!localStorage.getItem("voter_id")) {
    const uuid = (self.crypto && self.crypto.randomUUID)
        ? self.crypto.randomUUID()
        : String(Math.random()) + Date.now();
    localStorage.setItem("voter_id", uuid);
}
voterId = localStorage.getItem("voter_id");

const questionEl = document.getElementById("question");
const optionsEl = document.getElementById("options");
const resultsEl = document.getElementById("results");
const submitBtn = document.getElementById("submit");
const pollIdInput = document.getElementById("poll-id-input");
const loadBtn = document.getElementById("load-btn");

// Event delegation for radio buttons
optionsEl.addEventListener("change", (e) => {
    if (e.target.name === "vote") {
        selectedOption = e.target.value;
    }
});

// Load a poll by ID
async function loadPoll(id) {
    pollId = id;
    selectedOption = null;
    questionEl.textContent = "Loading poll...";
    optionsEl.innerHTML = "";
    resultsEl.innerHTML = "";
    submitBtn.disabled = false;

    try {
        const res = await fetch(`${api}/poll/${pollId}`);
        const data = await res.json();

        if (data.error) {
            questionEl.textContent = "Poll not found.";
            submitBtn.disabled = true;
            return;
        }

        questionEl.textContent = data.question;

        // Render options
        optionsEl.innerHTML = "";
        data.options.forEach(opt => {
            const label = document.createElement("label");
            label.innerHTML = `
        <input type="radio" name="vote" value="${opt.id}">
        ${opt.text}
      `;
            optionsEl.appendChild(label);
        });

        // Handle closed poll state from API
        if (data.status === "closed") {
            questionEl.textContent += " (Poll closed)";
            submitBtn.disabled = true;
        }

        // Start polling results for this poll
        startResultsPolling();
    } catch (err) {
        questionEl.textContent = "Error loading poll.";
        submitBtn.disabled = true;
    }
}

// Poll results periodically for the current poll
function startResultsPolling() {
    if (!pollId) return;

    if (resultsIntervalId !== null) {
        clearInterval(resultsIntervalId);
    }

    resultsIntervalId = setInterval(async () => {
        try {
            const res = await fetch(`${api}/results/${pollId}`);
            const data = await res.json();

            // If results are hidden until poll is closed
            if (data.status === "hidden") {
                resultsEl.innerHTML = `<p>${data.message}</p>`;
                return;
            }

            if (data.status === "ok" && data.results) {
                resultsEl.innerHTML = "";
                for (const [name, count] of Object.entries(data.results)) {
                    resultsEl.innerHTML += `<p>${name}: ${count}</p>`;
                }
            }
        } catch (err) {
            // silently ignore for now
        }
    }, 1500);
}

// Load poll via "Load poll" button
loadBtn.onclick = () => {
    const id = Number(pollIdInput.value);
    if (!id) {
        alert("Enter a poll ID.");
        return;
    }
    loadPoll(id);
};

// Load poll via ?poll= query parameter
const params = new URLSearchParams(window.location.search);
const paramPoll = params.get("poll");
if (paramPoll) {
    pollIdInput.value = paramPoll;
    loadPoll(Number(paramPoll));
}

// Submit vote
submitBtn.onclick = async () => {
    if (!pollId) {
        alert("No poll loaded.");
        return;
    }
    if (!selectedOption) {
        alert("Pick an option.");
        return;
    }

    try {
        const resp = await fetch(`${api}/vote`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                poll_id: Number(pollId),
                option_id: Number(selectedOption),
                voter_token: voterId
            })
        });

        const data = await resp.json();

        if (data.status === "error") {
            if (data.message === "Already voted") {
                alert("You have already voted in this poll.");
            } else if (data.message === "Poll is closed") {
                alert("This poll is closed. You can't vote.");
                submitBtn.disabled = true;
            } else {
                alert("Error: " + data.message);
            }
        } else {
            alert("Vote recorded!");
        }
    } catch (err) {
        alert("Error submitting vote.");
    }
};
