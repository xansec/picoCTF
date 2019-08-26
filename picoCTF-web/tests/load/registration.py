"""Register various types of users and store their login credentials."""

import random
import uuid
from locust import HttpLocust, TaskSet, task
from locust.exception import StopLocust

from demographics_generator import get_affiliation, get_country_code, get_user_type, get_username, get_password, get_email, get_demographics

MONGO_HOST = "127.0.0.1"
MONGO_PORT = 27017
MONGO_USER = None
MONGO_PASS = None

API_BASE_URL = 'api/v1'
REGISTRATION_ENDPOINT = API_BASE_URL + '/users'

def generate_user():
    """Generate a set of valid demographics for the given user type."""
    user_fields =  {
        'username': get_username(),
        'password': 'password',
        'email': get_email(),
        'affiliation': get_affiliation(),
        'country': get_country_code(),
        'usertype': get_user_type(),
        'demo': get_demographics(),
    }
    return user_fields

class RegistrationTasks(TaskSet):

    @task(weight=10)
    def successfully_register(l):
        user_demographics = generate_user()
        l.client.post(REGISTRATION_ENDPOINT, json=user_demographics)
        raise StopLocust # Terminate after successful registration

    @task(weight=1)
    def registration_error(l):
        user_demographics = generate_user()
        user_demographics['username'] = ''
        with l.client.post(REGISTRATION_ENDPOINT,
                json=user_demographics, catch_response=True) as res:
            if res.status_code == 400:
                res.success()


class RegistrationLocust(HttpLocust):
    task_set = RegistrationTasks
    min_wait = 1000
    max_wait = 4000
