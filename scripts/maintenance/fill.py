import sys
import re

varRe = re.compile(r"«([^»]*)»")


def varRepl(match):
    k = match.group(1)
    return keyValues[k]


inFile = sys.argv[1]
outFile = sys.argv[2]
data = sys.argv[3]

keyValues = {}

for line in data.strip().split():
    (k, v) = line.strip().split("=")
    keyValues[k] = v

with open(inFile) as f:
    text = f.read()
    text = varRe.sub(varRepl, text)


with open(outFile, "w") as f:
    f.write(text)
