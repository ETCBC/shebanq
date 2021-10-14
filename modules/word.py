from textwrap import dedent
import collections
import json

from gluon import current

from constants import ALWAYS
from helpers import collapseToRanges, hebKey, iDecode


class WORD:
    def __init__(self):
        pass

    def authRead(self, vr, lexicon_id):
        PASSAGE_DBS = current.PASSAGE_DBS

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

    def page(self, ViewSettings):
        Check = current.Check
        Caching = current.Caching

        pageConfig = ViewSettings.writeConfig()

        vr = Check.field("material", "", "version", default=False)
        if not vr:
            vr = ViewSettings.currentVersion()
        lan = Check.field("rest", "", "lan")
        letter = Check.field("rest", "", "letter")

        return Caching.get(
            f"words_page_{vr}_{lan}_{letter}_",
            lambda: self.page_c(pageConfig, vr, lan=lan, letter=letter),
            ALWAYS,
        )

    def page_c(self, pageConfig, vr, lan=None, letter=None):
        Caching = current.Caching

        (letters, words) = Caching.get(
            f"words_data_{vr}_", lambda: self.getData(vr), ALWAYS
        )

        return dict(
            version=vr,
            pageConfig=pageConfig,
            lan=lan,
            letter=letter,
            letters=letters,
            words=words.get(lan, {}).get(letter, []),
        )

    def body(self):
        """Retrieves a query word based on parameters.
        """
        Check = current.Check

        vr = Check.field("material", "", "version")
        iidRep = Check.field("material", "", "iid")

        (iid, keywords) = iDecode("w", iidRep)
        (authorized, msg) = self.authRead(vr, iid)
        msgs = []
        if not authorized:
            msgs.append(("error", msg))
            return dict(
                wordRecord=dict(),
                word=json.dumps(dict()),
                msgs=json.dumps(msgs),
            )
        wordRecord = self.getInfo(iid, vr, msgs)
        return dict(
            vr=vr,
            wordRecord=wordRecord,
            word=json.dumps(wordRecord),
            msgs=json.dumps(msgs),
        )

    def getItems(self, vr, chapter):
        PASSAGE_DBS = current.PASSAGE_DBS

        if vr not in PASSAGE_DBS:
            return []

        occurrences = PASSAGE_DBS[vr].executesql(
            dedent(
                f"""
                select anchor, lexicon_id
                from word_verse
                where anchor BETWEEN {chapter["first_m"]} AND {chapter["last_m"]}
                ;
                """
            )
        )
        lexemes = collections.defaultdict(lambda: [])

        for (slot, lexicon_id) in occurrences:
            lexemes[lexicon_id].append(slot)

        r = []
        if len(lexemes):
            lexiconIdsRep = ",".join(f"'{lexicon_id}'" for lexicon_id in lexemes)
            wordSql = dedent(
                f"""
                select * from lexicon where id in ({lexiconIdsRep})
                ;
                """
            )
            wordRecords = sorted(
                PASSAGE_DBS[vr].executesql(wordSql, as_dict=True),
                key=lambda x: hebKey(x["entryid_heb"]),
            )
            for w in wordRecords:
                r.append({"item": w, "slots": json.dumps(lexemes[w["id"]])})
        return r

    def read(self, vr, lexicon_id):
        PASSAGE_DBS = current.PASSAGE_DBS
        rows = (
            PASSAGE_DBS[vr].executesql(
                dedent(
                    f"""
                    select anchor
                    from word_verse
                    where lexicon_id = '{lexicon_id}' order by anchor
                    ;
                    """
                )
            )
            if vr in PASSAGE_DBS
            else []
        )
        return collapseToRanges(row[0] for row in rows)

    def getPlainInfo(self, vr, lexicon_id):
        PASSAGE_DBS = current.PASSAGE_DBS
        if vr not in PASSAGE_DBS:
            return {}

        records = PASSAGE_DBS[vr].executesql(
            dedent(
                f"""
                select * from lexicon where id = '{lexicon_id}'
                ;
                """
            ),
            as_dict=True,
        )
        return records[0] if records else {}

    def getInfo(self, iid, vr, msgs):
        PASSAGE_DBS = current.PASSAGE_DBS
        VERSIONS = current.VERSIONS

        sql = dedent(
            f"""
            select * from lexicon where id = '{iid}'
            ;
            """
        )
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
        PASSAGE_DBS = current.PASSAGE_DBS

        if vr not in PASSAGE_DBS:
            return ({}, {})
        hebrewData = sorted(
            PASSAGE_DBS[vr].executesql(
                dedent(
                    """
                    select id, entry_heb, entryid_heb, lan, gloss from lexicon
                    ;
                    """
                )
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
