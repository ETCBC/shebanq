/* eslint-env jquery */
/* globals Config, P, L, markdown */

import { escHT, special_links, markdownEscape } from "./helpers.js"
import { Msg } from "./msg.js"

export class Notes {
  constructor(newcontent) {
    this.show = false
    this.verselist = {}
    this.version = P.version
    this.sav_controls = $("span.nt_main_sav")
    this.sav_c = this.sav_controls.find('a[tp="s"]')
    this.rev_c = this.sav_controls.find('a[tp="r"]')
    this.logged_in = false
    this.cctrl = $("a.nt_main_ctrl")

    newcontent.find(".vradio").each((i, el) => {
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
        topl.find("span.nt_ctrl"),
        topl.find("table.t1_table")
      )
    })
    const { verselist } = this
    this.msgn = new Msg("nt_main_msg", () => {
      for (const notev of Object.values(verselist)) {
        notev.clear_msg()
      }
    })
    this.cctrl.click(e => {
      e.preventDefault()
      P.vs.hstatesv("n", { get: P.vs.get("n") == "v" ? "x" : "v" })
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

    if (P.vs.get("n") == "v") {
      this.cctrl.addClass("nt_loaded")
      for (const notev of Object.values(verselist)) {
        notev.show_notes(false)
        this.logged_in = notev.logged_in
      }
      if (this.logged_in) {
        this.sav_controls.show()
      }
    } else {
      this.cctrl.removeClass("nt_loaded")
      this.sav_controls.hide()
      for (const notev of Object.values(verselist)) {
        notev.hide_notes()
      }
    }
  }
}

class Notev {
  constructor(vr, bk, ch, vs, ctrl, dest) {
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
    this.ctrl = ctrl
    this.dest = dest

    const { book, chapter, verse } = this
    this.msgn = new Msg(`nt_msg_${book}_${chapter}_${verse}`)
    this.cctrl = ctrl.find("a.nt_ctrl")
    this.sav_controls = ctrl.find("span.nt_sav")

    const { sav_controls } = this
    this.sav_c = sav_controls.find('a[tp="s"]')
    this.edt_c = sav_controls.find('a[tp="e"]')
    this.rev_c = sav_controls.find('a[tp="r"]')

    const { sav_c, edt_c, rev_c, cctrl } = this

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
    cctrl.click(e => {
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
    const { cnotes_url } = Config

    const { version, book, chapter, verse, edt, msgn } = this
    const senddata = { version, book, chapter, verse, edit: edt }
    msgn.msg(["info", "fetching notes ..."])
    $.post(cnotes_url, senddata, data => {
      this.loaded = true
      msgn.clear()
      for (const m of data.msgs) {
        msgn.msg(m)
      }
      const { good, users, notes, nkey_index, changed, logged_in } = data
      if (good) {
        this.process(users, notes, nkey_index, changed, logged_in)
        if (adjust_verse) {
          if (P.mr == "m") {
            P.vs.mstatesv({ verse })
            P.material.goto_verse()
          }
        }
      }
    })
  }

  process(users, notes, nkey_index, changed, logged_in) {
    const {
      sidebars: { side_fetched, sidebar },
    } = P
    if (changed) {
      if (P.mr == "m") {
        side_fetched["mn"] = false
        sidebar["mn"].content.apply()
      }
    }
    this.orig_users = users
    this.orig_notes = notes
    this.orig_nkey_index = nkey_index
    this.orig_edit = []
    this.logged_in = logged_in
    this.gen_html(true)
    this.dirty = false
    this.apply_dirty()
    this.decorate()
  }

  decorate() {
    const { nt_statclass, nt_statsym, nt_statnext } = Config
    const { dest, logged_in, sav_controls, edt, sav_c, edt_c } = this
    dest
      .find("td.nt_stat")
      .find("a")
      .click(e => {
        e.preventDefault()
        const elem = $(e.delegateTarget)
        const statcode = elem.attr("code")
        const nextcode = nt_statnext[statcode]
        const nextsym = nt_statsym[nextcode]
        const row = elem.closest("tr")
        for (const c in nt_statclass) {
          row.removeClass(nt_statclass[c])
        }
        for (const c in nt_statsym) {
          elem.removeClass(`fa-${nt_statsym[c]}`)
        }
        row.addClass(nt_statclass[nextcode])
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
    if (logged_in) {
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

  gen_html_ca(canr) {
    const { nt_statclass, nt_statsym } = Config
    const { muting_n } = L
    const vr = this.version
    const notes = this.orig_notes[canr]
    const nkey_index = this.orig_nkey_index
    let html = ""
    this.nnotes += notes.length
    for (let n = 0; n < notes.length; n++) {
      const nline = notes[n]
      const { uid, nid, pub, shared, ro } = nline
      const kwtrim = $.trim(nline.kw)
      const kws = kwtrim.split(/\s+/)
      let mute = false
      for (const kw of kws) {
        const nkid = nkey_index[`${uid} ${kw}`]
        if (muting_n.isSet(`n${nkid}`)) {
          mute = true
          break
        }
      }
      if (mute) {
        this.mnotes += 1
        continue
      }
      const user = this.orig_users[uid]
      const pubc = pub ? "ison" : ""
      const sharedc = shared ? "ison" : ""
      const statc = nt_statclass[nline.stat]
      const statsym = nt_statsym[nline.stat]
      const edit_att = ro ? "" : ' edit="1"'
      const edit_class = ro ? "" : " edit"
      html += `<tr class="nt_cmt nt_info ${statc}${edit_class}" nid="${nid}"
          ncanr="${canr}"${edit_att}">`
      if (ro) {
        html += `<td class="nt_stat">
            <span class="fa fa-${statsym} fa-fw" code="${nline.stat}"></span>
          </td>`
        html += `<td class="nt_kw">${escHT(nline.kw)}</td>`
        const ntxt = special_links(markdown.toHTML(markdownEscape(nline.ntxt)))
        html += `<td class="nt_cmt">${ntxt}</td>`
        html += `<td class="nt_user" colspan="3" uid="${uid}">${escHT(user)}</td>`
        html += '<td class="nt_pub">'
        html += `<span class="ctrli pradio fa fa-share-alt fa-fw ${sharedc}"
          title="shared?"></span>`
        html += `<span class="ctrli pradio fa fa-quote-right fa-fw ${pubc}"
          title="published?"></span>`
      } else {
        this.orig_edit.push({ canr, note: nline })
        html += `<td class="nt_stat">
          <a href="#" title="set status" class="fa fa-${statsym} fa-fw"
          code="${nline.stat}"></a></td>`
        html += `<td class="nt_kw"><textarea>${nline.kw}</textarea></td>`
        html += `<td class="nt_cmt"><textarea>${nline.ntxt}</textarea></td>`
        html += `<td class="nt_user" colspan="3" uid="{uid}">${escHT(user)}</td>`
        html += '<td class="nt_pub">'
        html += `<a class="ctrli pradio fa fa-share-alt fa-fw ${sharedc}"
          href="#" title="shared?"></a>`
        html += `<span>${vr}</span>`
        html += `<a class="ctrli pradio fa fa-quote-right fa-fw ${pubc}"
          href="#" title="published?"></a>`
      }
      html += "</td></tr>"
    }
    return html
  }

  gen_html(replace) {
    this.mnotes = 0
    if (replace) {
      this.dest.find("tr[ncanr]").remove()
    }
    for (const canr in this.orig_notes) {
      const target = this.dest.find(`tr[canr="${canr}"]`)
      const html = this.gen_html_ca(canr)
      target.after(html)
    }
    if (this.nnotes == 0) {
      this.cctrl.addClass("nt_empty")
    } else {
      this.cctrl.removeClass("nt_empty")
    }
    if (this.mnotes == 0) {
      this.cctrl.removeClass("nt_muted")
    } else {
      this.cctrl.addClass("nt_muted")
      this.msgn.msg(["special", `muted notes: ${this.mnotes}`])
    }
  }

  sendnotes(senddata) {
    const { cnotes_url } = Config

    $.post(
      cnotes_url,
      senddata,
      data => {
        const { good, users, notes, nkey_index, changed, logged_in } = data
        this.msgn.clear()
        for (const m of data.msgs) {
          this.msgn.msg(m)
        }
        if (good) {
          this.dest.find("tr[ncanr]").remove()
          this.process(users, notes, nkey_index, changed, logged_in)
        }
      },
      "json"
    )
  }

  is_dirty() {
    let dirty = false
    const { orig_edit } = this
    if (orig_edit == undefined) {
      this.dirty = false
      return
    }
    for (let n = 0; n < orig_edit.length; n++) {
      const { canr, note: o_note } = orig_edit[n]
      const { nid } = o_note
      const n_note =
        nid == 0
          ? this.dest.find(`tr[nid="0"][ncanr="${canr}"]`)
          : this.dest.find(`tr[nid="${nid}"]`)
      const o_stat = o_note.stat
      const n_stat = n_note.find("td.nt_stat a").attr("code")
      const o_kw = $.trim(o_note.kw)
      const n_kw = $.trim(n_note.find("td.nt_kw textarea").val())
      const o_ntxt = o_note.ntxt
      const n_ntxt = $.trim(n_note.find("td.nt_cmt textarea").val())
      const o_shared = o_note.shared
      const n_shared = n_note.find("td.nt_pub a").first().hasClass("ison")
      const o_pub = o_note.pub
      const n_pub = n_note.find("td.nt_pub a").last().hasClass("ison")
      if (
        o_stat != n_stat ||
        o_kw != n_kw ||
        o_ntxt != n_ntxt ||
        o_shared != n_shared ||
        o_pub != n_pub
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
      this.cctrl.addClass("dirty")
    } else if (this.cctrl.hasClass("dirty")) {
      this.cctrl.removeClass("dirty")
    }
  }
  save() {
    this.edt = false
    const { version, book, chapter, verse, edt, orig_edit } = this
    const data = {
      version,
      book,
      chapter,
      verse,
      save: true,
      edit: edt,
    }
    const notelines = []
    if (orig_edit == undefined) {
      return
    }
    for (let n = 0; n < orig_edit.length; n++) {
      const { canr, note: o_note } = orig_edit[n]
      const { nid, uid } = o_note
      const n_note =
        nid == 0
          ? this.dest.find(`tr[nid="0"][ncanr="${canr}"]`)
          : this.dest.find(`tr[nid="${nid}"]`)
      const o_stat = o_note.stat
      const n_stat = n_note.find("td.nt_stat a").attr("code")
      const o_kw = $.trim(o_note.kw)
      const n_kw = $.trim(n_note.find("td.nt_kw textarea").val())
      const o_ntxt = o_note.ntxt
      const n_ntxt = $.trim(n_note.find("td.nt_cmt textarea").val())
      const o_shared = o_note.shared
      const n_shared = n_note.find("td.nt_pub a").first().hasClass("ison")
      const o_pub = o_note.pub
      const n_pub = n_note.find("td.nt_pub a").last().hasClass("ison")
      if (
        o_stat != n_stat ||
        o_kw != n_kw ||
        o_ntxt != n_ntxt ||
        o_shared != n_shared ||
        o_pub != n_pub
      ) {
        notelines.push({
          nid,
          canr,
          stat: n_stat,
          kw: n_kw,
          ntxt: n_ntxt,
          uid,
          shared: n_shared,
          pub: n_pub,
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
    this.cctrl.removeClass("nt_loaded")
    this.sav_controls.hide()
    this.dest.find("tr.nt_cmt").hide()
    this.msgn.hide()
  }

  show_notes(adjust_verse) {
    this.show = true
    this.cctrl.addClass("nt_loaded")
    this.msgn.show()
    if (!this.loaded) {
      this.fetch(adjust_verse)
    } else {
      this.dest.find("tr.nt_cmt").show()
      if (this.logged_in) {
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
        P.vs.mstatesv({ verse: this.verse })
        P.material.goto_verse()
      }
    }
  }

  clear_msg() {
    this.msgn.clear()
  }
}
