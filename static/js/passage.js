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

var vcolors, viewstate, style, pagekind, view_url, thebook, thechapter, thevid, themonads

function getvars() {
    var vars = ''
    for (group in viewstate) {
        for (k in viewstate[group]) {
            for (name in viewstate[group][k]) {
                vars += '&'+k+name+'='+viewstate[group][k][name] 
            }
        }
    }
    return vars
}

function savestate(group, k) {
    $.cookie(group+k, viewstate[group][k])
}

function init_page() {
    if (pagekind != 'passage' || thechapter != 0) {
        init_hebrewdata()
        init_pickers()
        init_sidelists()
        if (pagekind == 'passage') {
            init_hlview()
        }
        init_viewlink()
    }
}

function init_subpage() {
    init_hebrewdata()
    init_pickers()
    init_hlview()
    init_viewlink()
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
    if (val == 'x') {
        $('.'+fld).each(function () {
            $(this).toggle()
        })
    }
    $('#'+fld).click(function() {
        $('.'+fld).each(function () {
            $(this).toggle()
        })
        settings[fld] = $(this).prop('checked')?'v':'x'
        savestate('hebrewdata','')
    })
}

function init_pickers() {
    if (pagekind == 'passage') {
        for (k in viewstate['hlview']) {
            jscolorpicker2(k, 'one')
        }
    }
    else {
        k = (pagekind == 'query')?'q':'w'
        jscolorpicker(k, thevid)
    }
}

function init_sidelists() {
    if (pagekind == 'passage') {
        for (k in viewstate['hlview']) {
            init_sidelist(k)
        }
    }
}

function init_sidelist(k) {
    var klistn = (k == 'q')?'queries':'words'
    var hidelist = $('#h_'+klistn)
    var showlist = $('#s_'+klistn)
    var thelist = $('#'+k+'bar')
    showlist.click(function(){
        hidelist.show()
        thelist.show()
        showlist.hide()
        init_sidelistitems(k)
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
        showlist.hide()
        if (k == 'q') {
            $('#fetchqueries').click()
        }
        init_sidelistitems(k)
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
    if (pagekind == 'passage') {
        for (k in viewstate['hlview']) {
            init_highlight(k)
            change_hlview(k)
        }
    }
    else {
        add_highlights((pagekind == 'query')?'q':'w', thevid, null)
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
        picker.show()
    })
    selc.click(function() {
        picker.hide()
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
        picker.hide()
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
        picker.show()
    })
    $('.cc.'+k+lab).click(function() {
        picker.hide()
        sel.css(stl, $(this).css(stl))
        viewstate['hlview'][k]['sel_'+lab] = $(this).html()
        change_hlview(k)
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
    var hlmy = $('#'+k+'hlmy')
    var hlmany = $('#'+k+'hlmany')
    var defc = sel.attr('defc')
    var defn = sel.attr('defn')
    var iscust = vid in viewstate['cmap'][k]
    var stl = style[k]['prop']
    if (!hlmy || hlmy.html() == undefined) {
        add_highlights(k, vid, null)
    }
    else {
        var hlmyon = hlmy.hasClass('ison') 
        var hlmanyon = hlmany.hasClass('ison') 
        if (hlmanyon || hlmyon) {
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

function change_hlview(k) {
    var activen = viewstate['hlview'][k]['active']
    var active = $('#'+k+activen)
    var klist = $('#'+((k=='q')?'queries':'words')+' li')
    var sel = $('#sel'+k+'_one')
    var hlradio = $('.'+k+'hradio')
    var hloff = $('#'+k+'hloff')
    var hlone = $('#'+k+'hlone')
    var hlmy = $('#'+k+'hlmy')
    var hlmany = $('#'+k+'hlmany')
    var hlreset = $('#'+k+'hldel')
    var stl = style[k]['prop']
    var selclr = sel.css(stl)

    hlradio.removeClass('ison')
    active.addClass('ison')
    if (activen == 'hlone' || activen == 'hlmy') {sel.show()} else {sel.hide()}

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
    else if (activen == 'hlmy') {
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
        hlmy.addClass('ison')
        viewstate['hlview'][k]['active'] = 'hlone'
        viewstate['hlview'][k]['sel_one'] = sel.attr('defn')
        viewstate['cmap'][k] = {}
        klist.each(function(index, item) {
            vid = $(item).attr('vid')
            var sel = $('#sel'+k+'_'+vid)
            var selc = $('#selc'+k+'_'+vid)
            sel.css(stl, vcolors[sel.attr('defn')][k])
            selc.prop('checked', false)
            add_highlights(k, vid, selclr)
        })
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

