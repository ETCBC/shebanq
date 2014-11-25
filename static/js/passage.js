function replace_select_options(selectBox, last_chapter_num) {
    $(selectBox).empty()
    for(var i=1; i<=last_chapter_num; i++){
        $(selectBox)
            .append($("<option></option>")
            .attr("value", i)
            .text(i))
    }
}

function get_last_chapter_num() {
    $("select#verses_form_Book").change(function () {
        ajax('last_chapter_num', ['Book'], ':eval')
    })

    $(document).ajaxComplete(function(event, xhr, settings) {
        if (settings.url === 'last_chapter_num') {
            replace_select_options('#verses_form_Chapter', xhr.responseText)
        }
    })
}


$(document).ready(function () {
    get_last_chapter_num()
})

$.cookie.raw = false
$.cookie.json = true
$.cookie.defaults.expires = 30
$.cookie.defaults.path = '/'

var vcolors, viewstate, style, pagekind, queriesfetched
var thebook, thechapter, thevid, themonads
var view_url, query_url, rpage_url

function getvars() {
    var vars = ''
    var sep = '?'
    var comps = {id: thevid, book: thebook, chapter: thechapter}
    for (name in comps) {
        val = comps[name]
        if (val) {
            vars += sep+name+"="+val
            sep = '&'
        }
    }
    for (group in viewstate) {
        for (k in viewstate[group]) {
            for (name in viewstate[group][k]) {
                vars += sep+k+name+'='+viewstate[group][k][name] 
                sep = '&'
            }
        }
    }
    return vars
}

function savestate(group, k) {
    $.cookie(group+k, viewstate[group][k])
}

function init_page() {
    if (pagekind == 'passage') {
        if (thechapter != 0) {
            init_hebrewdata()
            init_hlpickers()
            init_sidelists()
            init_hlview()
        }
    }
    else {
        init_hebrewdata()
        init_onepickers()
    }
    init_viewlink()
}

function adjust_height() {
    subtract = (pagekind == 'query')?350:(pagekind == 'word')?350:400
    target = (pagekind == 'query')?$('#qresults'):(pagekind == 'word')?$('#wresults'):$('#presults')
    target.css('height', (window.innerHeight - subtract)+'px')
}

function refresh_verses() {
    if (pagekind == 'passage') {
        refresh_hebrewdata()
        refresh_hlview()
    }
    else {
        if (pagekind == 'query') {
            refresh_pagenav()
        }
        refresh_oneview()
    }
    adjust_height()
}

function refresh_pagenav() {
    var pagelinks = $('.rpnav')
    themonads = $.parseJSON($('#rpmonads').val())
    refresh_hebrewdata()
    pagelinks.each(function() {
        refresh_thispagenav($(this))
    })
}

function refresh_thispagenav(rp) {
    var vid = rp.attr('vid')
    var page = rp.attr('page')
    rp.click(function() {
        $('#rlist').load(rpage_url+'?id='+vid+'&page='+page+ '#rpresult', function (response, stats, xhr) {
            refresh_verses()
        }, 'html')
    })
}

function init_hebrewdata() {
    var settings = viewstate['hebrewdata']['']
    for (fld in settings) {
        init_hebrewdatafield(fld, settings[fld])
    }
}

function init_hebrewdatafield(fld, val) {
    var settings = viewstate['hebrewdata']['']
    $('#'+fld).prop('checked', val == 'v')
    $('#'+fld).click(function() {
        $('.'+fld).each(function () {
            $(this).toggle()
        })
        settings[fld] = $(this).prop('checked')?'v':'x'
        savestate('hebrewdata','')
    })
}

function refresh_hebrewdata() {
    var settings = viewstate['hebrewdata']['']
    var do_text = settings['txt_p']
    var do_data = settings['txt_il']
    for (fld in settings) {
        refresh_hebrewdatafield(fld, settings[fld])
    }
}

function refresh_hebrewdatafield(fld, val) {
    var settings = viewstate['hebrewdata']['']
    $('.'+fld).each(function (i) {
        if (val == 'x') {
            $(this).hide()
        }
        else {
            $(this).show()
        }
    })
}

function init_hlpickers() {
    for (k in viewstate['hlview']) {
        jscolorpicker2(k, 'one')
    }
}

function init_onepickers() {
    k = (pagekind == 'query')?'q':'w'
    jscolorpicker(k, thevid)
}

function init_sidelists() {
    for (k in viewstate['hlview']) {
        init_sidelist(k)
    }
}

