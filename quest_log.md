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
