/* eslint-env jquery */
/* globals Config, P, L, markdown */

import { escHT, specialLinks, markdownEscape } from "./helpers.js"
import { Msg } from "./msg.js"

export class Notes {
  constructor(contentNew) {
    this.show = false
    this.verselist = {}
    this.version = P.version
    this.sav_controls = $("span.nt_main_sav")
    this.sav_c = this.sav_controls.find('a[tp="s"]')
    this.rev_c = this.sav_controls.find('a[tp="r"]')
    this.loggedIn = false
    this.mainCtrl = $("a.nt_main_ctl")

    contentNew.find(".vradio").each((i, el) => {
      const elem = $(el)
      const bk = elem.attr("b")
      const ch = elem.attr("c")
      const vs = elem.attr("v")
      const topl = elem.closest("div")
      this.verselist[`${bk} ${ch}:${vs}`] = new Notev(
        this.version,
        bk,
        ch,
        vs,
        topl.find("span.nt_ctl"),
        topl.find("table.t1_table")
      )
    })
    const { verselist } = this
    this.msgn = new Msg("nt_main_msg", () => {
      for (const notev of Object.values(verselist)) {
        notev.clear_msg()
      }
    })
    this.mainCtrl.click(e => {
      e.preventDefault()
      P.viewState.hstatesv("n", { get: P.viewState.get("n") == "v" ? "x" : "v" })
      this.apply()
    })
    this.rev_c.click(e => {
      e.preventDefault()
      for (const notev of Object.values(verselist)) {
        notev.revert()
      }
    })
    this.sav_c.click(e => {
      e.preventDefault()
      for (const notev of Object.values(verselist)) {
        notev.save()
      }
      this.msgn.msg(["special", "Done"])
    })
    this.msgn.clear()
    $("span.nt_main_sav").hide()
    this.apply()
  }

  apply() {
    const { verselist } = this

    if (P.viewState.get("n") == "v") {
      this.mainCtrl.addClass("nt_loaded")
      for (const notev of Object.values(verselist)) {
        notev.show_notes(false)
        this.loggedIn = notev.loggedIn
      }
      if (this.loggedIn) {
        this.sav_controls.show()
      }
    } else {
      this.mainCtrl.removeClass("nt_loaded")
      this.sav_controls.hide()
      for (const notev of Object.values(verselist)) {
        notev.hide_notes()
      }
    }
  }
}

class Notev {
  constructor(vr, bk, ch, vs, ctl, dest) {
    this.loaded = false
    this.nnotes = 0
    this.mnotes = 0
    this.show = false
    this.edt = false
    this.dirty = false
    this.version = vr
    this.book = bk
    this.chapter = ch
    this.verse = vs
    this.ctl = ctl
    this.dest = dest

    const { book, chapter, verse } = this
    this.msgn = new Msg(`nt_msg_${book}_${chapter}_${verse}`)
    this.noteCtrl = ctl.find("a.nt_ctl")
    this.sav_controls = ctl.find("span.nt_sav")

    const { sav_controls } = this
    this.sav_c = sav_controls.find('a[tp="s"]')
    this.edt_c = sav_controls.find('a[tp="e"]')
    this.rev_c = sav_controls.find('a[tp="r"]')

    const { sav_c, edt_c, rev_c, noteCtrl } = this

    sav_c.click(e => {
      e.preventDefault()
      this.save()
    })
    edt_c.click(e => {
      e.preventDefault()
      this.edit()
    })
    rev_c.click(e => {
      e.preventDefault()
      this.revert()
    })
    noteCtrl.click(e => {
      e.preventDefault()
      this.is_dirty()
      if (this.show) {
        this.hide_notes()
      } else {
        this.show_notes(true)
      }
    })

    dest.find("tr.nt_cmt").hide()
    $("span.nt_main_sav").hide()
    sav_controls.hide()
  }

  fetch(adjust_verse) {
    const { verseNotesUrl } = Config

    const { version, book, chapter, verse, edt, msgn } = this
    const senddata = { version, book, chapter, verse, edit: edt }
    msgn.msg(["info", "fetching notes ..."])
    $.post(verseNotesUrl, senddata, data => {
      this.loaded = true
      msgn.clear()
      for (const m of data.msgs) {
        msgn.msg(m)
      }
      const { good, users, notes, keyIndex, changed, loggedIn } = data
      if (good) {
        this.process(users, notes, keyIndex, changed, loggedIn)
        if (adjust_verse) {
          if (P.mr == "m") {
            P.viewState.mstatesv({ verse })
            P.material.goto_verse()
          }
        }
      }
    })
  }

