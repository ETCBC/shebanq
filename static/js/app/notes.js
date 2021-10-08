/* eslint-env jquery */
/* globals Config, PG, VS, LS, markdown */

/**
 * @module notes
 */

import { escHT, specialLinks, markdownEscape, idPrefixNotes } from "./helpers.js"
import { Diagnostics } from "./diagnostics.js"

/**
 * Controls notes on **text** pages
 *
 * @see [notetree] for the notes overview page.
 */
export class Notes {
  constructor(contentNew) {
    this.show = false
    this.verseList = {}
    this.version = PG.version
    this.saveCtls = $("span.nt_main_sav")
    this.saveCtl = this.saveCtls.find('a[tp="s"]')
    this.revertCtl = this.saveCtls.find('a[tp="r"]')
    this.authenticated = false
    this.mainCtl = $("a.nt_main_ctl")

    contentNew.find(".vradio").each((i, el) => {
      const elem = $(el)
      const bk = elem.attr("b")
      const ch = elem.attr("c")
      const vs = elem.attr("v")
      const container = elem.closest("div")
      this.verseList[`${bk} ${ch}:${vs}`] = new NoteVerse(
        this.version,
        bk,
        ch,
        vs,
        container.find("span.nt_ctl"),
        container.find("table.t1_table")
      )
    })
    const { verseList } = this
    this.diagnostics = new Diagnostics("nt_main_msg", () => {
      for (const noteVerse of Object.values(verseList)) {
        noteVerse.clearDiagnostics()
      }
    })
    this.mainCtl.off("click").click(e => {
      e.preventDefault()
      VS.setHighlight("n", { get: VS.get("n") == "v" ? "x" : "v" })
      this.apply()
    })
    this.revertCtl.off("click").click(e => {
      e.preventDefault()
      for (const noteVerse of Object.values(verseList)) {
        noteVerse.revert()
      }
    })
    this.saveCtl.off("click").click(e => {
      e.preventDefault()
      for (const noteVerse of Object.values(verseList)) {
        noteVerse.save()
      }
      this.diagnostics.msg(["special", "Done"])
    })
    this.diagnostics.clear()
    $("span.nt_main_sav").hide()
    this.apply()
  }

  apply() {
    const { verseList } = this

    if (VS.get("n") == "v") {
      this.mainCtl.addClass("nt_loaded")
      for (const noteVerse of Object.values(verseList)) {
        noteVerse.showNotes(false)
        this.authenticated = noteVerse.authenticated
      }
      if (this.authenticated) {
        this.saveCtls.show()
      }
    } else {
      this.mainCtl.removeClass("nt_loaded")
      this.saveCtls.hide()
      for (const noteVerse of Object.values(verseList)) {
        noteVerse.hideNotes()
      }
    }
  }
}

/**
 * Controls the notes belonging to a single verse.
 */
class NoteVerse {
  constructor(vr, bk, ch, vs, ctl, dest) {
    this.loaded = false
    this.nNotes = 0
    this.mnotes = 0
    this.show = false
    this.editing = false
    this.dirty = false
    this.version = vr
    this.book = bk
    this.chapter = ch
    this.verse = vs
    this.ctl = ctl
    this.dest = dest

    const { book, chapter, verse } = this
    this.diagnostics = new Diagnostics(`nt_msg_${book}_${chapter}_${verse}`)
    this.noteCtl = ctl.find("a.nt_ctl")
    this.saveCtls = ctl.find("span.nt_sav")

    const { saveCtls } = this
    this.saveCtl = saveCtls.find('a[tp="s"]')
    this.editCtl = saveCtls.find('a[tp="e"]')
    this.revertCtl = saveCtls.find('a[tp="r"]')

    const { saveCtl, editCtl, revertCtl, noteCtl } = this

    saveCtl.off("click").click(e => {
      e.preventDefault()
      this.save()
    })
    editCtl.off("click").click(e => {
      e.preventDefault()
      this.edit()
    })
    revertCtl.off("click").click(e => {
      e.preventDefault()
      this.revert()
    })
    noteCtl.off("click").click(e => {
      e.preventDefault()
      this.isDirty()
      if (this.show) {
        this.hideNotes()
      } else {
        this.showNotes(true)
      }
    })

    dest.find("tr.nt_cmt").hide()
    $("span.nt_main_sav").hide()
    saveCtls.hide()
  }

