/* eslint-env jquery */
/* globals Config, markdown */

export const escHT = text => {
  const chr = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
  }
  return text.replace(/[&<>]/g, a => chr[a])
}

const mEscape = ns => ns.replace(/_/g, "\\_")

export const markdownEscape = ntxt => ntxt.replace(/\[[^\]\n\t]+\]\([^)]*\)/g, mEscape)

export const put_markdown = wdg => {
  const did = wdg.attr("did")
  const src = $(`#dv_${did}`)
  const mdw = $(`#dm_${did}`)
  mdw.html(special_links(markdown.toHTML(src.val())))
}

export const toggle_detail = (wdg, detail, extra) => {
  const thedetail = detail == undefined ? wdg.closest("div").find(".detail") : detail
  thedetail.toggle()
  if (extra != undefined) {
    extra(wdg)
  }
  let thiscl, othercl
  if (wdg.hasClass("fa-chevron-right")) {
    thiscl = "fa-chevron-right"
    othercl = "fa-chevron-down"
  } else {
    thiscl = "fa-chevron-down"
    othercl = "fa-chevron-right"
  }
  wdg.removeClass(thiscl)
  wdg.addClass(othercl)
}

export const special_links = d_mdGiven => {
  const { featurehost, host } = Config

  let d_md = d_mdGiven
  d_md = d_md.replace(
    /<a [^>]*href=['"]image[\n\t ]+([^)\n\t '"]+)['"][^>]*>(.*?)(<\/a>)/g,
    '<br/><img src="$1"/><br/>$2<br/>'
  )
  d_md = d_md.replace(
    /(<a [^>]*)href=['"]([^)\n\t '"]+)[\n\t ]+([^:)\n\t '"]+):([^)\n\t '"]+)['"]([^>]*)>(.*?)(<\/a>)/g,
    '$1b="$2" c="$3" v="$4" href="#" class="fa fw" $5>&#xf100;$6&#xf101;$7'
  )
  d_md = d_md.replace(
    /(<a [^>]*)href=['"]([^)\n\t '"]+)[\n\t ]+([^)\n\t '"]+)['"]([^>]*)>(.*?)(<\/a>)/g,
    '$1b="$2" c="$3" v="1" href="#" class="fa fw" $4>&#xf100;$5&#xf101;$6'
  )
  d_md = d_md.replace(
    /(href=['"])shebanq:([^)\n\t '"]+)(['"])/g,
    `$1${host}$2$3 class="fa fw fa-bookmark" `
  )
  d_md = d_md.replace(
    /(href=['"])feature:([^)\n\t '"]+)(['"])/g,
    `$1${featurehost}/$2$3 target="_blank" class="fa fw fa-file-text" `
  )
  d_md = d_md.replace(
    /\[([^\]\n\t]+)\]\(image[\n\t ]+([^)\n\t '"]+)\)/g,
    '<br/><img src="$2"/><br/>$1<br/>'
  )
  d_md = d_md.replace(
    /\[([^\]\n\t]+)\]\(([^)\n\t '"]+)[\n\t ]+([^:)\n\t '"]+):([^)\n\t '"]+)\)/g,
    '<a b="$2" c="$3" v="$4" href="#" class="fa fw">&#xf100;$1&#xf101;</a>'
  )
  d_md = d_md.replace(
    /\[([^\]\n\t]+)\]\(([^)\n\t '"]+)[\n\t ]+([^)\n\t '"]+)\)/g,
    '<a b="$2" c="$3" v="1" href="#" class="fa fw">&#xf100;$1&#xf101;</a>'
  )
  d_md = d_md.replace(
    /\[([^\]\n\t]+)\]\(shebanq:([^)\n\t '"]+)\)/g,
    `<a href="${host}$2" class="fa fw">&#xf02e;$1</a>`
  )
  d_md = d_md.replace(
    /\[([^\]\n\t]+)\]\(feature:([^)\n\t '"]+)\)/g,
    `<a target="_blank" href="${featurehost}/$2" class="fa fw">$1&#xf15c;</a>`
  )
  d_md = d_md.replace(
    /\[([^\]\n\t]+)\]\(([^)\n\t '"]+)\)/g,
    '<a target="_blank" href="$2" class="fa fw">$1&#xf08e;</a>'
  )
  return d_md
}

export const defcolor = (qw, iid) => {
  /* compute the default color
   *
   * The data for the computation comes from the server
   * and is stored in the javascript global variable Config
   * vdefaultcolors, dncols, dnrows
   */
  const { style, vdefaultcolors, dncols, dnrows } = Config

  let result
  if (qw in style) {
    result = style[qw]["default"]
  } else if (qw) {
    const mod = iid % vdefaultcolors.length
    result = vdefaultcolors[dncols * (mod % dnrows) + Math.floor(mod / dnrows)]
  } else {
    const iidstr = iid == null ? "" : iid
    let sumiid = 0
    for (let i = 0; i < iidstr.length; i++) {
      sumiid += iidstr.charCodeAt(i)
    }
    const mod = sumiid % vdefaultcolors.length
    result = vdefaultcolors[dncols * (mod % dnrows) + Math.floor(mod / dnrows)]
  }
  return result
}

export const close_dialog = dia => {
  const was_open = Boolean(
    dia && dia.length && dia.dialog("instance") && dia.dialog("isOpen")
  )
  if (was_open) {
    dia.dialog("close")
  }
  return was_open
}


