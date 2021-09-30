import sys
import re
from subprocess import run

from tools.pdocs import console, pdoc3serve, pdoc3, shipDocs

ORG = "etcbc"
REPO = "shebanq"
PKG = "shebanq"

VERSION_CONFIG = dict(
    setup=dict(
        file="setup.py",
        re=re.compile(r"""version\s*=\s*['"]([^'"]*)['"]"""),
        mask="version='{}'",
    ),
)

currentVersion = None
newVersion = None


HELP = """
python3 build.py command

command:

-h
--help


docs  : serve docs locally
pdocs : build docs
sdocs : ship docs
clean : clean local develop build
l     : local develop build
g     : push to github, code and docs
v     : show current version
r1    : version becomes r1+1.0.0
r2    : version becomes r1.r2+1.0
r3    : version becomes r1.r2.r3+1
ship  : build for shipping

For g and ship you need to pass a commit message.
"""


def readArgs():
    args = sys.argv[1:]
    if not len(args) or args[0] in {"-h", "--help", "help"}:
        console(HELP)
        return (False, None, [])
    arg = args[0]
    if arg not in {
        "docs",
        "pdocs",
        "sdocs",
        "clean",
        "l",
        "i",
        "g",
        "v",
        "r1",
        "r2",
        "r3",
        "ship",
    }:
        console(HELP)
        return (False, None, [])
    if arg in {"g", "ship"}:
        if len(args) < 2:
            console("Provide a commit message")
            return (False, None, [])
        return (arg, args[1], args[2:])
    return (arg, None, [])


def incVersion(version, task):
    comps = [int(c) for c in version.split(".")]
    (major, minor, update) = comps
    if task == "r1":
        major += 1
        minor = 0
        update = 0
    elif task == "r2":
        minor += 1
        update = 0
    elif task == "r3":
        update += 1
    return ".".join(str(c) for c in (major, minor, update))


def replaceVersion(task, mask):
    def subVersion(match):
        global currentVersion
        global newVersion
        currentVersion = match.group(1)
        newVersion = incVersion(currentVersion, task)
        return mask.format(newVersion)

    return subVersion


def showVersion():
    global currentVersion
    versions = set()
    for (key, c) in VERSION_CONFIG.items():
        with open(c["file"]) as fh:
            text = fh.read()
        match = c["re"].search(text)
        version = match.group(1)
        console(f'{version} (according to {c["file"]})')
        versions.add(version)
    currentVersion = None
    if len(versions) == 1:
        currentVersion = list(versions)[0]


def adjustVersion(task):
    for (key, c) in VERSION_CONFIG.items():
        console(f'Adjusting version in {c["file"]}')
        with open(c["file"]) as fh:
            text = fh.read()
        text = c["re"].sub(replaceVersion(task, c["mask"]), text)
        with open(c["file"], "w") as fh:
            fh.write(text)
    if currentVersion == newVersion:
        console(f"Rebuilding version {newVersion}")
    else:
        console(f"Replacing version {currentVersion} by {newVersion}")


def commit(task, msg):
    run(["git", "add", "--all", "."])
    run(["git", "commit", "-m", msg])
    run(["git", "push", "origin", "master"])
    if task in {"ship"}:
        tagVersion = f"v{currentVersion}"
        commitMessage = f"Release {currentVersion}: {msg}"
        run(["git", "tag", "-a", tagVersion, "-m", commitMessage])
        run(["git", "push", "origin", "--tags"])


def clean():
    run(["python3", "setup.py", "develop", "-u"])
    run(["pip3", "uninstall", "-y", PKG])


def main():
    (task, msg, remaining) = readArgs()
    if not task:
        return
    elif task == "docs":
        pdoc3serve(PKG)
    elif task == "pdocs":
        pdoc3(PKG)
    elif task == "sdocs":
        shipDocs(ORG, REPO, PKG)
    elif task == "clean":
        clean()
    elif task == "l":
        clean()
        run(["python3", "setup.py", "develop"])
    elif task == "g":
        shipDocs(ORG, REPO, PKG)
        commit(task, msg)
    elif task == "v":
        showVersion()
    elif task in {"r", "r1", "r2", "r3"}:
        adjustVersion(task)
    elif task == "ship":
        showVersion()
        if not currentVersion:
            console("No current version")
            return

        answer = input("right version ? [yn]")
        if answer != "y":
            return
        shipDocs(ORG, REPO, PKG)
        commit(task, msg)


main()
