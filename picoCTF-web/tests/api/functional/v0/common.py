"""Utilities for functional tests."""

import datetime
import json
import re

import pymongo
import pytest

import api
import api.problem
import api.shell_servers
import api.user

TESTING_DB_NAME = 'ctf_test'
db = None


def decode_response(res):
    """Parse a WebSuccess or WebError response."""
    decoded_dict = json.loads(res.data.decode('utf-8'))
    return (decoded_dict['status'], decoded_dict['message'],
            decoded_dict['data'])


def get_csrf_token(res):
    """Extract the CSRF token from a response."""
    for header in res.headers:
        m = re.search('token=(.+?);', header[1])
        if m:
            return m.group(1)
    return RuntimeError('Could not find CSRF token in response headers.')


def get_conn():
    """Get a connection to the testing database."""
    global db
    if db is None:
        client = pymongo.MongoClient('127.0.0.1')
        db = client[TESTING_DB_NAME]
    return db


def clear_db():
    """Clear out the testing database."""
    db = get_conn()
    db.command('dropDatabase')


@pytest.fixture
def client():
    """Create a test client of the Flask app."""
    app = api.create_app({
        'TESTING': True,
        'MONGO_DB_NAME': TESTING_DB_NAME
    })
    return app.test_client()


@pytest.fixture
def app():
    """Create an instance of the Flask app for testing."""
    app = api.create_app({
        'TESTING': True,
        'MONGO_DB_NAME': TESTING_DB_NAME
    })
    return app


ADMIN_DEMOGRAPHICS = {
                        'username': 'adminuser',
                        'password': 'adminpw',
                        'firstname': 'Admin',
                        'lastname': 'User',
                        'email': 'admin@example.com',
                        'eligibility': True,
                        'country': 'US',
                        'affiliation': 'Admin School',
                        'usertype': 'other',
                        'demo': {
                            'parentemail': 'admin@example.com',
                            'age': '18+'
                        },
                        'gid': None,
                        'rid': None
                      }

TEACHER_DEMOGRAPHICS = {
                        'username': 'teacheruser',
                        'password': 'teacherpw',
                        'firstname': 'Teacher',
                        'lastname': 'User',
                        'email': 'teacher@example.com',
                        'eligibility': True,
                        'country': 'US',
                        'affiliation': 'Sample School',
                        'usertype': 'teacher',
                        'demo': {
                            'parentemail': 'teacher@example.com',
                            'age': '18+'
                        },
                        'gid': None,
                        'rid': None
                      }

USER_DEMOGRAPHICS = {
                        'username': 'sampleuser',
                        'password': 'samplepw',
                        'firstname': 'Sample',
                        'lastname': 'User',
                        'email': 'sample@example.com',
                        'eligibility': True,
                        'country': 'US',
                        'affiliation': 'Sample School',
                        'usertype': 'student',
                        'demo': {
                            'parentemail': 'student@example.com',
                            'age': '13-17'
                        },
                        'gid': None,
                        'rid': None
                      }


def register_test_accounts():
    """
    Register an admin, teacher, and student account with known demographics.

    Intended to be used, if needed, in conjunction with clear_db()
    to set up a clean environment for each test.
    """
    with app().app_context():
        api.user.add_user(ADMIN_DEMOGRAPHICS)
        api.user.add_user(TEACHER_DEMOGRAPHICS)
        api.user.add_user(USER_DEMOGRAPHICS)