  /**
   * get the notes belonging to the current verse.
   *
   * @see Triggers [C:hebrew.getversenotes][controllers.hebrew.getversenotes]
   */
  fetch(adjustVerse) {
    const { getNotesVerseJsonUrl } = Config

    const { version, book, chapter, verse, editing, diagnostics } = this
    const sendData = { version, book, chapter, verse, edit: editing }
    diagnostics.msg(["info", "fetching notes ..."])
    $.post(getNotesVerseJsonUrl, sendData, data => {
      this.loaded = true
      diagnostics.clear()
      for (const mg of data.msgs) {
        diagnostics.msg(mg)
      }
      const { good, users, notes, keyIndex, changed, authenticated } = data
      if (good) {
        this.process(users, notes, keyIndex, changed, authenticated)
        if (adjustVerse) {
          if (PG.mr == "m") {
            VS.setMaterial({ verse })
            PG.material.gotoVerse()
          }
        }
      }
    })
  }

  process(users, notes, keyIndex, changed, authenticated) {
    const {
      sidebars: { sideFetched, sidebar },
    } = PG
    if (changed) {
      if (PG.mr == "m") {
        sideFetched["mn"] = false
        sidebar["mn"].content.apply()
      }
    }
    this.usersOld = users
    this.notesOld = notes
    this.origKeyIndex = keyIndex
    this.editOld = []
    this.authenticated = authenticated
    this.genHtml(true)
    this.dirty = false
    this.applyDirty()
    this.decorate()
  }

  decorate() {
    const { noteStatusCls, noteStatusSym, noteStatusNxt } = Config
    const { dest, authenticated, saveCtls, editing, saveCtl, editCtl } = this
    dest
      .find("td.nt_stat")
      .find("a")
      .off("click")
      .click(e => {
        e.preventDefault()
        const elem = $(e.delegateTarget)
        const statcode = elem.attr("code")
        const nextcode = noteStatusNxt[statcode]
        const nextsym = noteStatusSym[nextcode]
        const row = elem.closest("tr")
        for (const cls of Object.values(noteStatusCls)) {
          row.removeClass(cls)
        }
        for (const cls of Object.values(noteStatusSym)) {
          elem.removeClass(`fa-${cls}`)
        }
        row.addClass(noteStatusCls[nextcode])
        elem.attr("code", nextcode)
        elem.addClass(`fa-${nextsym}`)
      })
    dest
      .find("td.nt_pub")
      .find("a")
      .off("click")
      .click(e => {
        e.preventDefault()
        const elem = $(e.delegateTarget)
        if (elem.hasClass("ison")) {
          elem.removeClass("ison")
        } else {
          elem.addClass("ison")
        }
      })
    dest.find("tr.nt_cmt").show()
    if (authenticated) {
      $("span.nt_main_sav").show()
      saveCtls.show()
      if (editing) {
        saveCtl.show()
        editCtl.hide()
      } else {
        saveCtl.hide()
        editCtl.show()
      }
    }
    PG.decorateCrossrefs(dest)
  }

