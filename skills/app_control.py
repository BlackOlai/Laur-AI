# Placeholder skill for app_control
# This module satisfies imports expecting 'skills.app_control'.
# It defines minimal interface with KEYWORDS and execute.

KEYWORDS = []

def execute(query, say, takeCommand, context=None):
    """Dummy execute function that does nothing.
    Returns False to indicate the skill does not handle the query.
    """
    return False
