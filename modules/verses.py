import collections

from constants import NOTFILLFIELDS
from boiler import FIELDNAMES
from helpers import h_esc
from verse import Verse


class Verses:
    def __init__(
        self,
        passage_dbs,
        vr,
        mr,
        verse_ids=None,
        chapter=None,
        tp=None,
        tr=None,
        lang="en",
    ):
        if tr is None:
            tr = "hb"
        self.version = vr
        passage_db = passage_dbs[vr] if vr in passage_dbs else None
        self.mr = mr
        self.tp = tp
        self.tr = tr
        self.verses = []
        if self.mr == "r" and (verse_ids is None or len(verse_ids) == 0):
            return
        verse_ids_str = (
            ",".join((str(v) for v in verse_ids)) if verse_ids is not None else None
        )
        cfield = "verse.id"
        cwfield = "word_verse.verse_id"
        condition_pre = (
            f"""
where {{}} in ({verse_ids_str})
"""
            if verse_ids is not None
            else f"""
where chapter_id = {chapter}
"""
            if chapter is not None
            else ""
        )
        condition = condition_pre.format(cfield)
        wcondition = condition_pre.format(cwfield)

        verse_info = (
            passage_db.executesql(
                f"""
select
    verse.id,
    book.name,
    chapter.chapter_num,
    verse.verse_num
    {", verse.xml" if tp == "txt_p" else ""}
from verse
inner join chapter on verse.chapter_id=chapter.id
inner join book on chapter.book_id=book.id
{condition}
order by verse.id
;
"""
            )
            if passage_db
            else []
        )

        word_records = []
        word_records = (
            passage_db.executesql(
                f"""
select {",".join(FIELDNAMES[tp])}, verse_id, lexicon_id from word
inner join word_verse on word_number = word_verse.anchor
inner join verse on verse.id = word_verse.verse_id
{wcondition}
order by word_number
;
""",
                as_dict=True,
            )
            if passage_db
            else []
        )

        word_data = collections.defaultdict(lambda: [])
        for record in word_records:
            word_data[record["verse_id"]].append(
                dict(
                    (
                        x,
                        h_esc(
                            str(y), not (x.endswith("_border") or x in NOTFILLFIELDS)
                        ),
                    )
                    for (x, y) in record.items()
                )
            )

        for v in verse_info:
            v_id = int(v[0])
            xml = v[4] if tp == "txt_p" else ""
            self.verses.append(
                Verse(
                    passage_dbs,
                    vr,
                    v[1],
                    v[2],
                    v[3],
                    xml=xml,
                    word_data=word_data[v_id],
                    tp=tp,
                    tr=tr,
                    mr=mr,
                    lang=lang,
                )
            )
