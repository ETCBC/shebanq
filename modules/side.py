from viewdefs import colorPicker
from helpers import debug


class SIDE:
    def __init__(self, Caching, Material, Word, Query, Note):
        self.Caching = Caching
        self.Material = Material
        self.Word = Word
        self.Query = Query
        self.Note = Note

    def get(self, vr, qw, bk, ch, is_published):
        Caching = self.Caching

        return Caching.get(
            f"items_{qw}_{vr}_{bk}_{ch}_{is_published}_",
            lambda: self.get_c(vr, qw, bk, ch, is_published),
            None,
        )

    def get_c(self, vr, qw, bk, ch, is_published):
        Material = self.Material
        Word = self.Word
        Query = self.Query
        Note = self.Note

        (book, chapter) = Material.getPassage(vr, bk, ch)
        if not chapter:
            result = dict(
                colorPicker=colorPicker,
                sideItems=[],
                qw=qw,
            )
        else:
            if qw == "q":
                debug(f"original function PUB={is_published}")
                slotSets = Query.getItems(vr, chapter, is_published == "v")
                sideItems = Query.group(vr, slotSets)
            elif qw == "w":
                slotSets = Word.getItems(vr, chapter)
                sideItems = Word.group(vr, slotSets)
            elif qw == "n":
                sideItems = Note.getItems(vr, book, chapter, is_published)
            else:
                sideItems = []
            result = dict(
                colorPicker=colorPicker,
                sideItems=sideItems,
                qw=qw,
            )
        return result
