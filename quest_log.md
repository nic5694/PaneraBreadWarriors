# Quest Log of Our Progress

---

## 🗺️ Original Quests

### Tier 1 ✅
Finished the models, routers, and seeded the database.

### Tier 2 ✅
Created integration and unit tests.

### Tier 3 ✅
Deployed with ArgoCD and Proxmox, with two status checks on GitHub Pages.

---

## 🛡️ Reliability Engineering — Build a service that refuses to die easily.

> In the real world, code breaks. Your job is to build a safety net so strong that even when things go wrong, the service keeps running.

**Difficulty:** ⭐⭐

---

### 🥉 Tier 1: Bronze — The Shield

**Objective:** Prove your code works before you ship it.

#### ⚔️ Main Objectives

- **Write Unit Tests:** Test suite using pytest. Test individual functions in isolation. ✅
- **Automate Defense:** GitHub Actions runs tests on every commit. ✅
- **Pulse Check:** `GET /health` returns `200 OK`. ✅

#### ✅ Verification (Loot)

- CI logs showing green/passing tests.
- A working `GET /health` endpoint.

---

> 💡 **Hidden Reliability Score:** Bonus up to +50 awarded for resilient behavior — rejecting bad input, preserving data consistency, enforcing uniqueness, and maintaining expected behavior across core flows.

### 🥈 Tier 2: Silver (The Fortress)
**Objective** Stop bad code from ever reaching production.

#### ⚔️ Main Objectives
- 50% Coverage: Use pytest-cov. Ensure half your code lines are hit by tests.
- Integration Testing: Write tests that hit the API (e.g., POST to /shorten  → Check DB).

The Gatekeeper: Configure CI so deployment fails if tests fail.
Error Handling: Document how your app handles 404s and 500s.
> 💡 Intel Blocking Deploys: This is the #1 rule of SRE. Never ship broken code.
> Integration vs Unit: Unit tests check the engine; integration tests check if the car drives.

✅ Verification (Loot)
Coverage report showing >50%.
A screenshot of a blocked deploy due to a failed test.

### 🥇 Tier 3: Gold (The Immortal)
**Objective** Break it on purpose. Watch it survive.

#### ⚔️ Main Objectives
- 70% Coverage: High confidence in code stability.
- Graceful Failure: Send bad inputs. The app must return clean errors (JSON), not crash.
- Chaos Mode: Kill the app process or container while it's running. Show it restarts automatically (e.g., Docker restart policy).
- Failure Manual: Document exactly what happens when things break (Failure Modes).

> 💡 Intel **Chaos Engineering** Don't wait for a crash at 3 AM. Cause the crash at 2 PM and fix it.
> Graceful: A user should see "Service Unavailable," not a Python stack trace.

✅ Verification (Loot)
- Live Demo: Kill the container→Watch it resurrect.
- Live Demo: Send garbage data→Get a polite error.
- Link to "Failure Mode" documentation.
🧰 Recommended Loadout: pytest, pytest-cov, GitHub Actions
