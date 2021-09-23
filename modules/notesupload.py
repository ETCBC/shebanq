from viewdefs import NOTE_STATUS_CLS


class NOTESUPLOAD:
    def __init__(self, Caching, Pieces, auth, db, NOTE_DB, VERSIONS):
        self.Caching = Caching
        self.Pieces = Pieces
        self.auth = auth
        self.db = db
        self.NOTE_DB = NOTE_DB
        self.VERSIONS = VERSIONS

    def authUpload(self):
        auth = self.auth
        db = self.db

        myId = None
        authorized = False
        if auth.user:
            myId = auth.user.id
        if myId:
            sql = f"""
select uid from uploaders where uid = {myId}
    """
            records = db.executesql(sql)
            authorized = (
                records is not None and len(records) == 1 and records[0][0] == myId
            )
        msg = "" if authorized else "you are not allowed to upload notes as csv files"
        return (authorized, myId, msg)

    def upload(self, user_id, filetext, now, msgs):
        Caching = self.Caching
        Pieces = self.Pieces
        NOTE_DB = self.NOTE_DB
        VERSIONS = self.VERSIONS

        myVersions = set()
        bookInfo = {}
        for vr in VERSIONS:
            myVersions.add(vr)
            bookInfo[vr] = Pieces.getBooks(vr)[0]
        normFields = "\t".join(
            """
            version
            book
            chapter
            verse
            clause_atom
            is_shared
            is_published
            status
            keywords
            ntext
        """.strip().split()
        )
        good = True
        fieldnames = normFields.split("\t")
        nfields = len(fieldnames)
        errors = {}
        allKeywords = set()
        allVersions = set()
        now = now
        created_on = now
        modified_on = now

        nerrors = 0
        chunks = []
        chunksize = 100
        sqlhead = f"""
insert into note
({", ".join(fieldnames)},
 created_by, created_on, modified_on, shared_on, published_on,
 bulk) values
"""
        thisChunk = []
        thisI = 0
        for (i, linenl) in enumerate(filetext.value.decode("utf8").split("\n")):
            line = linenl.rstrip()
            if line == "":
                continue
            if i == 0:
                if line != normFields:
                    msgs.append(
                        [
                            "error",
                            (
                                f"Wrong fields: {line}. "
                                f"Required fields are {normFields}"
                            ),
                        ]
                    )
                    good = False
                    break
                continue
            fields = line.replace("'", "''").split("\t")
            if len(fields) != nfields:
                nerrors += 1
                errors.setdefault("wrong number of fields", []).append(i + 1)
                continue
            (
                version,
                book,
                chapter,
                verse,
                clause_atom,
                is_shared,
                is_published,
                status,
                keywords,
                ntext,
            ) = fields
            published_on = "NULL"
            shared_on = "NULL"
            if version not in myVersions:
                nerrors += 1
                errors.setdefault("unrecognized version", []).append(
                    f"{i + 1}:{version}"
                )
                continue
            books = bookInfo[version]
            if book not in books:
                nerrors += 1
                errors.setdefault("unrecognized book", []).append(f"{i + 1}:{book}")
                continue
            maxChapter = books[book]
            if not chapter.isdigit() or int(chapter) > maxChapter:
                nerrors += 1
                errors.setdefault("unrecognized chapter", []).append(
                    f"{i + 1}:{chapter}"
                )
                continue
            if not verse.isdigit() or int(verse) > 200:
                nerrors += 1
                errors.setdefault("unrecognized verse", []).append(f"{i + 1}:{verse}")
                continue
            if not clause_atom.isdigit() or int(clause_atom) > 100000:
                nerrors += 1
                errors.setdefault("unrecognized clause_atom", []).append(
                    f"{i + 1}:{clause_atom}"
                )
                continue
            if is_shared not in {"T", ""}:
                nerrors += 1
                errors.setdefault("unrecognized shared field", []).append(
                    f"{i + 1}:{is_shared}"
                )
                continue
            if is_published not in {"T", ""}:
                nerrors += 1
                errors.setdefault("unrecognized published field", []).append(
                    f"{i + 1}:{is_published}"
                )
                continue
            if status not in NOTE_STATUS_CLS:
                nerrors += 1
                errors.setdefault("unrecognized status", []).append(f"{i + 1}:{status}")
                continue
            if len(keywords) >= 128:
                nerrors += 1
                errors.setdefault("keywords length over 128", []).append(
                    f"{i + 1}:{len(keywords)}"
                )
                continue
            if len(ntext) >= 1024:
                nerrors += 1
                errors.setdefault("note text length over 1024", []).append(
                    f"{i + 1}:{len(ntext)}"
                )
                continue
            if nerrors > 20:
                msgs.append(["error", "too many errors, aborting"])
                break
            if is_shared == "T":
                shared_on = f"'{now}'"
            if is_published == "T":
                published_on = f"'{now}'"
            keywordList = keywords.split()
            if len(keywordList) == 0:
                errors.setdefault("empty keyword", []).append(f'{i+ 1}:"{keywords}"')
                continue
            allKeywords |= set(keywordList)
            keywords = "".join(f" {x} " for x in keywordList)
            allVersions.add(version)
            thisChunk.append(
                (
                    f"('{version}','{book}',{chapter},{verse},{clause_atom},"
                    f"'{is_shared}','{is_published}',"
                    f"'{status}','{keywords}','{ntext}',{user_id},"
                    f"'{created_on}','{modified_on}',{shared_on},{published_on},'b')"
                )
            )
            thisI += 1
            if thisI >= chunksize:
                chunks.append(thisChunk)
                thisChunk = []
                thisI = 0
        if len(thisChunk):
            chunks.append(thisChunk)

        # with open('/tmp/xxx.txt', 'w') as fh:
        #    for line in filetext.value:
        #        fh.write(line)
        if errors or nerrors:
            good = False
        else:
            avrep = "', '".join(allVersions)
            whereVersion = f"version in ('{avrep}')"
            whereKeywords = " or ".join(
                f" keywords like '% {keyword} %' " for keyword in keywordList
            )
            # first delete previously bulk uploaded notes by this author
            # and with these keywords and these versions
            delSql = f"""delete from note
where bulk = 'b'
and created_by = {user_id}
and {whereVersion}
and {whereKeywords};"""
            NOTE_DB.executesql(delSql)
            for chunk in chunks:
                chunkRep = ",\n".join(chunk)
                sql = f"{sqlhead} {chunkRep};"
                NOTE_DB.executesql(sql)
            Caching.clear(r"^items_n_")
            for vr in myVersions:
                Caching.clear(f"^verses_{vr}_n_")
        for msg in sorted(errors):
            istr = ",".join(str(i) for i in errors[msg])
            msgs.append(["error", f"{msg}: {istr}"])
        msgs.append(["good" if good else "error", "Done"])
        return True
