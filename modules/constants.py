import datetime


NULLDT = "____-__-__ __:__:__"
PUBLISH_FREEZE = datetime.timedelta(weeks=1)
PUBLISH_FREEZE_MSG = "1 week"

TPS = dict(
    o=("organization", "organization"), p=("project", "project"), q=("query", "query")
)

NOTFILLFIELDS = {"word_phono", "word_phono_sep"}
