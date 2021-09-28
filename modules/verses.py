import json

from gluon import current

from versecontent import VerseContent


class VERSES:
    def __init__(self):
        pass

    def get(self):
        extension = current.request.extension

        if extension == "json":
            return self.getJson()

        Check = current.Check
        Caching = current.Caching

        vr = Check.field("material", "", "version")
        bk = Check.field("material", "", "book")
        ch = Check.field("material", "", "chapter")
        vs = Check.field("material", "", "verse")
        tr = Check.field("material", "", "tr")

        if vs is None:
            return dict(good=False, msgs=[])

        return Caching.get(
            f"verse_{vr}_{bk}_{ch}_{vs}_{tr}_",
            lambda: self.get_c(vr, bk, ch, vs, tr),
            None,
        )

    def get_c(self, vr, bk, ch, vs, tr):
        PASSAGE_DBS = current.PASSAGE_DBS

        material = VerseContent(
            PASSAGE_DBS,
            vr,
            bk,
            ch,
            vs,
            xml=None,
            wordData=None,
            tp="txtd",
            tr=tr,
            mr=None,
        )
        good = True
        msgs = []
        if len(material.wordData) == 0:
            msgs = [("error", f"{bk} {ch}:{vs} does not exist")]
            good = False
        return dict(
            good=good,
            msgs=msgs,
            material=material,
        )

    def getJson(self, vr, bk, ch, vs):
        Caching = current.Caching

        return Caching.get(
            f"versej_{vr}_{bk}_{ch}_{vs}_",
            lambda: self.getJson_c(vr, bk, ch, vs),
            None,
        )

    def getJson_c(self):
        Check = current.Check
        PASSAGE_DBS = current.PASSAGE_DBS

        vr = Check.field("material", "", "version")
        bk = Check.field("material", "", "book")
        ch = Check.field("material", "", "chapter")
        vs = Check.field("material", "", "verse")

        passageDb = PASSAGE_DBS[vr] if vr in PASSAGE_DBS else None
        msgs = []
        good = True
        data = dict()
        if passageDb is None:
            msgs.append(("Error", f"No such version: {vr}"))
            good = False
        if good:
            verseInfo = passageDb.executesql(
                f"""
select verse.id, verse.text from verse
inner join chapter on verse.chapter_id=chapter.id
inner join book on chapter.book_id=book.id
where book.name = '{bk}' and chapter.chapter_num = {ch} and verse_num = {vs}
;
"""
            )
            if len(verseInfo) == 0:
                msgs.append(("Error", f"No such verse: {bk} {ch}:{vs}"))
                good = False
            else:
                data = verseInfo[0]
                vid = data[0]
                wordInfo = passageDb.executesql(
                    f"""
select word.word_phono, word.word_phono_sep
from word
inner join word_verse on word_number = word_verse.anchor
inner join verse on verse.id = word_verse.verse_id
where verse.id = {vid}
order by word_number
;
"""
                )
                data = dict(
                    text=data[1], phonetic="".join(x[0] + x[1] for x in wordInfo)
                )
        return json.dumps(dict(good=good, msgs=msgs, data=data), ensure_ascii=False)
