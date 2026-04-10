import uuid
import random

from locust import HttpUser, task, between, events

QUERIES = [
    "पिकांची माहिती सांगा",
    "कापूस पिकाबद्दल सांगा",
    "ऊस पिकाची लागवड कशी करावी",
    "सोयाबीन पिकाची काळजी",
    "शेतीसाठी खत कोणते वापरावे",
    "कीटकनाशक फवारणी कधी करावी",
]

# Shared session IDs to simulate real users returning
_SESSION_POOL = [str(uuid.uuid4()) for _ in range(20)]


class ApiUser(HttpUser):
    wait_time = between(5, 10)

    def on_start(self):
        """Assign a persistent session to each simulated user."""
        self.session_id = random.choice(_SESSION_POOL)

    @task(3)
    def health(self):
        self.client.get("/api/health/live")

    @task(1)
    def root(self):
        self.client.get("/")

    @task(5)
    def chat(self):
        params = {
            "query": random.choice(QUERIES),
            "session_id": self.session_id,       # reuse session like a real user
            "source_lang": "mr",
            "target_lang": "mr",
            "user_id": "locust_user",
        }

        with self.client.get(
            "/api/chat/",
            params=params,
            headers={"Accept": "text/event-stream"},
            name="/api/chat (SSE)",
            catch_response=True,
            stream=True,
            timeout=60,           # SSE streams can be slow, give enough time
        ) as r:

            if r.status_code != 200:
                r.failure(f"HTTP {r.status_code}")
                return

            try:
                chunks_received = 0
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:
                        chunks_received += 1
                    if chunks_received > 10:      # read a bit more for realism
                        break

                if chunks_received == 0:
                    r.failure("No chunks received from SSE stream")
                else:
                    r.success()

            except Exception as e:
                r.failure(str(e))