function init_sidelist(k) {
    var klistn = (k == 'q')?'queries':'words'
    var hidelist = $('#h_'+klistn)
    var showlist = $('#s_'+klistn)
    var thelist = $('#'+k+'bar')
    if (k == 'q') {
        queriesfetched = false
    }
    showlist.click(function(){
        if (k == 'q') {
            if (!queriesfetched) {
                thelist.load(query_url, function () {
                    queriesfetched = true
                    init_sidelistitems(k)
                    refresh_hlview()
                }, 'html')
            }
        }
        hidelist.show()
        thelist.show()
        showlist.hide()
        viewstate['hlview'][k]['get'] = 'v'
        savestate('hlview',k)
    })
    hidelist.click(function(){
        showlist.show()
        thelist.hide()
        hidelist.hide()
        viewstate['hlview'][k]['get'] = 'x'
        savestate('hlview',k)
    })
    if (viewstate['hlview'][k]['get'] == 'v') {
        showlist.click()
        if (k != 'q') {
            init_sidelistitems(k)
        }
    }
    else {
        hidelist.hide()
        thelist.hide()
    }
}

function init_sidelistitems(k) {
    var klist = $('#'+((k=='q')?'queries':'words')+' li')
    klist.each(function(index, item) {
        var vid = $(item).attr('vid')
        init_sidelistitem(k, vid)
        jscolorpicker(k, vid)
    })
}

function init_sidelistitem(k,vid) {
    var more = $('#m_'+k+vid) 
    var head = $('#h_'+k+vid) 
    var desc = $('#d_'+k+vid) 
    desc.hide()
    more.click(function() {
        desc.toggle()
    })
}

function init_hlview() {
    for (k in viewstate['hlview']) {
        init_highlight(k)
    }
}

function refresh_hlview() {
    for (k in viewstate['hlview']) {
        change_hlview(k)
    }
}

function refresh_oneview() {
    if (thevid) {
        add_highlights((pagekind == 'query')?'q':'w', thevid, null)
    }
}

function change_hlview(k, picked) {
    var activen = viewstate['hlview'][k]['active']
    var active = $('#'+k+activen)
    var klist = $('#'+((k=='q')?'queries':'words')+' li')
    var selo = $('#sel'+k+'_one')
    var hlradio = $('.'+k+'hradio')
    var hloff = $('#'+k+'hloff')
    var hlone = $('#'+k+'hlone')
    var hlcustom = $('#'+k+'hlcustom')
    var hlmany = $('#'+k+'hlmany')
    var hlreset = $('#'+k+'hlreset')
    var stl = style[k]['prop']
    var selclr = selo.css(stl)

    if (picked && activen != 'hlcustom' && activen != 'hlone') {
        viewstate['hlview'][k]['active'] = 'hlcustom'
        activen = 'hlcustom'
        active = $('#'+k+activen)
    }
    hlradio.removeClass('ison')
    active.addClass('ison')

    if (activen == 'hloff') {
        klist.each(function(index, item) {
            add_highlights(k, $(item).attr('vid'), style[k]['off'])
        })
    }
    else if (activen == 'hlone') {
        klist.each(function(index, item) {
            add_highlights(k, $(item).attr('vid'), selclr)
        })
    }
    else if (activen == 'hlcustom') {
        var cmap = viewstate['cmap'][k]
        klist.each(function(index, item) {
            var vid =  $(item).attr('vid')
            add_highlights(k, vid, (vid in cmap)?null:selclr)
        })
    }
    else if (activen =='hlmany') {
        klist.each(function(index, item) {
            add_highlights(k, $(item).attr('vid'), null)
        })
    }
    else if (activen == 'hlreset') {
        hlreset.removeClass('ison')
        hlcustom.addClass('ison')
        var selclr2 = selo.attr('defn')
        selo.css(stl, vcolors[selclr2][k])
        viewstate['hlview'][k]['active'] = 'hlcustom'
        viewstate['hlview'][k]['sel_one'] = selclr2
        viewstate['cmap'][k] = {}
        klist.each(function(index, item) {
            var vid =  $(item).attr('vid')
            var sel = $('#sel'+k+'_'+vid)
            var selc = $('#selc'+k+'_'+vid)
            var selclr = sel.attr('defn')
            sel.css(stl, vcolors[selclr][k])
            selc.prop('checked', false)
            add_highlights(k, vid, vcolors[selclr2][k])
        })
        /*klist.each(function(index, item) {
            var vid = $(item).attr('vid')
            var sel = $('#sel'+k+'_'+vid)
            var selc = $('#selc'+k+'_'+vid)
            var selclr = vcolors[sel.attr('defn')][k]
            sel.css(stl, selclr)
            selc.prop('checked', false)
            add_highlights(k, vid, selclr)
        })
        */
    }
}

function init_highlight(k) {
    $('.'+k+'hradio').click(function() {
        viewstate['hlview'][k]['active'] = $(this).attr('id').substring(1)
        change_hlview(k)
        savestate('hlview',k)
    })
}

