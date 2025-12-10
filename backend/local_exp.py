import random
import math
import requests
import numpy as np
import matplotlib.pyplot as plt
from collections import Counter

API = "http://127.0.0.1:8000"

random.seed(42)

# --------------------------
# Weighted Randomized Response
# --------------------------

def weighted_krr(true_id, option_ids, epsilon_user, option_weights):
    k = len(option_ids)
    if k < 2:
        return true_id

    w = option_weights.get(true_id, 1.0)
    epsilon_eff = epsilon_user / w

    e = math.exp(epsilon_eff)
    p = e / (e + k - 1)

    if random.random() < p:
        return true_id
    else:
        others = [o for o in option_ids if o != true_id]
        return random.choice(others)


# --------------------------
# MAIN EXPERIMENT
# --------------------------

def create_poll(question, options_with_weights):
    # 1. Create poll
    r = requests.post(f"{API}/create_poll", json={"question": question})
    poll_id = r.json()["poll_id"]

    # 2. Add options with weights
    for text, weight in options_with_weights:
        requests.post(f"{API}/add_option", json={
            "poll_id": poll_id,
            "text": text,
            "weight": weight
        })

    return poll_id


def load_poll(poll_id):
    return requests.get(f"{API}/poll/{poll_id}").json()


def close_poll(poll_id):
    requests.post(f"{API}/close_poll", json={"poll_id": poll_id})


def get_results(poll_id):
    return requests.get(f"{API}/results/{poll_id}").json()



# --------------------------
# Utility samplers
# --------------------------

def sample_from_dist(d):
    r = random.random()
    acc = 0
    for key, p in d.items():
        acc += p
        if r <= acc:
            return key
    return list(d.keys())[-1]


# --------------------------
# FULL EXPERIMENT
# --------------------------

def run_single_experiment():

    # create poll
    poll_id = create_poll(
        "Who is the best CS professor?",
        [("Prof. Kretchmar", 1.0), ("Prof. Law", 1.0), ("Prof. Lall", 1.0), ("Prof. Truex", 2.0)]
    )

    # Load poll to get option IDs
    poll_data = load_poll(poll_id)
    options = poll_data["options"]
    option_ids = [opt["id"] for opt in options]

    # Map numeric IDs (0,1,2,3) → true option IDs assigned by DB
    id_map = {i: option_ids[i] for i in range(len(option_ids))}

    #print(f"Poll {poll_id} ({poll_data['question']})")

    true_counts = Counter()

    # simulate Users Voting 
    #print(f"Simulating {N_USERS} users voting...")
    for _ in range(N_USERS):
        # choose true option
        true_opt = sample_from_dist(true_probs)
        true_counts[true_opt] += 1

        # choose epsilon_user for this user
        eps_user = sample_from_dist(privacy_dist)

        # apply LDP
        reported_true_id = id_map[true_opt]
        opt_weights = {id_map[k]: option_weights[k] for k in option_weights}

        reported_id = weighted_krr(
            reported_true_id,
            option_ids,
            eps_user,
            opt_weights
        )

        effective_epsilon = eps_user / opt_weights[reported_true_id]

        # send the vote to your real backend
        requests.post(f"{API}/vote", json={
            "poll_id": poll_id,
            "option_id": reported_id,
            "voter_token": f"test_user_{_}",  # unique synthetic token
            "epsilon_used": effective_epsilon
        })

    #print("Closing poll...")
    close_poll(poll_id)

    # ----- 4. Get results -----
   # print("Fetching debiased results...")
   # results = get_results(poll_id)

    # print("\n--- True Counts ---")
    # for k, v in sorted(true_counts.items()):
    #     print(f"Option {k}: {v}")

    # print("\n--- Debiased Estimates ---")
    # for k, est in results["results"].items():
    #     print(f"{k}: {est:.2f}")

    # print("\nTotal synthetic votes:", N_USERS)

    # Prepare vectors for error calculation
    debiased = get_results(poll_id)["results"]

    # Convert debiased dict {"A":value, "B":value...} -> vector
    debiased_vec = np.array([debiased[k] for k in debiased])

    return np.array([true_counts[i] for i in range(4)]), debiased_vec



# --------------------------
# Simulation Parameters
# --------------------------

N_values = [50, 100, 200, 500, 1000]


# True distribution of votes
true_probs = {
    0: 0.2,   # Option A
    1: 0.05,   # Option B
    2: 0.15,  # Option C
    3: 0.6   # Option D 
}

# User privacy distribution
privacy_dist = {
    0.5: 1/3,   # High privacy
    1.0: 1/3,   # Medium
    2.0: 1/3    # Low privacy
}

# Creator weights
option_weights = {
    0: 1.0,
    1: 1.0,
    2: 1.0,
    3: 2.0   # Extra protected
}
TRIALS = 5
all_errors = []

# Run the pipeline for each N
for N in N_values:
    N_USERS = N
    avg_true = np.zeros(4)
    avg_debiased = np.zeros(4)
    for t in range(TRIALS):
        true_vec, debiased_vec = run_single_experiment()
        for i in range(4):
            avg_true[i] += true_vec[i]
            avg_debiased[i] += debiased_vec[i]

    for i in range(4):
        avg_true[i] /= TRIALS
        avg_debiased[i] /= TRIALS

    abs_errors = np.abs(avg_true - avg_debiased)
    all_errors.append(abs_errors)

    # print(f"\nN = {N}")
    # for i, e in enumerate(abs_errors):
    #     print(f"  Option {i}: error {e:.2f}")

    # ---------------------
    # Clustered bar chart
    # ---------------------
    x = np.arange(4)
    width = 0.35
    plt.figure(figsize=(7,5))
    plt.bar(x - width/2, avg_true, width, label="True Counts")
    plt.bar(x + width/2, avg_debiased, width, label="Avg. Debiased Estimates")
    plt.xticks(x, ["Prof. Kretchmar","Prof. Law","Prof. Lall","Prof. Truex"])
    plt.title(f"True vs Debiased Counts (N={N})")
    plt.ylabel("Counts")
    plt.legend()
    plt.grid(axis="y")
    #plt.show()
    plt.savefig(f"debiasing_N_{N}.png")
    plt.close()


# # ============================================================
# #     Graph 2: Error vs N (total error)
# # ============================================================
# total_errors = [err.sum() for err in all_errors]

# plt.figure(figsize=(7,5))
# plt.plot(N_values, total_errors, marker='o')
# plt.xlabel("N (Synthetic Users)")
# plt.ylabel("Total L1 Error")
# plt.title("Total Debiasing Error vs Sample Size")
# plt.grid(True)
# plt.show()


# # ============================================================
# #     Graph 3: Per-option error vs N
# # ============================================================
# all_errors = np.array(all_errors)  # shape (len(N), 4)

# plt.figure(figsize=(7,5))
# for opt in range(4):
#     plt.plot(N_values, all_errors[:, opt], marker='o', label=f"Option {opt}")

# plt.xlabel("N (Synthetic Users)")
# plt.ylabel("Absolute Error")
# plt.title("Per-option Error vs Sample Size")
# plt.legend()
# plt.grid(True)
# plt.show()