import time
from locust import HttpUser, task, between


class QuickstartUser(HttpUser):
    wait_time = between(1, 5)

    @task
    def generate_schedule(self):
        self.client.post(
            "/recommend-schedule",
            json={
                "program_code": "0508",
                "start_year": 2027,
                "start_term": "Fall",
                "target_grad_year": 2032,
                "target_grad_term": "Spring",
                "taken_courses": [
                    "MATE3031",
                    "QUIM3131",
                    "QUIM3133",
                    "CIIC3015",
                    "QUIM3132",
                    "QUIM3134",
                    "CIIC3075",
                    "CIIC4010",
                    "MATE3032",
                    "MATE3063",
                    "FISI3171",
                    "FISI3173",
                    "CIIC4020",
                ],
                "specific_elective_credits_initial": {
                    "english": 6,
                    "spanish": 6,
                    "sociohumanistics": 6,
                    "technical": 3,
                    "free": 0,
                    "kinesiology": 0,
                },
                "credit_load_preference": {"min": 9, "max": 18},
                "summer_preference": "None",
                "specific_summers": None,
                "difficulty_curve": "Flat",
            },
        )
