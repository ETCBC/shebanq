import xml.etree.ElementTree as ET

from constants import NOTFILLFIELDS
from blang import booktrans
from boiler import FIELDNAMES, TEXT_TPL
from helpers import h_esc


class Verse:
    def __init__(
        self,
        passage_dbs,
        vr,
        book_name,
        chapter_num,
        verse_num,
        xml=None,
        word_data=None,
        tp=None,
        tr=None,
        mr=None,
        lang="en",
    ):
        self.version = vr
        passage_db = passage_dbs[vr] if vr in passage_dbs else None
        self.tp = tp
        self.tr = tr
        self.mr = mr
        self.lang = lang
        self.book_name = book_name
        self.chapter_num = chapter_num
        self.verse_num = verse_num
        if xml is None:
            xml = ""
        if word_data is None:
            fnames = ",".join(FIELDNAMES["txt_il"])
            wsql = f"""
select {fnames}, lexicon_id from word
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
            word_records = (
                passage_db.executesql(wsql, as_dict=True) if passage_db else []
            )
            word_data = []
            for record in word_records:
                word_data.append(
                    dict(
                        (
                            (
                                x,
                                h_esc(
                                    str(y),
                                    not (x.endswith("_border") or x in NOTFILLFIELDS),
                                ),
                            )
                            for (x, y) in record.items()
                        ),
                    )
                )
        self.xml = xml
        self.word_data = word_data
        self.words = []

    # def chapter_link(self): return (self.book_name, self.chapter_num)
    # def verse_link(self): return (self.book_name, self.chapter_num, self.verse_num)

    def label(self):
        return (
            booktrans[self.lang][self.book_name].replace("_", " "),
            self.book_name,
            self.chapter_num,
            self.verse_num,
        )

    def get_words(self):
        if len(self.words) == 0:
            root = ET.fromstring(f"<verse>{self.xml}</verse>".encode("utf-8"))
            i = 0
            for child in root:
                monad_id = int(child.attrib["m"])
                lex_id = child.attrib["l"]
                text = "" if child.text is None else child.text
                wdata = self.word_data[i]
                phtext = wdata["word_phono"]
                phsep = wdata["word_phono_sep"]
                trailer = child.get("t", "")
                self.words.append((monad_id, lex_id, text, trailer, phtext, phsep))
                i += 1
        return self.words

    def material(self, user_agent):
        if self.tp == "txt_p":
            return self._plain_text(user_agent)
        elif self.tp == "txt_tb1":
            return self._tab1_text(user_agent)
        elif self.tp == "txt_tb2":
            return self._tab2_text(user_agent)
        elif self.tp == "txt_tb3":
            return self._tab3_text(user_agent)
        elif self.tp == "txt_il":
            return self._rich_text(user_agent)

    def _plain_text(self, user_agent):
        material = []
        for word in self.get_words():
            if self.tr == "hb":
                # no longer needed because the browser now render Hebrew text properly
                # atext = adapted_text(word[2], user_agent)
                atext = word[2]
                sep = word[3]
            elif self.tr == "ph":
                atext = word[4]
                sep = word[5]
            material.append(
                f"""<span m="{word[0]}" l="{word[1]}">{atext}</span>{sep}"""
            )
        return "".join(material)

    def _rich_text(self, user_agent):
        material = []
        for word in self.word_data:
            material.append(TEXT_TPL.format(**word))
        return "".join(material)

    def _tab1_text(self, user_agent):
        material = ["""<table class="t1_table">"""]
        curnum = (0, 0, 0)
        curca = []
        for word in self.word_data:
            thisnum = (
                word["sentence_number"],
                word["clause_number"],
                word["clause_atom_number"],
            )
            if thisnum != curnum:
                material.append(self._putca1(curca))
                curca = []
                curnum = thisnum
            curca.append(word)
        material.append(self._putca1(curca))
        material.append("</table>")
        return "".join(material)

    def _tab2_text(self, user_agent):
        material = ['<dl class="lv2">']
        curnum = (0, 0, 0)
        curca = []
        for word in self.word_data:
            thisnum = (
                word["sentence_number"],
                word["clause_number"],
                word["clause_atom_number"],
            )
            if thisnum != curnum:
                material.append(self._putca2(curca))
                curca = []
                curnum = thisnum
            curca.append(word)
        material.append(self._putca2(curca))
        material.append("</dl>")
        return "".join(material)

    def _tab3_text(self, user_agent):
        material = ['<dl class="lv3">']
        curnum = (0, 0, 0)
        curca = []
        for word in self.word_data:
            thisnum = (
                word["sentence_number"],
                word["clause_number"],
                word["clause_atom_number"],
            )
            if thisnum != curnum:
                material.append(self._putca3(curca))
                curca = []
                curnum = thisnum
            curca.append(word)
        material.append(self._putca3(curca))
        material.append("</dl>")
        return "".join(material)

    def _putca1(self, words):
        if len(words) == 0:
            return ""
        txttp = words[0]["clause_txt"].replace("?", "")
        ctp = words[0]["clause_typ"]
        tabn = int(words[0]["clause_atom_tab"])
        canr = int(words[0]["clause_atom_number"])
        # tab = '<span class="fa fa-plus-square">&#xf0fe;</span>' * tabn # plus square
        # tab = '&gt;' * tabn # plus square
        tab10s = int(tabn // 10)
        tab10r = tabn % 10
        smalltab = "&lt;" * tab10r
        bigtab = "&lt;" * tab10s
        result = [
            f"""