  genHtmlClauseAtom(clause_atom) {
    const { noteStatusCls, noteStatusSym } = Config
    const { lsNotesMuted } = LS
    const vr = this.version
    const notes = this.notesOld[clause_atom]
    const keyIndex = this.origKeyIndex
    let html = ""
    this.nNotes += notes.length
    for (const note of notes) {
      const { user_id, note_id, is_published, is_shared, ro } = note
      const keywordsTrim = $.trim(note.keywords)
      const keywordList = keywordsTrim.split(/\s+/)
      let mute = false
      for (const keywords of keywordList) {
        const key_id = keyIndex[`${user_id} ${keywords}`]
        if (lsNotesMuted.isSet(`${idPrefixNotes}${key_id}`)) {
          mute = true
          break
        }
      }
      if (mute) {
        this.mnotes += 1
        continue
      }
      const user = this.usersOld[user_id]
      const pubc = is_published ? "ison" : ""
      const sharedc = is_shared ? "ison" : ""
      const statc = noteStatusCls[note.status]
      const statsym = noteStatusSym[note.status]
      const editAtt = ro ? "" : ' edit="1"'
      const editCls = ro ? "" : " edit"
      html += `<tr class="nt_cmt nt_info ${statc}${editCls}" note_id="${note_id}"
          note_clause_atom="${clause_atom}"${editAtt}">`
      if (ro) {
        html += `<td class="nt_stat">
            <span class="fa fa-${statsym} fa-fw" code="${note.status}"></span>
          </td>`
        html += `<td class="keywords">${escHT(note.keywords)}</td>`
        const ntext = specialLinks(markdown.toHTML(markdownEscape(note.ntext)))
        html += `<td class="nt_cmt">${ntext}</td>`
        html += `<td class="nt_user" colspan="3" user_id="${user_id}">${escHT(
          user
        )}</td>`
        html += '<td class="nt_pub">'
        html += `<span class="ctli pradio fa fa-share-alt fa-fw ${sharedc}"
          title="shared?"></span>`
        html += `<span class="ctli pradio fa fa-quote-right fa-fw ${pubc}"
          title="published?"></span>`
      } else {
        this.editOld.push({ clause_atom, note })
        html += `<td class="nt_stat">
          <a href="#" title="set status" class="fa fa-${statsym} fa-fw"
          code="${note.status}"></a></td>`
        html += `<td class="keywords"><textarea>${note.keywords}</textarea></td>`
        html += `<td class="nt_cmt"><textarea>${note.ntext}</textarea></td>`
        html += `<td class="nt_user" colspan="3" user_id="{user_id}">${escHT(
          user
        )}</td>`
        html += '<td class="nt_pub">'
        html += `<a class="ctli pradio fa fa-share-alt fa-fw ${sharedc}"
          href="#" title="shared?"></a>`
        html += `<span>${vr}</span>`
        html += `<a class="ctli pradio fa fa-quote-right fa-fw ${pubc}"
          href="#" title="published?"></a>`
      }
      html += "</td></tr>"
    }
    return html
  }

  genHtml(replace) {
    this.mnotes = 0
    if (replace) {
      this.dest.find("tr[note_clause_atom]").remove()
    }
    for (const clause_atom in this.notesOld) {
      const thisDest = this.dest.find(`tr[clause_atom="${clause_atom}"]`)
      const html = this.genHtmlClauseAtom(clause_atom)
      thisDest.after(html)
    }
    if (this.nNotes == 0) {
      this.noteCtl.addClass("nt_empty")
    } else {
      this.noteCtl.removeClass("nt_empty")
    }
    if (this.mnotes == 0) {
      this.noteCtl.removeClass("nt_muted")
    } else {
      this.noteCtl.addClass("nt_muted")
      this.diagnostics.msg(["special", `muted notes: ${this.mnotes}`])
    }
  }

  /**
   * sends edited notes to the server in order to be saved.
   *
   * @see Triggers [C:hebrew.putversenotes][controllers.hebrew.putversenotes]
   */
  sendnotes(sendData) {
    const { putNotesVerseJsonUrl } = Config

    $.post(
      putNotesVerseJsonUrl,
      sendData,
      data => {
        const { good, users, notes, keyIndex, changed, authenticated } = data
        this.diagnostics.clear()
        for (const mg of data.msgs) {
          this.diagnostics.msg(mg)
        }
        if (good) {
          this.dest.find("tr[note_clause_atom]").remove()
          this.process(users, notes, keyIndex, changed, authenticated)
        }
      },
      "json"
    )
  }

  isDirty() {
    let dirty = false
    const { editOld } = this
    if (editOld == undefined) {
      this.dirty = false
      return
    }
    for (const entry of editOld) {
      const { clause_atom, note: noteOld } = entry
      const { note_id } = noteOld
      const noteNew =
        note_id == 0
          ? this.dest.find(`tr[note_id="0"][note_clause_atom="${clause_atom}"]`)
          : this.dest.find(`tr[note_id="${note_id}"]`)
      const statusOld = noteOld.status
      const statusNew = noteNew.find("td.nt_stat a").attr("code")
      const keywordsOld = $.trim(noteOld.keywords)
      const keywordsNew = $.trim(noteNew.find("td.keywords textarea").val())
      const ntextOld = noteOld.ntext
      const ntextNew = $.trim(noteNew.find("td.nt_cmt textarea").val())
      const is_sharedOld = noteOld.is_shared
      const isSharedNew = noteNew.find("td.nt_pub a").first().hasClass("ison")
      const isPublishedOld = noteOld.is_published
      const isPublishedNew = noteNew.find("td.nt_pub a").last().hasClass("ison")
      if (
        statusOld != statusNew ||
        keywordsOld != keywordsNew ||
        ntextOld != ntextNew ||
        is_sharedOld != isSharedNew ||
        isPublishedOld != isPublishedNew
      ) {
        dirty = true
        break
      }
    }
    this.dirty = dirty
    this.applyDirty()
  }