  process(users, notes, keyIndex, changed, loggedIn) {
    const {
      sidebars: { side_fetched, sidebar },
    } = P
    if (changed) {
      if (P.mr == "m") {
        side_fetched["mn"] = false
        sidebar["mn"].content.apply()
      }
    }
    this.usersOld = users
    this.notesOld = notes
    this.origKeyIndex = keyIndex
    this.editOld = []
    this.loggedIn = loggedIn
    this.gen_html(true)
    this.dirty = false
    this.apply_dirty()
    this.decorate()
  }

  decorate() {
    const { noteStatusCls, noteStatusSym, noteStatusNxt } = Config
    const { dest, loggedIn, sav_controls, edt, sav_c, edt_c } = this
    dest
      .find("td.nt_stat")
      .find("a")
      .click(e => {
        e.preventDefault()
        const elem = $(e.delegateTarget)
        const statcode = elem.attr("code")
        const nextcode = noteStatusNxt[statcode]
        const nextsym = noteStatusSym[nextcode]
        const row = elem.closest("tr")
        for (const c in noteStatusCls) {
          row.removeClass(noteStatusCls[c])
        }
        for (const c in noteStatusSym) {
          elem.removeClass(`fa-${noteStatusSym[c]}`)
        }
        row.addClass(noteStatusCls[nextcode])
        elem.attr("code", nextcode)
        elem.addClass(`fa-${nextsym}`)
      })
    dest
      .find("td.nt_pub")
      .find("a")
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
    if (loggedIn) {
      $("span.nt_main_sav").show()
      sav_controls.show()
      if (edt) {
        sav_c.show()
        edt_c.hide()
      } else {
        sav_c.hide()
        edt_c.show()
      }
    }
    P.decorate_crossrefs(dest)
  }

