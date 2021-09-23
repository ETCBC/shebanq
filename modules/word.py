import collections
import json

from helpers import collapseToRanges, hebKey


class WORD:
    def __init__(self, Caching, PASSAGE_DBS, VERSIONS):
        self.Caching = Caching
        self.PASSAGE_DBS = PASSAGE_DBS
        self.VERSIONS = VERSIONS

    def authRead(self, vr, lexicon_id):
        PASSAGE_DBS = self.PASSAGE_DBS

        authorized = None
        if not lexicon_id or vr not in PASSAGE_DBS:
            authorized = False
        else:
            wordRecord = self.getPlainInfo(vr, lexicon_id)
            if wordRecord:
                authorized = True
        msg = (
            f"No word with id {lexicon_id}"
            if authorized is None
            else f"No data version {vr}"
            if vr not in PASSAGE_DBS
            else ""
        )
        return (authorized, msg)

    def getItems(self, vr, chapter):
        PASSAGE_DBS = self.PASSAGE_DBS

        return (
            PASSAGE_DBS[vr].executesql(
                f"""
select anchor, lexicon_id
from word_verse
where anchor BETWEEN {chapter["first_m"]} AND {chapter["last_m"]}
;
"""
            )
            if vr in PASSAGE_DBS
            else []
        )

    def read(self, vr, lexicon_id):
        PASSAGE_DBS = self.PASSAGE_DBS
        slots = (
            PASSAGE_DBS[vr].executesql(
                f"""
select anchor from word_verse where lexicon_id = '{lexicon_id}' order by anchor
;
"""
            )
            if vr in PASSAGE_DBS
            else []
        )
        return collapseToRanges(slots)

    def group(self, vr, occurrences):
        PASSAGE_DBS = self.PASSAGE_DBS

        if vr not in PASSAGE_DBS:
            return []
        wordIds = collections.defaultdict(lambda: [])
        for x in occurrences:
            wordIds[x[1]].append(x[0])
        r = []
        if len(wordIds):
            wordIdsRep = ",".join("'{x}'" for x in wordIds)
            wordSql = f"""
select * from lexicon where id in ({wordIdsRep})
;
"""
            wordRecords = sorted(
                PASSAGE_DBS[vr].executesql(wordSql, as_dict=True),
                key=lambda x: hebKey(x["entryid_heb"]),
            )
            for w in wordRecords:
                r.append({"item": w, "slots": json.dumps(wordIds[w["id"]])})
        return r

    def getPlainInfo(self, vr, lexicon_id):
        PASSAGE_DBS = self.PASSAGE_DBS
        if vr not in PASSAGE_DBS:
            return {}

        records = PASSAGE_DBS[vr].executesql(
            f"""
select * from lexicon where id = '{lexicon_id}'
;
""",
            as_dict=True,
        )
        return records[0] if records else {}

    def getInfo(self, iid, vr, msgs):
        PASSAGE_DBS = self.PASSAGE_DBS
        VERSIONS = self.VERSIONS

        sql = f"""
select * from lexicon where id = '{iid}'
;
"""
        wordRecord = dict(id=iid, versions={})
        for v in VERSIONS:
            records = PASSAGE_DBS[v].executesql(sql, as_dict=True)
            if records is None:
                msgs.append(
                    ("error", f"Cannot lookup word with id {iid} in version {v}")
                )
            elif len(records) == 0:
                msgs.append(("warning", f"No word with id {iid} in version {v}"))
            else:
                wordRecord["versions"][v] = records[0]
        return wordRecord

    def getData(self, vr):
        PASSAGE_DBS = self.PASSAGE_DBS

        if vr not in PASSAGE_DBS:
            return ({}, {})
        hebrewData = sorted(
            PASSAGE_DBS[vr].executesql(
                """
select id, entry_heb, entryid_heb, lan, gloss from lexicon
;
"""
            ),
            key=lambda x: (x[3], hebKey(x[2])),
        )
        letters = dict(arc=[], hbo=[])
        words = dict(arc={}, hbo={})
        for (wid, e, eid, lan, gloss) in hebrewData:
            letter = ord(e[0])
            if letter not in words[lan]:
                letters[lan].append(letter)
                words[lan][letter] = []
            words[lan][letter].append((e, wid, eid, gloss))
        return (letters, words)

    def page(self, ViewSettings, vr, lan=None, letter=None):
        Caching = self.Caching

        return Caching.get(
            f"words_page_{vr}_{lan}_{letter}_",
            lambda: self.page_c(ViewSettings, vr, lan=lan, letter=letter),
            None,
        )

    def page_c(self, ViewSettings, vr, lan=None, letter=None):
        Caching = self.Caching

        (letters, words) = Caching.get(
            f"words_data_{vr}_", lambda: self.getData(vr), None
        )
        version = ViewSettings.theVersion()

        return dict(
            version=version,
            ViewSettings=ViewSettings,
            lan=lan,
            letter=letter,
            letters=letters,
            words=words.get(lan, {}).get(letter, []),
        )
