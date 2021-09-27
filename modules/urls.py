import re

from gluon import current

from helpers import hEsc


class Urls:
    def __init__(self):
        URL = current.URL

        imagePat = re.compile(
            """<a [^>]*href=['"]image[\n\t ]+([^)\n\t '"]+)['"][^>]*>(.*?)</a>"""
        )

        def imageRepl(match):
            return f"""<br/><img src="{match.group(1)}"/><br/>{match.group(2)}<br/>"""

        versePat = re.compile(
            r"""(<a [^>]*href=['"])([^)\n\t ]+)[\n\t ]+([^:)\n\t '"]+)"""
            r""":([^)\n\t '"]+)(['"][^>]*>.*?</a>)"""
        )

        def verseRepl(match):
            return (
                match.group(1)
                + hEsc(
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

        chapterPat = re.compile(
            """(<a [^>]*href=['"])([^)\n\t ]+)[\n\t ]+"""
            """([^)\n\t '"]+)(['"][^>]*>.*?</a>)"""
        )

        def chapterRepl(match):
            return (
                match.group(1)
                + hEsc(
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

        shebanqPat = re.compile("""(href=['"])shebanq:([^)\n\t '"]+['"])""")

        def shebanqRepl(match):
            return match.group(1) + URL("hebrew", "text", host=True) + match.group(2)

        featurePat = re.compile("""(href=['"])feature:([^)\n\t '"]+)(['"])""")

        def featureRepl(match):
            return (
                f"""{match.group(1)}{URL("static", "docs/features", host=True)}/"""
                f"""{match.group(2)}{match.group(3)} """
                '''target="_blank"'''
            )

        def specialLinks(md):
            md = imagePat.sub(imageRepl, md)
            md = versePat.sub(verseRepl, md)
            md = chapterPat.sub(chapterRepl, md)
            md = shebanqPat.sub(shebanqRepl, md)
            md = featurePat.sub(featureRepl, md)
            return md

        setattr(self, "specialLinks", specialLinks)
