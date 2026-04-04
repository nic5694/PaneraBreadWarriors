# Reliability

Reliability of GitRev is built on preventative testing, deployment guardrails, and graceful failure behavior. The service is validated with unit and integration tests, monitored through health checks, and exercised under controlled failure scenarios to ensure the system remains stable and recovers safely when issues occur.

## Tier 1

**Status:** Completed

**Objective:** Prove your code works before you ship it.

**Main Objectives:**

- Write unit tests with pytest to validate isolated logic
- Run tests automatically in GitHub Actions on every commit
- Implement health endpoint returns HTTP 200

**Results:**

| Metric | Target | Actual |
|--------|--------|--------|
| Unit Test Coverage | Baseline test suite present | TODO: Add more tests to reach baseline coverage |
| CI Test Automation | Run on every commit | Completed CI pipeline is set up to run tests on every push/PR before changes are promoted to the deployment |
| Health Endpoint | 200 OK | 200 OK |

**Test Run Date:** -  
**Test Duration:** -  
**Notes:** Unit tests, CI checks are active and CD is deploying only if tests pass; health endpoint is confirmed working.

**Verification:**

TODO: output the CI into a file and link it below to show passing tests and health check response. Add a screenshot of the CI pipeline showing green/passing tests and a curl command showing the health check response.
- CI logs showing passing test runs
- Health check response from GET /health

---

### Tier 2: Silver

**Status:** In Progress

**Objective:** Stop bad code from reaching production.

**Main Objectives:**

- Reach at least 50% code coverage using pytest-cov - TODO: Add more tests to reach 50% coverage
- Add integration tests that hit API endpoints and verify database effects - TODO: Add integration tests that hit API endpoints and verify database effects
- Block deployment when tests fail in CI - DONE: CI pipeline is configured to fail deploy if tests fail
- Document application handling for 404 and 500 errors - TODO: Add documentation for 404 and 500 error handling

**Results:**

| Metric | Target | Actual |
|--------|--------|--------|
| Coverage | >= 50% | - |
| Integration Tests | API + DB validation | - |
| CI Gate | Failed tests block deploy | Completed within the [python_ci.yml](../.github/workflows/python_ci.yml) workflow |
| Error Handling Docs | 404 and 500 behavior documented | - |

**Test Run Date:** -  
**Test Duration:** -  
**CI Gate Behavior:** -  
**Error Handling Notes:** -  
**Notes:** -

**Verification:**

- Coverage report showing >= 50%
- Integration test evidence
- Screenshot of blocked deploy due to failing tests

---

### Tier 3: Gold

**Status:** Not Started

**Objective:** Intentionally break the system and verify graceful recovery.

**Main Objectives:**

- Reach at least 70% code coverage
- Validate graceful failure responses for bad input
- Demonstrate automatic recovery after process/container failure - DONE: Kubernetes will automatically restart failed containers, and the application should recover without manual intervention
- Document failure modes and recovery behavior - TODO: Add documentation detailing how the system handles failures and recovers with proof of the chaos testing

**Results:**

| Metric | Target | Actual |
|--------|--------|--------|
| Coverage | >= 70% | - |
| Graceful Failure | Clean JSON errors, no crash | - |
| Auto Recovery | Container/process restarts | Completed within the Kubernetes deployment configuration |
| Failure Mode Documentation | Completed | - |

**Test Run Date:** -  
**Test Duration:** -  
**Chaos Test Method:** -  
**Recovery Observation:** -  
**Notes:** -

**Failure Analysis:**

Question: What failed during chaos testing?  
Answer: -

Question: How did the system recover?  
Answer: -

Question: What reliability improvements were added?  
Answer: -

**Verification:**

- Live demo evidence of container/process restart and recovery
- Live demo evidence of graceful validation errors for bad input
- Link to failure mode documentation

