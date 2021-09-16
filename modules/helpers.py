from base64 import b64decode, b64encode


DEBUG = True


def debug(msg):
    if DEBUG:
        print(msg)


def heb_key(x):
    return x.replace("שׁ", "ששׁ").replace("שׂ", "ששׂ")


def iid_encode(qw, idpart, kw=None, sep="|"):
    if qw == "n":
        return (
            b64encode((f"{idpart}|{kw}").encode("utf8"))
            .decode("utf8")
            .replace("\n", "")
            .replace("=", "_")
        )
    if qw == "w":
        return idpart
    if qw == "q":
        return str(idpart)
    return str(idpart)


def iid_decode(qw, iidrep, sep="|", rsep=None):
    idpart = iidrep
    kw = ""
    if qw == "n":
        try:
            (idpart, kw) = (
                b64decode(iidrep.replace("_", "=").encode("utf8"))
                .decode("utf8")
                .split(sep, 1)
            )
        except Exception:
            (idpart, kw) = (None, None)
    if qw == "w":
        (idpart, kw) = (iidrep, "")
    if qw == "q":
        (idpart, kw) = (int(iidrep) if iidrep.isdigit() else 0, "")
    if rsep is None:
        result = (idpart, kw)
    else:
        if qw == "n":
            result = rsep.join((str(idpart), kw))
        else:
            result = str(idpart)
    return result


def h_esc(material, fill=True):
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


def to_ascii(x):
    return x.encode("ascii", "replace")


def formatVersion(qw, lid, vr, st):
    if qw == "q":
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
        return f"""<a href="#" class="ctrl br{qw} {cls} fa fa-{icon}"
{qw}id="{lid}" v="{vr}"></a>"""

    else:
        strep = st if st else "-"
        return f'<a href="#" class="ctrl br{qw}" nkid="{lid}" v="{vr}">{strep}</a>'


def pagelist(page, pages, spread):
    factor = 1
    filtered_pages = {1, page, pages}
    while factor <= pages:
        page_base = factor * int(page / factor)
        filtered_pages |= {
            page_base + int((i - spread / 2) * factor)
            for i in range(2 * int(spread / 2) + 1)
        }
        factor *= spread
    return sorted(i for i in filtered_pages if i > 0 and i <= pages)


def count_monads(rows):
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


def collapse_into_ranges(monads):
    covered = set()
    for (start,) in monads:
        covered.add(start)
    return normalize_ranges(None, fromset=covered)


def normalize_ranges(ranges, fromset=None):
    covered = set()
    if fromset is not None:
        covered = fromset
    else:
        for (start, end) in ranges:
            for i in range(start, end + 1):
                covered.add(i)
    cur_start = None
    cur_end = None
    result = []
    for i in sorted(covered):
        if i not in covered:
            if cur_end is not None:
                result.append((cur_start, cur_end - 1))
            cur_start = None
            cur_end = None
        elif cur_end is None or i > cur_end:
            if cur_end is not None:
                result.append((cur_start, cur_end - 1))
            cur_start = i
            cur_end = i + 1
        else:
            cur_end = i + 1
    if cur_end is not None:
        result.append((cur_start, cur_end - 1))
    return (len(covered), result)


# we need to h_esc the markdown text
# but markdown does an extra layer of escaping & inside href attributes.
# we have to unescape doubly escaped &


def sanitize(text):
    return text.replace("&amp;amp;", "&amp;")


def feed(db):
    pqueryx_sql = """
select
    query.id as qid,
    auth_user.first_name as ufname,
    auth_user.last_name as ulname,
    query.name as qname,
    query.description as qdesc,
    qe.id as qvid,
    qe.executed_on as qexe,
    qe.version as qver
from query inner join
    (
        select t1.id, t1.query_id, t1.executed_on, t1.version
        from query_exe t1
          left outer join query_exe t2
            on (
                t1.query_id = t2.query_id and
                t1.executed_on < t2.executed_on and
                t2.executed_on >= t2.modified_on
            )
        where
            (t1.executed_on is not null and t1.executed_on >= t1.modified_on) and
            t2.query_id is null
    ) as qe
on qe.query_id = query.id
inner join auth_user on query.created_by = auth_user.id
where query.is_shared = 'T'
order by qe.executed_on desc, auth_user.last_name
"""

    return db.executesql(pqueryx_sql)
