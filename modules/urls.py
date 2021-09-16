import re

from helpers import h_esc


class Urls:
    def __init__(self, URL):
        self.URL = URL

        image_pat = re.compile(
            """<a [^>]*href=['"]image[\n\t ]+([^)\n\t '"]+)['"][^>]*>(.*?)</a>"""
        )

        def image_repl(match):
            return f"""<br/><img src="{match.group(1)}"/><br/>{match.group(2)}<br/>"""

        verse_pat = re.compile(
            r"""(<a [^>]*href=['"])([^)\n\t ]+)[\n\t ]+([^:)\n\t '"]+)"""
            r""":([^)\n\t '"]+)(['"][^>]*>.*?</a>)"""
        )

        def verse_repl(match):
            return (
                match.group(1)
                + h_esc(
                    URL(
                        "hebrew",
                        "text",
                        host=True,
                        vars=dict(
                            book=match.group(2),
                            chapter=match.group(3),
                            verse=match.group(4),
                            mr="m",
                        ),
                    )
                )
                + match.group(5)
            )

        chapter_pat = re.compile(
            """(<a [^>]*href=['"])([^)\n\t ]+)[\n\t ]+"""
            """([^)\n\t '"]+)(['"][^>]*>.*?</a>)"""
        )

        def chapter_repl(match):
            return (
                match.group(1)
                + h_esc(
                    URL(
                        "hebrew",
                        "text",
                        host=True,
                        vars=dict(
                            book=match.group(2),
                            chapter=match.group(3),
                            verse="1",
                            mr="m",
                        ),
                    )
                )
                + match.group(4)
            )

        shebanq_pat = re.compile("""(href=['"])shebanq:([^)\n\t '"]+['"])""")

        def shebanq_repl(match):
            return match.group(1) + URL("hebrew", "text", host=True) + match.group(2)

        feature_pat = re.compile("""(href=['"])feature:([^)\n\t '"]+)(['"])""")

        def feature_repl(match):
            return (
                f"""{match.group(1)}{URL("static", "docs/features", host=True)}/"""
                f"""{match.group(2)}{match.group(3)} """
                '''target="_blank"'''
            )

        def special_links(d_md):
            d_md = image_pat.sub(image_repl, d_md)
            d_md = verse_pat.sub(verse_repl, d_md)
            d_md = chapter_pat.sub(chapter_repl, d_md)
            d_md = shebanq_pat.sub(shebanq_repl, d_md)
            d_md = feature_pat.sub(feature_repl, d_md)
            return d_md

        setattr(self, "special_links", special_links)
