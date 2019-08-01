"""
Module for dealing with events.

An event, typically a competition, has associated eligibility criteria.
A team is initially eligible for any events for which its founding member
is eligibile.

When a new member joins the team, the team's eligibility for a given event
will be revoked if the new member does not fit its criteria.
(However, by default, members are prevented from joining a team if doing
so would cause the team to lose any existing eligibility status.)

Events can also have certain metadata, such as a sponsor, logo, etc.
"""

import api


def get_all_events():
    """Return a list of all events in the database."""
    db = api.db.get_conn()
    events = db.events.find({}, {'_id': False})
    if not events:
        return []
    else:
        return list(events)


def get_event(eid):
    """Return an event from the database, or None if it does not exist."""
    db = api.db.get_conn()
    return db.events.find_one({'eid': eid}, {'_id': False})


def add_event(name, eligibility_conditions="", sponsor=None, logo=None):
    """
    Add an event to the database.

    Args:
        name (str): name of the event
        eligibility_conditions (str): mongodb query to find eligible users
        sponsor (str): optional, sponsor of the event
        logo (str): optional, URL of a logo image for the event

    Returns:
        ID of the newly created event
    """
    db = api.db.get_conn()
    eid = api.common.token()
    db.events.insert({
        "eid": eid,
        "name": name,
        "eligibility_conditions": eligibility_conditions,
        "sponsor": sponsor,
        "logo": logo,
    })
    return eid


def is_eligible(user, event):
    """Determine whether a given user is eligible for an event."""
    search_query = event['eligibility_conditions']
    search_query['uid'] = user['uid']
    db = api.db.get_conn()
    return db.users.find_one(search_query) is not None
