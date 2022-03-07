import sys
import re

varRe = re.compile(r"«([^»]*)»")


def varRepl(match):
    k = match.group(1)
    if k in keyValues:
        value = keyValues[k]
    else:
        value = ""
        print(f"Undefined parameter: {k}")
    return value


inFile = sys.argv[1]
outFile = sys.argv[2]
data = sys.argv[3]

keyValues = {}

for line in data.strip().split("\n"):
    parts = line.strip().split("=", 1)
    if len(parts) < 2:
        print(f"Missing value for {parts[0]}")
        continue
    (k, v) = parts
    keyValues[k] = v

with open(inFile) as f:
    text = f.read()
    text = varRe.sub(varRepl, text)


with open(outFile, "w") as f:
    f.write(text)
