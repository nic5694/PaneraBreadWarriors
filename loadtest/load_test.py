from itertools import count
from uuid import uuid4

from locust import FastHttpUser, SequentialTaskSet, between, task


user_counter = count(1)
url_counter = count(1)
run_id = uuid4().hex[:8]


class ApiWorkflow(SequentialTaskSet):
    def _create_user_with_retry(self, max_attempts=10):
        last_error = None
        for _ in range(max_attempts):
            unique_token = uuid4().hex
            self.user_payload = {
                "name": f"load-test-{run_id}-user-{self.user_index}-{unique_token[:8]}",
                "email": f"load-test-{run_id}-user-{self.user_index}-{unique_token[:8]}@example.com",
                "password": "password123",
            }

            response = self.client.post(
                "/users",
                json=self.user_payload,
                name="POST /users",
            )

            if response.status_code == 201:
                self.user_id = response.json()["data"]["id"]
                return

            if response.status_code != 409:
                response.raise_for_status()

            last_error = response.text

        raise RuntimeError(
            f"Failed to create unique user payload after retries. Last error: {last_error}"
        )

    def _create_url_with_retry(self, max_attempts=10):
        last_error = None
        for _ in range(max_attempts):
            unique_token = uuid4().hex
            payload = {
                "user_id": str(self.user_id),
                "shortcode": f"lt-{unique_token[:16]}",
                "original_url": f"https://example.com/{run_id}/{self.user_index}/{unique_token}",
                "title": "Load test URL",
            }

            response = self.client.post(
                "/urls/",
                json=payload,
                name="POST /urls",
            )

            if response.status_code == 201:
                self.url_payload = payload
                self.url_id = response.json()["data"]["id"]
                self.shortcode = response.json()["data"]["shortcode"]
                return

            if response.status_code != 409:
                response.raise_for_status()

            last_error = response.text

        raise RuntimeError(
            f"Failed to create unique URL payload after retries. Last error: {last_error}"
        )

    def on_start(self):
        self.user_index = next(user_counter)
        self.url_index = next(url_counter)

        self._create_user_with_retry()

        self._create_url_with_retry()

        self.event_payload = {
            "url_id": self.url_id,
            "event_type": "click",
        }

        with self.client.post(
            "/events",
            json=self.event_payload,
            name="POST /events",
            catch_response=True,
        ) as response:
            if response.status_code != 201:
                response.failure(
                    f"Event bootstrap failed status={response.status_code} body={response.text[:500]}"
                )

    def _health(self):
        self.client.get("/health", name="GET /health")

    def _list_users(self):
        self.client.get("/users", name="GET /users")

    def _get_user(self):
        self.client.get(
            f"/users/{self.user_id}",
            name="GET /users/:id",
        )

    def _update_user(self):
        update_payload = {
            "name": f"load-test-{run_id}-user-{self.user_index}-updated",
            "email": f"load-test-{run_id}-user-{self.user_index}-updated@example.com",
        }
        self.client.patch(
            f"/users/{self.user_id}",
            json=update_payload,
            name="PATCH /users/:id",
        )

    def _resolve_shortcode(self):
        self.client.get(
            f"/r/{self.shortcode}",
            name="GET /r/:shortcode",
            allow_redirects=False,
        )

    def _list_events(self):
        self.client.get(
            "/events",
            name="GET /events",
        )

    @task
    def run_workload(self):
        self._health()
        self._list_users()
        self._get_user()
        self._update_user()
        self._resolve_shortcode()
        self._list_events()

    def on_stop(self):
        self.client.delete(
            f"/users/{self.user_id}",
            name="DELETE /users/:id",
        )


class ApiUser(FastHttpUser):
    wait_time = between(0.5, 1.5)
    tasks = [ApiWorkflow]