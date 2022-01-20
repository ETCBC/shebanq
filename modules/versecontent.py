from textwrap import dedent
import xml.etree.ElementTree as ET

from gluon import current

from constants import NOTFILLFIELDS
from blang import BOOK_TRANS
from boiler import FIELDNAMES, TEXT_TPL
from helpers import hEsc


class VERSECONTENT:
    """Handle a single verse.

    It can retrieve word data from the database
    and render it in various textual formats.
    """

    def __init__(
        self,
        vr,
        book_name,
        chapter_num,
        verse_num,
        xml=None,
        wordData=None,
        tp=None,
        tr=None,
        mr=None,
        lang="en",
    ):
        self.version = vr
        self.tp = tp
        self.tr = tr
        self.mr = mr
        self.lang = lang
        self.book_name = book_name
        self.chapter_num = chapter_num
        self.verse_num = verse_num
        self.xml = xml
        self.wordData = wordData
        self.process()

    def process(self):
        vr = self.version
        book_name = self.book_name
        chapter_num = self.chapter_num
        verse_num = self.verse_num
        xml = self.xml
        wordData = self.wordData

        if xml is None:
            xml = ""

        PASSAGE_DBS = current.PASSAGE_DBS
        passageDb = PASSAGE_DBS.get(vr, None)
        if wordData is None and passageDb:
            fieldNames = ",".join(FIELDNAMES["txtd"])
            wsql = dedent(
                f"""
                select {fieldNames}, lexicon_id from word
                inner join word_verse on word_number = word_verse.anchor
                inner join verse on verse.id = word_verse.verse_id
                inner join chapter on verse.chapter_id = chapter.id
                inner join book on chapter.book_id = book.id
                where book.name = '{book_name}'
                and chapter.chapter_num = {chapter_num}
                and verse.verse_num = {verse_num}
                order by word_number
                ;
                """
            )
            wordRecords = passageDb.executesql(wsql, as_dict=True) if passageDb else []
            wordData = []
            for record in wordRecords:
                wordData.append(
                    dict(
                        (
                            (
                                x,
                                hEsc(
                                    str(y),
                                    not (x.endswith("_border") or x in NOTFILLFIELDS),
                                ),
                            )
                            for (x, y) in record.items()
                        ),
                    )
                )
        self.xml = xml
        self.wordData = wordData
        self.words = []

    def label(self):
        return (
            BOOK_TRANS[self.lang][self.book_name].replace("_", " "),
            self.book_name,
            self.chapter_num,
            self.verse_num,
        )

    def getWords(self):
        if len(self.words) == 0:
            root = ET.fromstring(f"<verse>{self.xml}</verse>".encode("utf-8"))
            i = 0
            for child in root:
                slotid = int(child.attrib["m"])
                lexicon_id = child.attrib["l"]
                text = "" if child.text is None else child.text
                thisWordData = self.wordData[i]
                phonoText = thisWordData["word_phono"]
                phonoSep = thisWordData["word_phono_sep"]
                trailer = child.get("t", "")
                self.words.append(
                    (slotid, lexicon_id, text, trailer, phonoText, phonoSep)
                )
                i += 1
        return self.words

    def material(self):
        if self.tp == "txtp":
            return self.plainText()
        elif self.tp == "txt1":
            return self.tab1Text()
        elif self.tp == "txt2":
            return self.tab2Text()
        elif self.tp == "txt3":
            return self.tab3Text()
        elif self.tp == "txtd":
            return self.dataText()

    def plainText(self):
        """Present text in plain Hebrew or plain phonetic text.

        See [∈ text-representation][elem-text-representation]
        """
        material = []
        for word in self.getWords():
            if self.tr == "hb":
                wordText = word[2]
                sep = word[3]
            elif self.tr == "ph":
                wordText = word[4]
                sep = word[5]
            material.append(
                f"""<span m="{word[0]}" l="{word[1]}">{wordText}</span>{sep}"""
            )
        return "".join(material)

    def dataText(self):
        """Present text in data format.

        Linguistic features of the words will be shown,
        according to the current settings of the legend.

        See [∈ legend][elem-feature-legend], [∈ show-verse-data][elem-show-verse-data]
        """
        material = []
        for word in self.wordData:
            material.append(TEXT_TPL.format(**word))
        return "".join(material)

    def tab1Text(self):
        """Present text in a table, mode 1.

        Mode 1 is notes view, i.e. notes are viewed
        interlinear with the clause atoms.

        See [∈ text-presentation][elem-text-presentation]
        """
        material = ["""<table class="t1_table">"""]
        curNum = (0, 0, 0)
        curClauseAtom = []
        for word in self.wordData:
            thisNum = (
                word["sentence_number"],
                word["clause_number"],
                word["clause_atom_number"],
            )
            if thisNum != curNum:
                material.append(self.putClauseAtom1(curClauseAtom))
                curClauseAtom = []
                curNum = thisNum
            curClauseAtom.append(word)
        material.append(self.putClauseAtom1(curClauseAtom))
        material.append("</table>")
        return "".join(material)

    def tab2Text(self):
        """Present text in a table, mode 2.

        Mode 2 is syntactic view, i.e. indentation is used to
        represent linguistic embedding.

        See [∈ text-presentation][elem-text-presentation]
        """
        material = ['<dl class="lv2">']
        curNum = (0, 0, 0)
        curClauseAtom = []
        for word in self.wordData:
            thisNum = (
                word["sentence_number"],
                word["clause_number"],
                word["clause_atom_number"],
            )
            if thisNum != curNum:
                material.append(self.putClauseAtom2(curClauseAtom))
                curClauseAtom = []
                curNum = thisNum
            curClauseAtom.append(word)
        material.append(self.putClauseAtom2(curClauseAtom))
        material.append("</dl>")
        return "".join(material)

    def tab3Text(self):
        """Present text in a table, mode 3.

        Mode 3 is abstract view, i.e. letters are replaced by
        abstract symbols, where many letters map to the same symbol.
        represent linguistic embedding.

        See [∈ text-presentation][elem-text-presentation]
        """
        material = ['<dl class="lv3">']
        curNum = (0, 0, 0)
        curClauseAtom = []
        for word in self.wordData:
            thisNum = (
                word["sentence_number"],
                word["clause_number"],
                word["clause_atom_number"],
            )
            if thisNum != curNum:
                material.append(self.putClauseAtom3(curClauseAtom))
                curClauseAtom = []
                curNum = thisNum
            curClauseAtom.append(word)
        material.append(self.putClauseAtom3(curClauseAtom))
        material.append("</dl>")
        return "".join(material)

    def putClauseAtom1(self, words):
        if len(words) == 0:
            return ""
        textType = words[0]["clause_txt"].replace("?", "")
        clauseType = words[0]["clause_typ"]
        tabN = int(words[0]["clause_atom_tab"])
        clauseAtomNumber = int(words[0]["clause_atom_number"])
        tab10s = int(tabN // 10)
        tab10r = tabN % 10
        smalltab = "&lt;" * tab10r
        bigtab = "&lt;" * tab10s
        result = [
            dedent(
                f"""
                <tr clause_atom="{clauseAtomNumber}">
                    <td colspan="3" class="t1_txt">
                """
            )
        ]
        for word in words:
            if "r" in word["phrase_border"]:
                result.append(
                    dedent(
                        f"""<span class="t1_phf1"
                    >{word["phrase_function"]}</span><span
                    class="t1_phfn">{word["phrase_number"]}</span>"""
                    )
                )
            if self.tr == "hb":
                wordText = word["word_heb"]
            elif self.tr == "ph":
                wordText = word["word_phono"] + word["word_phono_sep"]
            result.append(
                f"""<span m="{word["word_number"]}" l="{word["lexicon_id"]}">"""
                f"""{wordText}</span>"""
            )
        result.append(
            dedent(
                f"""
                </td>
                <td class="t1_tb1">{smalltab}</td>
                <td class="t1_tb10">{bigtab}</td>
                <td class="t1_txttp">{textType}</td>
                <td class="t1_ctp">{clauseType}</td>
                </tr>
                """
            )
        )
        return "".join(result)

    def putClauseAtom2(self, words):
        if len(words) == 0:
            return ""
        textType = words[0]["clause_txt"]
        clauseType = words[0]["clause_typ"]
        code = words[0]["clause_atom_code"]
        tabN = int(words[0]["clause_atom_tab"])
        tab = '<span class="fa">&#xf060;</span>' * tabN  # arrow-left
        result = [
            dedent(
                f"""<dt class="lv2"><span class="ctxt2"
                >{textType}</span>
                <span class="ctp2">{clauseType}</span> <span class="ccode2"
                >{code}</span></dt><dd class="lv2"
            ><span class="tb2">{tab}</span>&nbsp;"""
            )
        ]
        for word in words:
            if "r" in word["phrase_border"]:
                result.append(f' <span class="phf2">{word["phrase_function"]}</span> ')
            if self.tr == "hb":
                wordText = word["word_heb"]
            elif self.tr == "ph":
                wordText = word["word_phono"] + word["word_phono_sep"]
            result.append(
                f"""<span m="{word["word_number"]}" l="{word["lexicon_id"]}">"""
                f"{wordText}</span> "
            )
        result.append("</dd>")
        return "".join(result)

    def putClauseAtom3(self, words):
        if len(words) == 0:
            return ""
        tabN = int(words[0]["clause_atom_tab"])
        tab = '<span class="fa">&#xf060;</span>' * tabN  # arrow-left
        result = [
            f'<dt class="lv3"><span class="tb3">{tab}</span></dt><dd class="lv3">'
        ]
        phrb_table = dict(
            rr="&nbsp;",  # arrow-circle-right
            r='<span class="fa">&#xf105;</span>',  # arrow-circle-o-left
            l='<span class="fa">&#xf104;</span>',  # arrow-circle-o-right
            ll="&nbsp;",  # arrow-circle-left,
        )
        for word in words:
            phraseBorders = word["phrase_border"].split()
            borderSymStart = ""
            borderSymEnd = ""
            for phraseBorder in phraseBorders:
                borderSymbols = phrb_table.get(phraseBorder, "")
                if "r" in phraseBorder:
                    borderSymStart = borderSymbols
                elif "l" in phraseBorder:
                    borderSymEnd = borderSymbols
            if word["word_lex"] == "H":
                textSymbol = "0d9"  # caret-left
            elif word["word_lex"] == "W":
                textSymbol = "0d8"  # caret-up
            elif word["word_lex"] == "&gt;LHJM/":
                textSymbol = "0ed"  #
            elif word["word_lex"] == "JHWH/":
                textSymbol = "0ee"  #
            elif word["word_pos"] == "nmpr":
                if word["word_gender"] == "m":
                    textSymbol = "222"  # mars
                elif word["word_gender"] == "f":
                    textSymbol = "221"  # venus
                elif word["word_gender"] == "NA":
                    textSymbol = "1db"  # genderless
                elif word["word_gender"] == "unknown":
                    textSymbol = "1db"  # genderless
            elif word["word_pos"] == "verb":
                textSymbol = "013"  # cog
            elif word["word_pos"] == "subs":
                textSymbol = "146"  # minus-square
            else:
                textSymbol = "068"  # minus
            result.append(
                f"""{borderSymStart}<span
m="{word["word_number"]}" l="{word["lexicon_id"]}"
><span class="fa">&#xf{textSymbol};</span></span>{borderSymEnd}"""
            )
        result.append("</dd>")
        return "".join(result)
