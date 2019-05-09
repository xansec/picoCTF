"""Classes and functions used by multiple modules in the system."""
import uuid
from hashlib import md5

import bcrypt
import bson.json_util as json_util
from voluptuous import Invalid, MultipleInvalid


def token():
    """
    Generate a random but insecure token.

    Returns:
        The randomly generated token

    """
    return str(uuid.uuid4().hex)


def hash(string):
    """
    Hash a string.

    Args:
        string: string to be hashed.
    Returns:
        The hex digest of the string.

    """
    return md5(string.encode("utf-8")).hexdigest()


class PicoException(Exception):
    """
    General class for exceptions in the picoCTF API.

    Allows specification of a message and response code to display to the
    client, as well as an optional field for arbitrary data.

    The 'data' field will not be displayed to clients but will be stored
    in the database, making it ideal for storing stack traces, etc.
    """

    def __init__(self, message, status_code=500, data=None):
        """Initialize a new PicoException."""
        Exception.__init__(self)
        self.message = message
        self.status_code = status_code
        self.data = data

    def to_dict(self):
        """Convert a PicoException to a dict for serialization."""
        rv = dict()
        rv['message'] = self.message
        return rv


class APIException(Exception):
    """Base class for exceptions thrown by the API."""

    data = {}


class InternalException(APIException):
    """Exceptions thrown by the API constituting mild errors."""

    pass


def WebSuccess(message=None, data=None):
    """Legacy successful response wrapper."""
    return json_util.dumps({
            'status': 1,
            'message': message,
            'data': data
        })


def WebError(message=None, data=None):
    """Legacy failure response wrapper."""
    return json_util.dumps({
            'status': 0,
            'message': message,
            'data': data
        })


def flat_multi(multidict):
    """
    Flatten any single element lists in a multidict.

    Args:
        multidict: multidict to be flattened.
    Returns:
        Partially flattened database.

    """
    flat = {}
    for key, values in multidict.items():
        flat[key] = values[0] if type(values) == list and len(values) == 1 \
                    else values
    return flat


def check(*callback_tuples):
    """
    Voluptuous wrapper function to raise our APIException.

    Args:
        callback_tuples: a callback_tuple should contain
                         (status, msg, callbacks)
    Returns:
        Returns a function callback for the Schema

    """
    def v(value):
        """
        Try to validate the value with the given callbacks.

        Args:
            value: the item to validate
        Raises:
            APIException with the given error code and msg.
        Returns:
            The value if the validation callbacks are satisfied.

        """
        for msg, callbacks in callback_tuples:
            for callback in callbacks:
                try:
                    result = callback(value)
                    if not result and type(result) == bool:
                        raise Invalid()
                except Exception:
                    raise PicoException(msg, 400)
        return value
    return v


def validate(schema, data):
    """
    Wrap the call to voluptuous schema to raise the proper exception.

    Args:
        schema: The voluptuous Schema object
        data: The validation data for the schema object

    Raises:
        APIException with status 0 and the voluptuous error message

    """
    try:
        schema(data)
    except MultipleInvalid as error:
        raise PicoException(error.msg, 400)


def safe_fail(f, *args, **kwargs):
    """
    Safely call a function that can raise an APIException.

    Args:
        f: function to call
        *args: positional arguments
        **kwargs: keyword arguments
    Returns:
        The function result or None if an exception was raised.
    """
    try:
        return f(*args, **kwargs)
    except APIException:
        return None


def hash_password(password):
    """
    Hash plaintext password.

    Args:
        password: plaintext password
    Returns:
        Secure hash of password.

    """
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(8))
