import sys
import os
from subprocess import run
from textwrap import dedent


ORG = "etcbc"
REPO = "shebanq"
PKG = "shebanq"

PY_SRC = "modules/"
PY_DST = "docs/server/bymodule"

JS_SRC = "static/js/app"
JS_DST = "docs/client/bymodule"

HELP = """
python3 build.py command

command:

-h
--help


jdocs : build jsdocs
docs  : serve docs locally (after building them, including js docs)
mdocs : build docs (excluding jsdocs)
mkdocs : build docs (including jsdocs)
sdocs : ship docs (after building them, including js docs)
ship  : build for shipping

For g and ship you need to pass a commit message.
"""


def console(*args):
    sys.stderr.write(" ".join(args) + "\n")
    sys.stderr.flush()


def readArgs():
    args = sys.argv[1:]
    if not len(args) or args[0] in {"-h", "--help", "help"}:
        console(HELP)
        return (False, None, [])
    arg = args[0]
    if arg not in {
        "jdocs",
        "docs",
        "mdocs",
        "mkdocs",
        "sdocs",
        "clean",
        "ship",
    }:
        console(HELP)
        return (False, None, [])
    if arg in {"ship"}:
        if len(args) < 2:
            console("Provide a commit message")
            return (False, None, [])
        return (arg, args[1], args[2:])
    return (arg, None, [])


def commit(task, msg):
    run(["git", "add", "--all", "."])
    run(["git", "commit", "-m", msg])
    run(["git", "push", "origin", "master"])


def serveDocs():
    run(["mkdocs", "serve"])


def makeDocs():
    run(["mkdocs", "build"])


def shipDocs():
    run(["mkdocs", "gh-deploy"])


def makePyDocs():
    pyFiles = sorted(
        pyFile.removesuffix(".py")
        for pyFile in os.listdir(PY_SRC)
        if pyFile.endswith(".py")
    )
    console(f"update references for {len(pyFiles)} python modules")
    for pyFile in pyFiles:
        with open(f"{PY_DST}/{pyFile}.md", "w") as fh:
            fh.write(
                dedent(
                    f"""
                ## ::: {pyFile}

                ---

                """
                )
            )


def makeJsDocs():
    jsFiles = sorted(jsFile for jsFile in os.listdir(JS_SRC) if jsFile.endswith(".js"))
    console(f"update jsdocs for {len(jsFiles)} modules")
    for jsFile in jsFiles:
        outFile = f"{jsFile.removesuffix('js')}md"
        run(f"jsdoc2md {JS_SRC}/{jsFile} > {JS_DST}/{outFile}", shell=True)


def main():
    (task, msg, remaining) = readArgs()
    if not task:
        return
    elif task == "jdocs":
        makeJsDocs()
    elif task == "docs":
        makeJsDocs()
        makePyDocs()
        serveDocs()
    elif task == "mdocs":
        makeDocs()
    elif task == "mkdocs":
        makeJsDocs()
        makePyDocs()
        makeDocs()
    elif task == "sdocs":
        makeJsDocs()
        makePyDocs()
        shipDocs()
    elif task == "ship":
        shipDocs()
        commit(task, msg)


main()
