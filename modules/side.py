from viewsettings import colorpicker
from helpers import debug


class SIDE:
    def __init__(self, Caching, Material, Word, Query, Note):
        self.Caching = Caching
        self.Material = Material
        self.Word = Word
        self.Query = Query
        self.Note = Note

    def get(self, vr, qw, bk, ch, pub):
        Caching = self.Caching

        return Caching.get(
            f"items_{qw}_{vr}_{bk}_{ch}_{pub}_",
            lambda: self.get_c(vr, qw, bk, ch, pub),
            None,
        )

    def get_c(self, vr, qw, bk, ch, pub):
        Material = self.Material
        Word = self.Word
        Query = self.Query
        Note = self.Note

        (book, chapter) = Material.get_passage(vr, bk, ch)
        if not chapter:
            result = dict(
                colorpicker=colorpicker,
                side_items=[],
                qw=qw,
            )
        else:
            if qw == "q":
                debug(f"original function PUB={pub}")
                monad_sets = Query.get_items(vr, chapter, pub == "v")
                side_items = Query.group(vr, monad_sets)
            elif qw == "w":
                monad_sets = Word.get_items(vr, chapter)
                side_items = Word.group(vr, monad_sets)
            elif qw == "n":
                side_items = Note.get_items(vr, book, chapter, pub)
            else:
                side_items = []
            result = dict(
                colorpicker=colorpicker,
                side_items=side_items,
                qw=qw,
            )
        return result