  applyDirty() {
    if (this.dirty) {
      this.noteCtl.addClass("dirty")
    } else if (this.noteCtl.hasClass("dirty")) {
      this.noteCtl.removeClass("dirty")
    }
  }
  save() {
    this.editing = false
    const { version, book, chapter, verse, editing, editOld } = this
    const data = {
      version,
      book,
      chapter,
      verse,
      edit: editing,
    }
    const notelines = []
    if (editOld == undefined) {
      return
    }
    for (const entry of editOld) {
      const { clause_atom, note: noteOld } = entry
      const { note_id, user_id } = noteOld
      const noteNew =
        note_id == 0
          ? this.dest.find(`tr[note_id="0"][note_clause_atom="${clause_atom}"]`)
          : this.dest.find(`tr[note_id="${note_id}"]`)
      const statusOld = noteOld.status
      const statusNew = noteNew.find("td.nt_stat a").attr("code")
      const keywordsOld = $.trim(noteOld.keywords)
      const keywordsNew = $.trim(noteNew.find("td.keywords textarea").val())
      const ntextOld = noteOld.ntext
      const ntextNew = $.trim(noteNew.find("td.nt_cmt textarea").val())
      const is_sharedOld = noteOld.is_shared
      const isSharedNew = noteNew.find("td.nt_pub a").first().hasClass("ison")
      const isPublishedOld = noteOld.is_published
      const isPublishedNew = noteNew.find("td.nt_pub a").last().hasClass("ison")
      if (
        statusOld != statusNew ||
        keywordsOld != keywordsNew ||
        ntextOld != ntextNew ||
        is_sharedOld != isSharedNew ||
        isPublishedOld != isPublishedNew
      ) {
        notelines.push({
          note_id,
          clause_atom,
          status: statusNew,
          keywords: keywordsNew,
          ntext: ntextNew,
          user_id,
          is_shared: isSharedNew,
          is_published: isPublishedNew,
        })
      }
    }
    if (notelines.length > 0) {
      data["notes"] = JSON.stringify(notelines)
    } else {
      this.diagnostics.msg(["warning", "No changes"])
    }
    this.sendnotes(data)
  }

  edit() {
    this.editing = true
    this.fetch(true)
  }

  revert() {
    this.editing = false
    const { version, book, chapter, verse, editing } = this
    const data = {
      version,
      book,
      chapter,
      verse,
      edit: editing,
    }
    data["notes"] = JSON.stringify([])
    this.sendnotes(data)
  }

  hideNotes() {
    this.show = false
    this.noteCtl.removeClass("nt_loaded")
    this.saveCtls.hide()
    this.dest.find("tr.nt_cmt").hide()
    this.diagnostics.hide()
  }

  showNotes(adjustVerse) {
    const {
      loaded,
      authenticated,
      editCtl,
      noteCtl,
      saveCtl,
      saveCtls,
      diagnostics,
      dest,
      editing,
    } = this

    this.show = true
    noteCtl.addClass("nt_loaded")
    diagnostics.show()
    if (!loaded) {
      this.fetch(adjustVerse)
    } else {
      dest.find("tr.nt_cmt").show()
      if (authenticated) {
        saveCtls.show()
        if (editing) {
          saveCtl.show()
          editCtl.hide()
        } else {
          saveCtl.hide()
          editCtl.show()
        }
      }
      if (PG.mr == "m") {
        VS.setMaterial({ verse: this.verse })
        PG.material.gotoVerse()
      }
    }
  }

  clearDiagnostics() {
    this.diagnostics.clear()
  }
}
