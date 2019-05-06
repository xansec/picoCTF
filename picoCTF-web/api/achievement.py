"""Module for interacting with the achievements."""

from datetime import datetime
from importlib.machinery import SourceFileLoader
from os.path import join

import api.config
import api.db
import api.user
import api.logger
from api.common import InternalException


def get_achievement(aid):
    """
    Get a single achievement by aid.

    Args:
        aid: the achievement id
    Returns:
        the achievement dict, or None if not found
    """
    db = api.db.get_conn()
    return db.achievements.find_one({'aid': aid}, {"_id": 0})


def get_all_achievements():
    """
    Get all of the achievements in the database.

    Returns:
        List of achievement dicts from the database

    """
    db = api.db.get_conn()
    return list(
        db.achievements.find({}, {"_id": 0}))


def get_earned_achievement_instances(tid=None, uid=None):
    """
    Get the solved achievements for a given team or user.

    Args:
        uid / tid: Optional filters (exclusive, uid takes precedence)
    Returns:
        List of solved achievements
    """
    db = api.db.get_conn()

    match = {}

    if uid is not None:
        match.update({"uid": uid})
    elif tid is not None:
        match.update({"tid": tid})

    return list(db.earned_achievements.find(match, {"_id": 0}))


def set_earned_achievements_seen(tid=None, uid=None):
    """
    Set all earned achievements from a team or user seen.

    Args:
        tid: the team id
        uid: the user id
    """
    db = api.db.get_conn()

    match = {}

    if tid is not None:
        match.update({"tid": tid})
    elif uid is not None:
        match.update({"uid": uid})
    else:
        raise InternalException("You must specify either a tid or uid")

    db.earned_achievements.update(match, {"$set": {"seen": True}}, multi=True)


def get_earned_achievements_display(tid=None, uid=None):
    """
    Get the achievement display for a given user/team.

    Includes instance specific information.

    Args:
        tid: The team id
        tid: The user id
    Returns:
        A list of enabled achievements the team has earned.
    """
    instance_achievements = get_earned_achievement_instances(tid=tid, uid=uid)
    set_earned_achievements_seen(tid=tid, uid=uid)

    for instance_achievement in instance_achievements:
        achievement = get_achievement(instance_achievement["aid"])

        # Make sure not to override name or description.
        achievement.pop("name")
        achievement.pop("description")

        instance_achievement.update(achievement)

        # Make sure to remove sensitive data
        instance_achievement.pop("data", None)

    return instance_achievements


def get_earned_achievements(tid=None, uid=None):
    """
    Get the solved achievements for a given team or user.

    Args:
        tid: The team id
        tid: The user id
    Returns:
        List of solved achievement dictionaries
    """
    achievements = get_earned_achievement_instances(tid=tid, uid=uid)
    set_earned_achievements_seen(tid=tid, uid=uid)

    for achievement in achievements:
        achievement.update(get_achievement(achievement["aid"]))
        achievement.pop("data")

    return achievements


def get_processor(aid):
    """
    Return the processor module for a given achievement.

    Args:
        aid: the achievement id
    Returns:
        The processor module

    """
    try:
        path = get_achievement(aid)["processor"]
        base_path = api.config.get_settings(
        )["achievements"]["processor_base_path"]
        return SourceFileLoader(path[:-3], join(base_path, path)).load_module()
    except FileNotFoundError:
        raise InternalException("Achievement processor is offline.")


@api.logger.log_action
def process_achievement(aid, data):
    """
    Determine whether or not an achievement has been earned.

    Should not be called directly.

    Args:
        aid: the achievement id
        data: additional data dictionary
    """
    if data.get("uid", None) is None:
        data["uid"] = api.user.get_user()["uid"]

    if data.get("tid", None) is None:
        data["tid"] = api.user.get_user(uid=data["uid"])["tid"]

    get_achievement(aid=aid)
    processor = get_processor(aid)

    return processor.process(api, data)


def insert_earned_achievement(aid, data):
    """
    Store earned achievement for a user/team.

    Args:
        aid: the achievement id
        data: the data necessary to assess the achievement
              must include tid, uid
    """
    db = api.db.get_conn()

    tid, uid = data.pop("tid"), data.pop("uid")
    name, description = data.pop("name"), data.pop("description")

    db.earned_achievements.insert({
        "aid": aid,
        "tid": tid,
        "uid": uid,
        "data": data,
        "name": name,
        "description": description,
        "timestamp": datetime.utcnow().timestamp(),
        "seen": False
    })


def process_achievements(event, data):
    """
    Process achievements of a type with data.

    Args:
        event: event type, e.g., submit
        data: dictionary with additional information necessary for assessment
    """
    if data.get("uid", None) is None:
        data["uid"] = api.user.get_user()["uid"]

    if data.get("tid", None) is None:
        data["tid"] = api.user.get_user(uid=data["uid"])["tid"]

    eligible_achievements = [
        # @TODO clean this up
        achievement for achievement in get_all_achievements()
        if achievement["aid"] not in [
            earned_a['aid'] for earned_a in get_earned_achievements(
                data['tid'])]
        or achievement.get("multiple", False)
    ]

    for achievement in eligible_achievements:
        aid = achievement["aid"]

        acquired, instance_info = process_achievement(aid, data)

        info = {
            "name": achievement.get("name"),
            "description": achievement.get("description")
        }

        info.update(instance_info)
        data.update(info)
        if acquired:
            insert_earned_achievement(aid, data)


def insert_achievement(
        *ignore,
        name,
        score,
        description,
        processor,
        hidden,
        image,
        smallimage,
        disabled,
        multiple,
        ):
    """
    Insert an achievement object into the database.

    Kwargs:
        name: Name of the achievement.
        score: Point value of the achievement (positive integer).
        description: Description of the achievement.
        processor: Path to the achievement processor.
        hidden: Hide this achievement?
        image: Path to the achievement image.
        smallimage: Path to the achievement thumbnail.
        disabled: Disable this achievement?
        multiple: Allow earning multiple instances of this achievement?
    Returns:
        ID of the newly inserted achievement
    """
    db = api.db.get_conn()
    aid = api.common.token()
    db.achievements.insert_one({
        'aid': aid,
        'name': name,
        'description': description,
        'processor': processor,
        'hidden': hidden,
        'image': image,
        'smallimage': smallimage,
        'disabled': disabled,
        'multiple': multiple
    })
    return aid


def update_achievement(aid, updates):
    """
    Update a achievement with new properties.

    Args:
        aid: the aid of the achievement to update
        updates: dict of updated achievement fields

    Returns:
        aid of the updated achievement (unchanged), or
        None if the provided aid was not found

    """
    db = api.db.get_conn()
    success = db.achievements.find_one_and_update(
        {'aid': aid}, {'$set': updates})
    if not success:
        return None
    else:
        return aid