  gen_html_ca(clause_atom) {
    const { noteStatusCls, noteStatusSym } = Config
    const { muting_n } = L
    const vr = this.version
    const notes = this.notesOld[clause_atom]
    const keyIndex = this.origKeyIndex
    let html = ""
    this.nnotes += notes.length
    for (let n = 0; n < notes.length; n++) {
      const nline = notes[n]
      const { user_id, note_id, is_published, is_shared, ro } = nline
      const keywordsTrim = $.trim(nline.keywords)
      const keywordList = keywordsTrim.split(/\s+/)
      let mute = false
      for (const keywords of keywordList) {
        const key_id = keyIndex[`${user_id} ${keywords}`]
        if (muting_n.isSet(`n${key_id}`)) {
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
      const statc = noteStatusCls[nline.status]
      const statsym = noteStatusSym[nline.status]
      const edit_att = ro ? "" : ' edit="1"'
      const edit_class = ro ? "" : " edit"
      html += `<tr class="nt_cmt nt_info ${statc}${edit_class}" note_id="${note_id}"
          clause_atom="${clause_atom}"${edit_att}">`
      if (ro) {
        html += `<td class="nt_stat">
            <span class="fa fa-${statsym} fa-fw" code="${nline.status}"></span>
          </td>`
        html += `<td class="keywords">${escHT(nline.keywords)}</td>`
        const ntext = specialLinks(markdown.toHTML(markdownEscape(nline.ntext)))
        html += `<td class="nt_cmt">${ntext}</td>`
        html += `<td class="nt_user" colspan="3" user_id="${user_id}">${escHT(user)}</td>`
        html += '<td class="nt_pub">'
        html += `<span class="ctli pradio fa fa-share-alt fa-fw ${sharedc}"
          title="shared?"></span>`
        html += `<span class="ctli pradio fa fa-quote-right fa-fw ${pubc}"
          title="published?"></span>`
      } else {
        this.editOld.push({ clause_atom, note: nline })
        html += `<td class="nt_stat">
          <a href="#" title="set status" class="fa fa-${statsym} fa-fw"
          code="${nline.status}"></a></td>`
        html += `<td class="keywords"><textarea>${nline.keywords}</textarea></td>`
        html += `<td class="nt_cmt"><textarea>${nline.ntext}</textarea></td>`
        html += `<td class="nt_user" colspan="3" user_id="{user_id}">${escHT(user)}</td>`
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

  gen_html(replace) {
    this.mnotes = 0
    if (replace) {
      this.dest.find("tr[clause_atom]").remove()
    }
    for (const clause_atom in this.notesOld) {
      const target = this.dest.find(`tr[clause_atom="${clause_atom}"]`)
      const html = this.gen_html_ca(clause_atom)
      target.after(html)
    }
    if (this.nnotes == 0) {
      this.noteCtrl.addClass("nt_empty")
    } else {
      this.noteCtrl.removeClass("nt_empty")
    }
    if (this.mnotes == 0) {
      this.noteCtrl.removeClass("nt_muted")
    } else {
      this.noteCtrl.addClass("nt_muted")
      this.msgn.msg(["special", `muted notes: ${this.mnotes}`])
    }
  }

  sendnotes(senddata) {
    const { verseNotesUrl } = Config

    $.post(
      verseNotesUrl,
      senddata,
      data => {
        const { good, users, notes, keyIndex, changed, loggedIn } = data
        this.msgn.clear()
        for (const m of data.msgs) {
          this.msgn.msg(m)
        }
        if (good) {
          this.dest.find("tr[clause_atom]").remove()
          this.process(users, notes, keyIndex, changed, loggedIn)
        }
      },
      "json"
    )
  }

  is_dirty() {
    let dirty = false
    const { editOld } = this
    if (editOld == undefined) {
      this.dirty = false
      return
    }
    for (let n = 0; n < editOld.length; n++) {
      const { clause_atom, note: noteOld } = editOld[n]
      const { note_id } = noteOld
      const n_note =
        note_id == 0
          ? this.dest.find(`tr[note_id="0"][clause_atom="${clause_atom}"]`)
          : this.dest.find(`tr[note_id="${note_id}"]`)
      const statusOld = noteOld.status
      const statusNew = n_note.find("td.nt_stat a").attr("code")
      const keywordsOld = $.trim(noteOld.keywords)
      const keywordsNew = $.trim(n_note.find("td.keywords textarea").val())
      const ntextOld = noteOld.ntext
      const ntextNew = $.trim(n_note.find("td.nt_cmt textarea").val())
      const is_sharedOld = noteOld.is_shared
      const isSharedNew = n_note.find("td.nt_pub a").first().hasClass("ison")
      const isPublishedOld = noteOld.is_published
      const isPublishedNew = n_note.find("td.nt_pub a").last().hasClass("ison")
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
    this.apply_dirty()
  }

  apply_dirty() {
    if (this.dirty) {
      this.noteCtrl.addClass("dirty")
    } else if (this.noteCtrl.hasClass("dirty")) {
      this.noteCtrl.removeClass("dirty")
    }
  }
  save() {
    this.edt = false
    const { version, book, chapter, verse, edt, editOld } = this
    const data = {
      version,
      book,
      chapter,
      verse,
      save: true,
      edit: edt,
    }
    const notelines = []
    if (editOld == undefined) {
      return
    }
    for (let n = 0; n < editOld.length; n++) {
      const { clause_atom, note: noteOld } = editOld[n]
      const { note_id, user_id } = noteOld
      const n_note =
        note_id == 0
          ? this.dest.find(`tr[note_id="0"][clause_atom="${clause_atom}"]`)
          : this.dest.find(`tr[note_id="${note_id}"]`)
      const statusOld = noteOld.status
      const statusNew = n_note.find("td.nt_stat a").attr("code")
      const keywordsOld = $.trim(noteOld.keywords)
      const keywordsNew = $.trim(n_note.find("td.keywords textarea").val())
      const ntextOld = noteOld.ntext
      const ntextNew = $.trim(n_note.find("td.nt_cmt textarea").val())
      const is_sharedOld = noteOld.is_shared
      const isSharedNew = n_note.find("td.nt_pub a").first().hasClass("ison")
      const isPublishedOld = noteOld.is_published
      const isPublishedNew = n_note.find("td.nt_pub a").last().hasClass("ison")
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
      this.msgn.msg(["warning", "No changes"])
    }
    this.sendnotes(data)
  }

  edit() {
    this.edt = true
    this.fetch(true)
  }

  revert() {
    this.edt = false
    const { version, book, chapter, verse, edt } = this
    const data = {
      version,
      book,
      chapter,
      verse,
      save: true,
      edit: edt,
    }
    data["notes"] = JSON.stringify([])
    this.sendnotes(data)
  }

  hide_notes() {
    this.show = false
    this.noteCtrl.removeClass("nt_loaded")
    this.sav_controls.hide()
    this.dest.find("tr.nt_cmt").hide()
    this.msgn.hide()
  }

  show_notes(adjust_verse) {
    this.show = true
    this.noteCtrl.addClass("nt_loaded")
    this.msgn.show()
    if (!this.loaded) {
      this.fetch(adjust_verse)
    } else {
      this.dest.find("tr.nt_cmt").show()
      if (this.loggedIn) {
        this.sav_controls.show()
        if (this.edt) {
          this.sav_c.show()
          this.edt_c.hide()
        } else {
          this.sav_c.hide()
          this.edt_c.show()
        }
      }
      if (P.mr == "m") {
        P.viewState.mstatesv({ verse: this.verse })
        P.material.goto_verse()
      }
    }
  }

  clear_msg() {
    this.msgn.clear()
  }
}