sample_shellserver_publish_output = r'''
{
  "problems": [
    {
      "name": "SQL Injection 1",
      "category": "Web Exploitation",
      "pkg_dependencies": [
        "php7.2-sqlite3"
      ],
      "description": "There is a website running at http://{{server}}:{{port}}. Try to see if you can login!",
      "score": 40,
      "hints": [],
      "author": "Tim Becker",
      "organization": "ForAllSecure",
      "instances": [
        {
          "user": "sql-injection-1_0",
          "deployment_directory": "/problems/sql-injection-1_0_9e114b246c48eb158b16525f71ae2a00",
          "service": "sql-injection-1_0",
          "socket": null,
          "server": "192.168.2.3",
          "description": "There is a website running at http://192.168.2.3:17648. Try to see if you can login!",
          "flag": "9ac0a74de6bced3cdce8e7fd466f32d0",
          "flag_sha1": "958416d52940e4948eca8d9fb1eca21e4cf7eda1",
          "instance_number": 0,
          "should_symlink": false,
          "files": [
            {
              "path": "webroot/config.php",
              "permissions": 436,
              "user": null,
              "group": null
            },
            {
              "path": "webroot/login.phps",
              "permissions": 436,
              "user": null,
              "group": null
            },
            {
              "path": "webroot/login.php",
              "permissions": 436,
              "user": null,
              "group": null
            },
            {
              "path": "webroot/index.html",
              "permissions": 436,
              "user": null,
              "group": null
            },
            {
              "path": "users.db",
              "permissions": 288,
              "user": null,
              "group": null
            },
            {
              "path": "xinet_startup.sh",
              "permissions": 1517,
              "user": null,
              "group": null
            }
          ],
          "port": 17648
        },
        {
          "user": "sql-injection-1_1",
          "deployment_directory": "/problems/sql-injection-1_1_10a4b1cdfd3a0f78d0d8b9759e6d69c5",
          "service": "sql-injection-1_1",
          "socket": null,
          "server": "192.168.2.3",
          "description": "There is a website running at http://192.168.2.3:10987. Try to see if you can login!",
          "flag": "28054fef0f362256c78025f82e6572c3",
          "flag_sha1": "f57fa5d3861c22a657eecafe30a43bd4ad7a4a2a",
          "instance_number": 1,
          "should_symlink": false,
          "files": [
            {
              "path": "webroot/config.php",
              "permissions": 436,
              "user": null,
              "group": null
            },
            {
              "path": "webroot/login.phps",
              "permissions": 436,
              "user": null,
              "group": null
            },
            {
              "path": "webroot/login.php",
              "permissions": 436,
              "user": null,
              "group": null
            },
            {
              "path": "webroot/index.html",
              "permissions": 436,
              "user": null,
              "group": null
            },
            {
              "path": "users.db",
              "permissions": 288,
              "user": null,
              "group": null
            },
            {
              "path": "xinet_startup.sh",
              "permissions": 1517,
              "user": null,
              "group": null
            },
            {
              "path": "xinet_startup.sh",
              "permissions": 1517,
              "user": null,
              "group": null
            }
          ],
          "port": 10987
        }
      ],
      "sanitized_name": "sql-injection-1"
    },
    {
      "name": "Buffer Overflow 1",
      "category": "Binary Exploitation",
      "description": "Exploit the {{url_for(\"vuln\", display=\"Buffer Overflow\")}} found here: {{directory}}.",
      "score": 50,
      "hints": [
        "This is a classic buffer overflow with no modern protections."
      ],
      "author": "Tim Becker",
      "organization": "ForAllSecure",
      "instances": [
        {
          "user": "buffer-overflow-1_0",
          "deployment_directory": "/problems/buffer-overflow-1_0_bab40cd8ebd7845e1c4c2951c6f82e1f",
          "service": null,
          "socket": null,
          "server": "192.168.2.3",
          "description": "Exploit the <a href='//192.168.2.3/static/bd08ee41f495f8bff378c13157d0f511/vuln'>Buffer Overflow</a> found here: /problems/buffer-overflow-1_0_bab40cd8ebd7845e1c4c2951c6f82e1f.",
          "flag": "638608c79eca2165e7b241ff365df05b",
          "flag_sha1": "4b97abef055a11ec19c14622eb31eb1168d98aca",
          "instance_number": 0,
          "should_symlink": true,
          "files": [
            {
              "path": "flag.txt",
              "permissions": 288,
              "user": null,
              "group": null
            },
            {
              "path": "vuln",
              "permissions": 1517,
              "user": null,
              "group": null
            }
          ]
        },
        {
          "user": "buffer-overflow-1_1",
          "deployment_directory": "/problems/buffer-overflow-1_1_f49b6bd5da29513569bd87f98a934fa6",
          "service": null,
          "socket": null,
          "server": "192.168.2.3",
          "description": "Exploit the <a href='//192.168.2.3/static/c95410042007bb17f49b891a2a87afb2/vuln'>Buffer Overflow</a> found here: /problems/buffer-overflow-1_1_f49b6bd5da29513569bd87f98a934fa6.",
          "flag": "35013564b97b80d4fd3f2be45e5836ff",
          "flag_sha1": "5675d2d5819084d4203c1ef314239527074938a9",
          "instance_number": 1,
          "should_symlink": true,
          "files": [
            {
              "path": "flag.txt",
              "permissions": 288,
              "user": null,
              "group": null
            },
            {
              "path": "vuln",
              "permissions": 1517,
              "user": null,
              "group": null
            }
          ]
        }
      ],
      "sanitized_name": "buffer-overflow-1"
    },
    {
      "name": "ECB 1",
      "category": "Cryptography",
      "description": "There is a crypto service running at {{server}}:{{port}}. We were able to recover the source code, which you can download at {{url_for(\"ecb.py\")}}.",
      "hints": [],
      "score": 70,
      "author": "Tim Becker",
      "organization": "ForAllSecure",
      "pip_requirements": [
        "pycrypto"
      ],
      "pip_python_version": "3",
      "instances": [
        {
          "user": "ecb-1_0",
          "deployment_directory": "/problems/ecb-1_0_73a0108a98d2862a86f4b71534aaf7c3",
          "service": "ecb-1_0",
          "socket": null,
          "server": "192.168.2.3",
          "description": "There is a crypto service running at 192.168.2.3:46981. We were able to recover the source code, which you can download at <a href='//192.168.2.3/static/fd59acc6b8d2359d48bd939a08ecb8ab/ecb.py'>ecb.py</a>.",
          "flag": "49e56ea9bf2e2b60ba9af034b5b2a5fd",
          "flag_sha1": "77cec418714d6eb0dc48afa6d6f38200402a83c0",
          "instance_number": 0,
          "should_symlink": false,
          "files": [
            {
              "path": "flag",
              "permissions": 288,
              "user": null,
              "group": null
            },
            {
              "path": "key",
              "permissions": 288,
              "user": null,
              "group": null
            },
            {
              "path": "ecb.py",
              "permissions": 1517,
              "user": null,
              "group": null
            },
            {
              "path": "xinet_startup.sh",
              "permissions": 1517,
              "user": null,
              "group": null
            }
          ],
          "port": 46981
        },
        {
          "user": "ecb-1_1",
          "deployment_directory": "/problems/ecb-1_1_83b2ed9a1806c86219347bc4982a66de",
          "service": "ecb-1_1",
          "socket": null,
          "server": "192.168.2.3",
          "description": "There is a crypto service running at 192.168.2.3:21953. We were able to recover the source code, which you can download at <a href='//192.168.2.3/static/beb9874a05a1810fa8c9d79152ace1b3/ecb.py'>ecb.py</a>.",
          "flag": "85a32ccd05fa30e0efd8da555c1a101a",
          "flag_sha1": "f28581a86561c885152f7622200057585787c063",
          "instance_number": 1,
          "should_symlink": false,
          "files": [
            {
              "path": "flag",
              "permissions": 288,
              "user": null,
              "group": null
            },
            {
              "path": "key",
              "permissions": 288,
              "user": null,
              "group": null
            },
            {
              "path": "ecb.py",
              "permissions": 1517,
              "user": null,
              "group": null
            },
            {
              "path": "xinet_startup.sh",
              "permissions": 1517,
              "user": null,
              "group": null
            }
          ],
          "port": 21953
        }
      ],
      "sanitized_name": "ecb-1"
    }
  ],
  "bundles": [
    {
      "name": "Challenge Sampler",
      "author": "Christopher Ganas",
      "description": "This is the set of example challenges provided in the picoCTF-Problems repository.",
      "categories": [
        "Binary Exploitation",
        "Cryptography",
        "Web Exploitation"
      ],
      "problems": [
        "buffer-overflow-1",
        "ecb-1",
        "sql-injection-1"
      ],
      "dependencies": {
        "ecb-1": {
          "threshold": 1,
          "weightmap": {
            "buffer-overflow-1": 1
          }
        },
        "sql-injection-1": {
          "threshold": 1,
          "weightmap": {
            "buffer-overflow-1": 1,
            "ecb-1": 1
          }
        }
      }
    }
  ],
  "sid": "728f36885f7c4686805593b9e4988c30"
}
'''

