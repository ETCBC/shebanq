import collections

from constants import NOTFILLFIELDS
from boiler import FIELDNAMES
from helpers import hEsc
from verse import Verse


class Verses:
    def __init__(
        self,
        PASSAGE_DBS,
        vr,
        mr,
        verseIds=None,
        chapter=None,
        tp=None,
        tr=None,
        lang="en",
    ):
        if tr is None:
            tr = "hb"
        self.version = vr
        passageDb = PASSAGE_DBS[vr] if vr in PASSAGE_DBS else None
        self.mr = mr
        self.tp = tp
        self.tr = tr
        self.verses = []
        if self.mr == "r" and (verseIds is None or len(verseIds) == 0):
            return
        verseIdsStr = (
            ",".join((str(verse_id) for verse_id in verseIds))
            if verseIds is not None
            else None
        )
        verseIdField = "verse.id"
        wordVerseField = "word_verse.verse_id"
        conditionPre = (
            f"""
where {{}} in ({verseIdsStr})
"""
            if verseIds is not None
            else f"""
where chapter_id = {chapter}
"""
            if chapter is not None
            else ""
        )
        condition = conditionPre.format(verseIdField)
        wcondition = conditionPre.format(wordVerseField)

        verseInfo = (
            passageDb.executesql(
                f"""
select
    verse.id,
    book.name,
    chapter.chapter_num,
    verse.verse_num
    {", verse.xml" if tp == "txtp" else ""}
from verse
inner join chapter on verse.chapter_id=chapter.id
inner join book on chapter.book_id=book.id
{condition}
order by verse.id
;
"""
            )
            if passageDb
            else []
        )

        wordRecords = []
        wordRecords = (
            passageDb.executesql(
                f"""
select {",".join(FIELDNAMES[tp])}, verse_id, lexicon_id from word
inner join word_verse on word_number = word_verse.anchor
inner join verse on verse.id = word_verse.verse_id
{wcondition}
order by word_number
;
""",
                asDict=True,
            )
            if passageDb
            else []
        )

        wordData = collections.defaultdict(lambda: [])
        for record in wordRecords:
            wordData[record["verse_id"]].append(
                dict(
                    (
                        x,
                        hEsc(str(y), not (x.endswith("_border") or x in NOTFILLFIELDS)),
                    )
                    for (x, y) in record.items()
                )
            )

        for verse in verseInfo:
            verse_id = int(verse[0])
            xml = verse[4] if tp == "txtp" else ""
            self.verses.append(
                Verse(
                    PASSAGE_DBS,
                    vr,
                    verse[1],
                    verse[2],
                    verse[3],
                    xml=xml,
                    wordData=wordData[verse_id],
                    tp=tp,
                    tr=tr,
                    mr=mr,
                    lang=lang,
                )
            )
