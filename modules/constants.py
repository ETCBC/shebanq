import datetime

# cache expire times
ALWAYS = None
ONE_DAY = 24 * 3600
ONE_HOUR = 3600

NULLDT = "____-__-__ __:__:__"
"""Empty date time representation.
"""

PUBLISH_FREEZE = datetime.timedelta(weeks=1)
"""Time interval after which publishing is irrevocable.
"""

PUBLISH_FREEZE_MSG = "1 week"

TPS = dict(
    o=("organization", "organization"), p=("project", "project"), q=("query", "query")
)
"""Types of records in query tree view.
"""

NOTFILLFIELDS = {"word_phono", "word_phono_sep"}
"""Fields that, when represented in HTML, should not be filled with a
non breaking space when empty.
"""