problems_endpoint_response = [{'name': 'SQL Injection 1', 'category': 'Web Exploitation', 'description': 'There is a website running at http://192.168.2.3:17648. Try to see if you can login!', 'score': 40, 'hints': [], 'author': 'Tim Becker', 'organization': 'ForAllSecure', 'sanitized_name': 'sql-injection-1', 'disabled': False, 'pid': '4508167aa0b219fd9d131551d10aa58e', 'solves': 0, 'socket': None, 'server': '192.168.2.3', 'port': 17648, 'server_number': 1, 'solved': False, 'unlocked': True}, {'name': 'Buffer Overflow 1', 'category': 'Binary Exploitation', 'description': "Exploit the <a href='//192.168.2.3/static/bd08ee41f495f8bff378c13157d0f511/vuln'>Buffer Overflow</a> found here: /problems/buffer-overflow-1_0_bab40cd8ebd7845e1c4c2951c6f82e1f.", 'score': 50, 'hints': ['This is a classic buffer overflow with no modern protections.'], 'author': 'Tim Becker', 'organization': 'ForAllSecure', 'sanitized_name': 'buffer-overflow-1', 'disabled': False, 'pid': '1bef644c399e10a3f35fecdbf590bd0c', 'solves': 0, 'socket': None, 'server': '192.168.2.3', 'server_number': 1, 'solved': False, 'unlocked': True}, {'name': 'ECB 1', 'category': 'Cryptography', 'description': "There is a crypto service running at 192.168.2.3:21953. We were able to recover the source code, which you can download at <a href='//192.168.2.3/static/beb9874a05a1810fa8c9d79152ace1b3/ecb.py'>ecb.py</a>.", 'hints': [], 'score': 70, 'author': 'Tim Becker', 'organization': 'ForAllSecure', 'sanitized_name': 'ecb-1', 'disabled': False, 'pid': '7afda419da96e8471b49df9c2009e2ef', 'solves': 0, 'socket': None, 'server': '192.168.2.3', 'port': 21953, 'server_number': 1, 'solved': False, 'unlocked': True}]


def load_sample_problems():
    """Load the sample problems and bundle into the DB."""
    with app().app_context():
        db = get_conn()
        db.shell_servers.insert_one({
            'sid': '728f36885f7c4686805593b9e4988c30',
            'name': 'Test shell server',
            'host': 'testing.picoctf.com',
            'port': '22',
            'username': 'username',
            'password': 'password',
            'protocol': 'HTTPS',
            'server_number': 1
        })
        api.problem.load_published(
            json.loads(sample_shellserver_publish_output)
        )


def enable_sample_problems():
    """Enable any sample problems in the DB."""
    db = get_conn()
    db.problems.update_many({}, {'$set': {'disabled': False}})


def ensure_within_competition():
    """Adjust the competition times so that protected methods are callable."""
    db = get_conn()
    db.settings.update_one({}, {'$set': {
        'start_time': datetime.datetime.utcnow() - datetime.timedelta(1),
        'end_time': datetime.datetime.utcnow() + datetime.timedelta(1),
        }})