<tr canr="{canr}">
    <td colspan="3" class="t1_txt">
"""
        ]
        for word in words:
            if "r" in word["phrase_border"]:
                result.append(
                    f"""<span class="t1_phf1"
>{word["phrase_function"]}</span><span class="t1_phfn">{word["phrase_number"]}</span>"""
                )
            if self.tr == "hb":
                wtext = word["word_heb"]
            elif self.tr == "ph":
                wtext = word["word_phono"] + word["word_phono_sep"]
            result.append(
                f"""<span m="{word["word_number"]}" l="{word["lexicon_id"]}">"""
                f"""{wtext}</span>"""
            )
        result.append(
            f"""
    </td>
    <td class="t1_tb1">{smalltab}</td>
    <td class="t1_tb10">{bigtab}</td>
    <td class="t1_txttp">{txttp}</td>
    <td class="t1_ctp">{ctp}</td>
</tr>
"""
        )
        return "".join(result)

    def _putca2(self, words):
        if len(words) == 0:
            return ""
        txt = words[0]["clause_txt"]
        ctp = words[0]["clause_typ"]
        code = words[0]["clause_atom_code"]
        tabn = int(words[0]["clause_atom_tab"])
        tab = '<span class="fa">&#xf060;</span>' * tabn  # arrow-left
        result = [
            f"""<dt class="lv2"><span class="ctxt2"
            >{txt}</span> <span class="ctp2">{ctp}</span> <span class="ccode2"
            >{code}</span></dt><dd class="lv2"
            ><span class="tb2">{tab}</span>&nbsp;"""
        ]
        for word in words:
            if "r" in word["phrase_border"]:
                result.append(
                    f' <span class="phf2">{word["phrase_function"]}</span> '
                )
            if self.tr == "hb":
                wtext = word["word_heb"]
            elif self.tr == "ph":
                wtext = word["word_phono"] + word["word_phono_sep"]
            result.append(
                f"""<span m="{word["word_number"]}" l="{word["lexicon_id"]}">"""
                f"{wtext}</span> "
            )
        result.append("</dd>")
        return "".join(result)

    def _putca3(self, words):
        if len(words) == 0:
            return ""
        tabn = int(words[0]["clause_atom_tab"])
        tab = '<span class="fa">&#xf060;</span>' * tabn  # arrow-left
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
            phrbs = word["phrase_border"].split()
            phrbsymb = ""
            phrbsyme = ""
            for phrb in phrbs:
                phrbsym = phrb_table.get(phrb, "")
                if "r" in phrb:
                    phrbsymb = phrbsym
                elif "l" in phrb:
                    phrbsyme = phrbsym
            if word["word_lex"] == "H":
                txtsym = "0d9"  # caret-left
            elif word["word_lex"] == "W":
                txtsym = "0d8"  # caret-up
            elif word["word_lex"] == "&gt;LHJM/":
                txtsym = "0ed"  #
            elif word["word_lex"] == "JHWH/":
                txtsym = "0ee"  #
            elif word["word_pos"] == "nmpr":
                if word["word_gender"] == "m":
                    txtsym = "222"  # mars
                elif word["word_gender"] == "f":
                    txtsym = "221"  # venus
                elif word["word_gender"] == "NA":
                    txtsym = "1db"  # genderless
                elif word["word_gender"] == "unknown":
                    txtsym = "1db"  # genderless
            elif word["word_pos"] == "verb":
                txtsym = "013"  # cog
            elif word["word_pos"] == "subs":
                txtsym = "146"  # minus-square
            else:
                txtsym = "068"  # minus
            result.append(
                f"""{phrbsymb}<span m="{word["word_number"]}" l="{word["lexicon_id"]}"
><span class="fa">&#xf{txtsym};</span></span>{phrbsyme}"""
                )
        result.append("</dd>")
        return "".join(result)
