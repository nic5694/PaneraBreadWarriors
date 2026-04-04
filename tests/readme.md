🧪 Events API Testing Overview
This documentation covers the two-tier testing strategy implemented for the PaneraBreadWarriors Events service. We use Unit Tests to verify Python logic and Integration Tests to ensure database resilience.

🛠️ Unit Testing (Isolated Logic)
File: tests/unit_tests/events/unit_tests_events.py

These tests use unittest.mock to bypass the database entirely. They are designed to run in milliseconds and verify the EventService business logic.

What is verified:

JSON Serialization: Confirms the details dictionary is correctly stringified for database storage.

Error Translation: Ensures that a missing URL in the database triggers a custom UrlNotFoundError instead of a raw database crash.

Input Validation: Verifies that the service strictly enforces the presence of url_id and event_type.

Run Command:

Bash
pytest tests/unit_tests/events/unit_tests_events.py
🔗 Integration Testing (Database & Resilience)
File: tests/integration/events/test_events.py

Integration tests verify the full "Request-to-Database" lifecycle. These tests interact with the live PostgreSQL instance and are marked with @pytest.mark.integration.

Key Features:

Unique Data Generation: Uses uuid to generate random shortcodes and user_emails for every test run, preventing 409 CONFLICT errors caused by database unique constraints.

Sequence Recovery Test: A specialized test, test_create_event_recovers_from_sequence_drift, manually breaks the PostgreSQL ID sequence (setting it to 1) and verifies that the EventService automatically detects the IntegrityError, resyncs the sequence to MAX(id), and retries the operation successfully.

Status Code Validation: Confirms the Flask Blueprints return the correct RESTful status codes (201, 400, 404).

Run Command:

Bash
pytest -m integration tests/integration/events/test_events.py
🚀 Troubleshooting Guide
Error	Likely Cause	Solution
409 CONFLICT	A unique field (like shortcode) already exists in the DB.	Ensure the uuid helper is used in the _create_url test fixture.
AttributeError: Proxy	A unit test tried to touch the real database.	Mock the model methods (Event.create or Url.get_by_id) specifically.
500 INTERNAL ERROR	The database sequence is out of sync.	Run the sequence reset SQL or ensure the Service recovery logic is active.
📊 Summary Commands
Run All Tests: pytest

Run with Stdout Logs: pytest -s

Check Coverage: pytest --cov=app/services/event_service.py