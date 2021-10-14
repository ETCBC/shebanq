from gluon import current

from constants import ONE_HOUR


class SIDE:
    def __init__(self, Material, Word, Query, Note):
        self.Material = Material
        self.Word = Word
        self.Query = Query
        self.Note = Note

    def page(self):
        Check = current.Check

        vr = Check.field("material", "", "version")
        qw = Check.field("material", "", "qw")
        bk = Check.field("material", "", "book")
        ch = Check.field("material", "", "chapter")
        is_published = Check.field("highlights", qw, "pub") if qw != "w" else ""
        return self.get(vr, qw, bk, ch, is_published)

    def get(self, vr, qw, bk, ch, is_published):
        Caching = current.Caching

        return Caching.get(
            f"items_{qw}_{vr}_{bk}_{ch}_{is_published}_",
            lambda: self.get_c(vr, qw, bk, ch, is_published),
            ONE_HOUR,
        )

    def get_c(self, vr, qw, bk, ch, is_published):
        ViewDefs = current.ViewDefs
        Material = self.Material
        Word = self.Word
        Query = self.Query
        Note = self.Note

        (book, chapter) = Material.getPassage(vr, bk, ch)
        if not chapter:
            result = dict(
                colorPicker=ViewDefs.colorPicker,
                sideItems=[],
                qw=qw,
            )
        else:
            if qw == "q":
                sideItems = Query.getItems(vr, chapter, is_published == "v")
            elif qw == "w":
                sideItems = Word.getItems(vr, chapter)
            elif qw == "n":
                sideItems = Note.getItems(vr, book, chapter, is_published)
            else:
                sideItems = []
            result = dict(
                colorPicker=ViewDefs.colorPicker,
                sideItems=sideItems,
                qw=qw,
            )
        return result
