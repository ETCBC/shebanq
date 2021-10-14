/* eslint-env jquery */
/* globals Config, markdown */

/**
 * @module helpers
 */

export const DOC_NAME = "0_home"
export const idPrefixNotes = "n"
export const idPrefixQueries = "q"

/**
 * Escape the `&` `<` `>` in strings that must be rendered as HTML.
 */
export const escHT = text => {
  const chr = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
  }
  return text.replace(/[&<>]/g, a => chr[a])
}

/**
 * Escape the `_` character in strings that must be rendered as markdown.
 */
const mEscape = ns => ns.replace(/_/g, "\\_")

export const markdownEscape = ntext =>
  ntext.replace(/\[[^\]\n\t]+\]\([^)]*\)/g, mEscape)

/**
 * Display markdown
 *
 * The markdown is formatted as HTML, where shebanq-specific links
 * are resolved into working hyperlinks.
 *
 * @param wdg A div in the HTML
 *
 * This div has a subdiv with the source markdown in it
 * and a destination div which gets the result of the conversion
 */
export const putMarkdown = wdg => {
  const did = wdg.attr("did")
  const src = $(`#dv_${did}`)
  const mdw = $(`#dm_${did}`)
  mdw.html(specialLinks(markdown.toHTML(src.val())))
}

/**
 * Hide and expand material
 */
export const toggleDetail = (wdg, detail, extra) => {
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

/**
 * Resolve shebanq-specific links into working hyperlinks
 */
export const specialLinks = mdIn => {
  const { featureHost, pageShareUrl } = Config

  let mdOut = mdIn
  mdOut = mdOut.replace(
    /<a [^>]*href=['"]image[\n\t ]+([^)\n\t '"]+)['"][^>]*>(.*?)(<\/a>)/g,
    '<br/><img src="$1"/><br/>$2<br/>'
  )
  mdOut = mdOut.replace(
    /(<a [^>]*)href=['"]([^)\n\t '"]+)[\n\t ]+([^:)\n\t '"]+):([^)\n\t '"]+)['"]([^>]*)>(.*?)(<\/a>)/g,
    '$1b="$2" c="$3" v="$4" href="#" class="fa fw" $5>&#xf100;$6&#xf101;$7'
  )
  mdOut = mdOut.replace(
    /(<a [^>]*)href=['"]([^)\n\t '"]+)[\n\t ]+([^)\n\t '"]+)['"]([^>]*)>(.*?)(<\/a>)/g,
    '$1b="$2" c="$3" v="1" href="#" class="fa fw" $4>&#xf100;$5&#xf101;$6'
  )
  mdOut = mdOut.replace(
    /(href=['"])shebanq:([^)\n\t '"]+)(['"])/g,
    `$1${pageShareUrl}$2$3 class="fa fw fa-bookmark" `
  )
  mdOut = mdOut.replace(
    /(href=['"])feature:([^)\n\t '"]+)(['"])/g,
    `$1${featureHost}/$2$3 target="_blank" class="fa fw fa-file-text" `
  )
  mdOut = mdOut.replace(
    /\[([^\]\n\t]+)\]\(image[\n\t ]+([^)\n\t '"]+)\)/g,
    '<br/><img src="$2"/><br/>$1<br/>'
  )
  mdOut = mdOut.replace(
    /\[([^\]\n\t]+)\]\(([^)\n\t '"]+)[\n\t ]+([^:)\n\t '"]+):([^)\n\t '"]+)\)/g,
    '<a b="$2" c="$3" v="$4" href="#" class="fa fw">&#xf100;$1&#xf101;</a>'
  )
  mdOut = mdOut.replace(
    /\[([^\]\n\t]+)\]\(([^)\n\t '"]+)[\n\t ]+([^)\n\t '"]+)\)/g,
    '<a b="$2" c="$3" v="1" href="#" class="fa fw">&#xf100;$1&#xf101;</a>'
  )
  mdOut = mdOut.replace(
    /\[([^\]\n\t]+)\]\(shebanq:([^)\n\t '"]+)\)/g,
    `<a href="${pageShareUrl}$2" class="fa fw">&#xf02e;$1</a>`
  )
  mdOut = mdOut.replace(
    /\[([^\]\n\t]+)\]\(feature:([^)\n\t '"]+)\)/g,
    `<a target="_blank" href="${featureHost}/$2" class="fa fw">$1&#xf15c;</a>`
  )
  mdOut = mdOut.replace(
    /\[([^\]\n\t]+)\]\(([^)\n\t '"]+)\)/g,
    '<a target="_blank" href="$2" class="fa fw">$1&#xf08e;</a>'
  )
  return mdOut
}

/**
 * Computes the default color
 *
 * The data for the computation comes from the server
 * and is stored in the javascript global variable Config
 * colorsDefault, nDefaultClrCols, nDefaultClrRows
 */
export const colorDefault = (qw, iid) => {
  const { itemStyle, colorsDefault, nDefaultClrCols, nDefaultClrRows } = Config

  let result
  if (qw in itemStyle) {
    result = itemStyle[qw]["default"]
  } else if (qw) {
    const mod = iid % colorsDefault.length
    result =
      colorsDefault[
        nDefaultClrCols * (mod % nDefaultClrRows) + Math.floor(mod / nDefaultClrRows)
      ]
  } else {
    const iidstr = iid == null ? "" : iid
    let sumiid = 0
    for (let i = 0; i < iidstr.length; i++) {
      sumiid += iidstr.charCodeAt(i)
    }
    const mod = sumiid % colorsDefault.length
    result =
      colorsDefault[
        nDefaultClrCols * (mod % nDefaultClrRows) + Math.floor(mod / nDefaultClrRows)
      ]
  }
  return result
}

/**
 * Close a dialog box
 */
export const closeDialog = dia => {
  const wasOpen = Boolean(
    dia && dia.length && dia.dialog("instance") && dia.dialog("isOpen")
  )
  if (wasOpen) {
    dia.dialog("close")
  }
  return wasOpen
}
