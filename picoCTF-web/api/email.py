"""Module for email related functionality."""

from flask_mail import Message

import api
from api import PicoException

# The Flask-Mail object. Should be initialized during app startup.
mail = None


def request_password_reset(username):
    """
    Email a user a link to reset their password.

    Args:
        username: the username of the account

    Raises:
        PicoException: if provided username not found

    """
    user = api.user.get_user(name=username)
    if user is None:
        raise PicoException(
            'Username not found', 404)

    token_value = api.token.set_token({"uid": user['uid']}, "password_reset")

    settings = api.config.get_settings()

    body = """We recently received a request to reset the password for the following {0} account:\n\n\t{2}\n\nOur records show that this is the email address used to register the above account.  If you did not request to reset the password for the above account then you need not take any further steps.  If you did request the password reset please follow the link below to set your new password. \n\n {1}/reset#{3} \n\n Best of luck! \n The {0} Team""".format(  # noqa:E501
        settings["competition_name"], settings["competition_url"], username,
        token_value)

    subject = "{} Password Reset".format(settings["competition_name"])

    message = Message(body=body, recipients=[user['email']], subject=subject)
    mail.send(message)


def send_user_verification_email(username):
    """
    Email the user a link to verify their account.

    If email_verification is enabled in the config then the user
    won't be able to login until this step is completed.
    """
    settings = api.config.get_settings()

    user = api.user.get_user(name=username)

    # The number of verification attempts is stored in the key
    # along with the uid.

    key_query = {
        "$and": [{
            "uid": user["uid"]
        }, {
            "email_verification_count": {
                "$exists": True
            }
        }]
    }
    previous_key = api.token.find_key(key_query)

    if previous_key is None:
        token_value = api.token.set_token({
            "uid": user["uid"],
            "email_verification_count": 1
        }, "email_verification")
    else:
        previous_count = previous_key['email_verification_count']
        if (previous_count < settings["email"]["max_verification_emails"]):
            token_value = previous_key["tokens"]["email_verification"]
            api.token.delete_token(key_query, 'email_verification')
            api.token.set_token({
                'uid': user['uid'],
                'email_verification_count': previous_count + 1
            }, 'email_verification')
        else:
            raise PicoException(
                "User has been sent the maximum number of verification " +
                "emails.", 422)

    verification_link = "{}/api/user/verify?uid={}&token={}".\
        format(settings["competition_url"], user["uid"], token_value)

    body = """
Welcome to {0}!

You will need to visit the verification link below and then login to finalize
your account's creation.

If you believe this to be a mistake, and you haven't recently created an account
for {0} then you can safely ignore this email.

Verification link: {1}

Good luck and have fun!
The {0} Team.
    """.format(settings["competition_name"], verification_link) # noqa (79char)

    subject = "{} Account Verification".format(settings["competition_name"])

    verification_message = Message(
        body=body, recipients=[user['email']], subject=subject)

    bulk = [verification_message]

    # Also send parent verification email if neccessary
    if (settings["email"]["parent_verification_email"] and
            previous_key is None and user['demo']['age'] == "13-17"):
        body = """
Welcome to {0}!

An user account has just been created on our platform and your email address was
submitted by the user as the email address of the user's parent.

Thank you for authorizing the participation of your child age 13-17 in
{0} and providing your email address as part of the account registration process
for your child. As a reminder, the Terms of Service, Privacy Statement and
Competition Rules for {0} can be found at {1}.

If you received this email in error because you did not authorize your child's
registration for {0}, you are not the child's parent or legal guardian,
or your child is under age 13, please email us immediately at {2}.
        """.format(settings["competition_name"], "https://url", # noqa (79char)
                   "admin@email.com")

        subject = "{} Parent Account Verification".format(
            settings["competition_name"])
        recipients = [user['demo']['parentemail']]
        parent_email = Message(
            body=body, recipients=recipients, subject=subject)

        bulk.append(parent_email)

    with mail.connect() as conn:
        for msg in bulk:
            conn.send(msg)


def send_email_invite(gid, email, teacher=False):
    """
    Send an email registration link that will automatically join into a group.

    This link will bypass the email filter.
    """
    settings = api.config.get_settings()
    group = api.group.get_group(gid=gid)

    token_value = api.token.set_token({
        "gid": group["gid"],
        "email": email,
        "teacher": teacher
    }, "registration_token")

    registration_link = "{}/#g={}&r={}".\
        format(settings["competition_url"], group["gid"], token_value)

    body = """
You have been invited by the staff of the {1} organization to compete in {0}.
You will need to follow the registration link below to finish the account creation process.

If you believe this to be a mistake you can safely ignore this email.

Registration link: {2}

Good luck!
  The {0} Team.
    """.format(settings["competition_name"], group["name"], registration_link) # noqa (79char)

    subject = "{} Registration".format(settings["competition_name"])

    message = Message(body=body, recipients=[email], subject=subject)
    mail.send(message)
