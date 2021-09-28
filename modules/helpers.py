import sys
from datetime import datetime
from base64 import b64decode, b64encode


DEBUG = True


def debug(msg):
    if DEBUG:
        sys.stdout.write(f"{msg}\n")
        sys.stdout.flush()


def isodt(dt=None):
    return (
        datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        if dt is None
        else dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    )


def hebKey(x):
    return x.replace("שׁ", "ששׁ").replace("שׂ", "ששׂ")


def iEncode(qw, idpart, keywords=None, sep="|"):
    if qw == "n":
        return (
            b64encode((f"{idpart}|{keywords}").encode("utf8"))
            .decode("utf8")
            .replace("\n", "")
            .replace("=", "_")
        )
    if qw == "w":
        return idpart
    if qw == "q":
        return str(idpart)
    return str(idpart)


def iDecode(qw, iidRep, sep="|", rsep=None):
    idpart = iidRep
    keywords = ""
    if qw == "n":
        try:
            (idpart, keywords) = (
                b64decode(iidRep.replace("_", "=").encode("utf8"))
                .decode("utf8")
                .split(sep, 1)
            )
        except Exception:
            (idpart, keywords) = (None, None)
    if qw == "w":
        (idpart, keywords) = (iidRep, "")
    if qw == "q":
        (idpart, keywords) = (int(iidRep) if iidRep.isdigit() else 0, "")
    if rsep is None:
        result = (idpart, keywords)
    else:
        if qw == "n":
            result = rsep.join((str(idpart), keywords))
        else:
            result = str(idpart)
    return result


def hEsc(material, fill=True):
    material = (
        material.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
        .replace("\\n", "\n")
    )
    if fill:
        if material == "":
            material = "&nbsp;"
    return material


def toAscii(x):
    return x.encode("ascii", "replace")


def formatVersion(qw, obj_id, vr, st):
    if qw == "q":
        keyName = "query_id"
        if st == 1:
            icon = "quote-right"
            cls = "special"
        elif st == 2:
            icon = "quote-right"
            cls = ""
        elif st == 3:
            icon = "gears"
            cls = "good"
        elif st == 4:
            icon = "circle-o"
            cls = "warning"
        elif st == 5:
            icon = "clock-o"
            cls = "error"
        return f"""<a href="#" class="ctl br{qw} {cls} fa fa-{icon}"
{keyName}="{obj_id}" v="{vr}"></a>"""

    else:
        keyName = "key_id"
        stRep = st if st else "-"
        return (
            f'<a href="#" class="ctl br{qw}" {keyName}="{obj_id}" v="{vr}">{stRep}</a>'
        )


def pagelist(page, pages, spread):
    factor = 1
    filteredPages = {1, page, pages}
    while factor <= pages:
        pageBase = factor * int(page / factor)
        filteredPages |= {
            pageBase + int((i - spread / 2) * factor)
            for i in range(2 * int(spread / 2) + 1)
        }
        factor *= spread
    return sorted(i for i in filteredPages if i > 0 and i <= pages)


def countSlots(rows):
    covered = set()
    for (b, e) in rows:
        covered |= set(range(b, e + 1))
    return len(covered)


def flatten(msets):
    result = set()
    for (b, e) in msets:
        for m in range(b, e + 1):
            result.add(m)
    return list(sorted(result))


def collapseToRanges(slots):
    covered = set()
    for start in slots:
        covered.add(start)
    return normRanges(None, fromset=covered)


def normRanges(ranges, fromset=None):
    covered = set()
    if fromset is not None:
        covered = fromset
    else:
        for (start, end) in ranges:
            for i in range(start, end + 1):
                covered.add(i)
    curStart = None
    curEnd = None
    result = []
    for i in sorted(covered):
        if i not in covered:
            if curEnd is not None:
                result.append((curStart, curEnd - 1))
            curStart = None
            curEnd = None
        elif curEnd is None or i > curEnd:
            if curEnd is not None:
                result.append((curStart, curEnd - 1))
            curStart = i
            curEnd = i + 1
        else:
            curEnd = i + 1
    if curEnd is not None:
        result.append((curStart, curEnd - 1))
    return (len(covered), result)


# we need to hEsc the markdown text
# but markdown does an extra layer of escaping & inside href attributes.
# we have to unescape doubly escaped &


def sanitize(text):
    return text.replace("&amp;amp;", "&amp;")