function init_viewlink() {
    $("#cviewlink").hide()
    $("#xviewlink").hide()

    $("#xviewlink").click(function() {
        $("#cviewlink").hide()
        $("#xviewlink").hide()
        $("#yviewlink").show()
    })
    $("#yviewlink").click(function() {
        $("#yviewlink").hide()
        $("#xviewlink").show()
        $('#cviewlink').val(view_url+getvars())
        $('#cviewlink').each(function() {
            $(this).show()
            $(this).select()
        })
    })
    $('#cviewlink').val(view_url+getvars())
}

function jscolorpicker(k, vid) {
    var sel = $('#sel'+k+'_'+vid)
    var selc = $('#selc'+k+'_'+vid)
    var picker = $('#picker'+k+'_'+vid)
    var stl = style[k]['prop']
    picker.hide()
    sel.click(function() {
        picker.dialog({
            dialogClass: 'cpickerd',
            closeOnEscape: true,
            modal: true,
            title: 'choose a color',
            position: {my: 'right top', at: 'left top', of: selc},
            width: '200px',
        })
    })
    selc.click(function() {
        picker.dialog('close')
        var was_cust = vid in viewstate['cmap'][k]
        if (was_cust) {
            sel.css(stl, vcolors[sel.attr('defn')][k])
            delete viewstate['cmap'][k][vid]
        }
        else {
            viewstate['cmap'][k][vid] = sel.attr('defn')
        }
        selc.prop('checked', vid in viewstate['cmap'][k])
        change_highlight(k, vid)
        savestate('cmap', k)
    })
    $('.cc.'+k+vid).click(function() {
        picker.dialog('close')
        sel.css(stl, $(this).css(stl))
        viewstate['cmap'][k][vid] = $(this).html()
        selc.prop('checked', true)
        change_highlight(k, vid)
        savestate('cmap', k)
    })
    var colorn = viewstate['cmap'][k][vid]
    if (colorn == undefined) {colorn = sel.attr('defn')}
    $('.cc.'+k+vid).each(function() {$(this).css(stl, vcolors[$(this).html()][k])})
    sel.css(stl, vcolors[colorn][k])
    selc.prop('checked', vid in viewstate['cmap'][k])
}

function jscolorpicker2(k, lab) {
    var sel = $('#sel'+k+'_'+lab)
    var picker = $('#picker'+k+'_'+lab)
    var stl = style[k]['prop']
    picker.hide()
    sel.click(function() {
        picker.dialog({
            dialogClass: 'cpickerd',
            closeOnEscape: true,
            modal: true,
            title: 'choose a color',
            position: {my: 'right top', at: 'left top', of: sel},
            width: '200px',
        })
    })
    $('.cc.'+k+lab).click(function() {
        picker.dialog('close')
        sel.css(stl, $(this).css(stl))
        viewstate['hlview'][k]['sel_'+lab] = $(this).html()
        change_hlview(k, true)
        savestate('hlview',k)
    })
    var colorn = viewstate['hlview'][k]['sel_'+lab]
    if (colorn == undefined) {colorn = sel.attr('defn')}
    $('.cc.'+k+lab).each(function() {$(this).css(stl, vcolors[$(this).html()][k])})
    sel.css(stl, vcolors[colorn][k])
}

function change_highlight(k, vid) {
    var sel = $('#sel'+k+'_'+vid)
    var selo = $('#sel'+k+'_one')
    var hlcustom = $('#'+k+'hlcustom')
    var hlmany = $('#'+k+'hlmany')
    var defc = sel.attr('defc')
    var defn = sel.attr('defn')
    var iscust = vid in viewstate['cmap'][k]
    var stl = style[k]['prop']
    if (!hlcustom || hlcustom.html() == undefined) {
        add_highlights(k, vid, null)
    }
    else {
        var hlcustomon = hlcustom.hasClass('ison') 
        var hlmanyon = hlmany.hasClass('ison') 
        if (hlmanyon || hlcustomon) {
            if (hlmanyon) {
                add_highlights(k, vid, null)
            }
            else {
                if (iscust) {
                    add_highlights(k, vid, null)
                }
                else {
                    selclr = selo.css(stl)
                    add_highlights(k, vid, selclr)
                }
            }
        }
    }
}

function add_highlights(k, vid, clr) {
    var monads = (pagekind == 'passage')? $.parseJSON($('#'+k+vid).attr('monads')) : themonads
    var stl = style[k]['prop']

    var hc = (clr == null)? $('#sel'+k+'_'+vid).css(stl) : clr
    $.each(monads, function(index, item) {
        $('span[m="'+item+'"]').css(stl, hc)
    })
}

