/*

Application workflow:

There is a skeleton page, filled with HTML.
The skeleton has the following parts:

A. Sidebar with
    w: viewsettings plus a list of word items
    q: viewsettings plus a list of query items
    m: viewsettings plus the metadata of an individual query
B. Main part with
    heading
    material selector (either book/chapter, or resultpages)
    m: viewsettings (share link plus text/data selector)
    material (either the verses of a passage or the verses of the resultpage of a query)

There is a dictionary viewstate, in which the current viewsettings are being maintained.
Viewstate is divided in groups, each group is serialized to a cookie with every change made by the user.
Viewstate is initialized from the querystring and/or the cookies, where the querystring wins.

Depending on user actions, parts of the skeleton are loaded with HTML, through AJAX calls.

The application goes through the following stages:

setup_ functions:
    insert the action items into the skeleton or a new load of html that has come from the server
    Does not change the viewstate, does not look at the viewstate

apply_ functions:
    looks at the viewstate and adapts the display of the page, this might entail ajax actions
    does not change the viewstate

The skeleton can be used to structure several kinds of pages:

passage page
    The sidebar contains A-w and A-q, but not A-m
    The main part B contains a verse list from a passage (a chapter)
    A-w and A-q are lists of relevant words (lexemes) and queries.

query page
    The sidebar contains A-m, but not A-w and A-q
    The main part B contains a page with a verse list of verses containing a result of the query.
    A-m shows the metadata of the query, and the query can be edited in place. 

word page
    The sidebar contains A-m, but not A-w and A-q
    The main part B contains a page with a verse list of verses containing an occurrence of a word (lexeme).
    A-m shows the metadata of the query, and the query can be edited in place. 

The cookies are

material
    the current book, chapter, query id, word id, pagekind (m=material, q=query, w=word),
    tp (text-or-data setting: whether the material is shown as plain text (txt_p) or as interlinear data (txt_il))

hebrewdata
    a list of switches controlling which fields are shown in the data view

highlights
    groups of settings controlling the highlight colors
    group q: for queries
    group w: for words

    Both groups contain the same settings:
    active (which is the active setting: hloff, hlone, hlcustom, hlmany)
    sel_one (the color if all queries are highlighted with one color)
    get (whether or not to retrieve the side list of relevant items)

colormap
    mappings between queries and colors and between words and colors, based on the id of queries and words

*/

// GLOBALS

$.cookie.raw = false
$.cookie.json = true
$.cookie.defaults.expires = 30
$.cookie.defaults.path = '/'

var vcolors, viewstate, viewfluid, style, title, side_fetched, material_fetched
var thebooks, themonads
var view_url, material_url, side_url, rpage_url, color_url
var page
var subtract = 250


// TOP LEVEL: DYNAMICS, PAGE, SKELETON

function dynamics() {
    viewfluid = {}
    page = new Page()
    page.go('m')
}

function Page() {
    var settings = viewstate['material']['']
    this.skeleton = new Skeleton()
    this.prev = {}
    for (x in settings) {
        this.prev[x] = null
    }
    this.apply = function() {
        var pagekind = settings['pagekind']
        var thechapter = settings['chapter']
        this.skeleton.apply()
        $('#thechapter').html((thechapter > 0)?thechapter:'')
        if (pagekind == 'q') {
            $('#side_bar_m').show()
        }
        else {
            $('#side_bar_m').hide()
        }
        for (x in settings) {
            this.prev[x] = settings[x]
        }
    }
    this.go = function(pagekind) {
        settings['pagekind'] = pagekind
        if (
            settings['pagekind'] != this.prev.pagekind ||
            (this.prev.pagekind == 'm' && (settings['book'] != this.prev.book || settings['chapter'] != this.prev.chapter)) ||
            (this.prev.pagekind != 'm' && (settings[pagekind+id] != this.prev.vid || settings['pg'] != this.prev.pg))
        ) {
            material_fetched = {'txt_p': false, 'txt_il': false}
        }
        savestate('material','')
        this.apply()
    }
}

function Skeleton() {
    this.material = new Material()
    //this.sidebars = new Sidebars()
    this.apply = function() {
        this.material.apply()
        //this.sidebars.apply()
    }
    $('#material_txt_p').css('height', (window.innerHeight - subtract)+'px')
    $('#material_txt_il').css('height', (2 * window.innerHeight - subtract)+'px')
}

// MATERIAL

function Material() {
    var js_this = this
    var pagekind = viewstate['material']['']['pagekind']
    this.name = 'material'
    this.hid = '#'+this.name
    this.cselect = $('#material_select')
    this.viewlink = new Viewlink()
    this.mselect = new MSelect()
    this.pselect = new PSelect()
    this.message = new MMessage()
    this.content = new MContent()
    this.msettings = new MSettings(this.content)
    this.apply = function() {
        this.viewlink.apply()
        this.msettings.apply()
        this.mselect.apply()
        this.pselect.apply()
        this.fetch()
    }
    this.fetch = function() {
        var settings = viewstate['material']['']
        var pagekind = settings['pagekind']
        var tp = settings['tp']
        vars = '?pagekind='+pagekind
        vars += '&tp='+tp
        if (pagekind == 'm') {
            vars += '&book='+settings['book']
            vars += '&chapter='+settings['chapter']
            do_fetch = settings['book'] != 'x' && settings['chapter'] > 0
        }
        else {
            vars += '&id='+settings[pagekind+'id']
            vars += '&rpage='+settings['rpage']
            do_fetch = settings[pagekind+'id'] >=0
        }
        if (do_fetch && !material_fetched[tp]) {
            this.message.msg('fetching data ...')
            $.get(material_url+vars, function(html) {
                var response = $(html)
                if (pagekind != 'm') {
                    js_this.pselect.add(response)
                }
                js_this.message.add(response)
                js_this.content.add(response)
                material_fetched[tp] = true
                js_this.process()
            }, 'html')
        }
    }
    this.process = function() {
        var settings = viewstate['material']['']
        var pagekind = settings['pagekind']
        this.msettings.apply()
        if (pagekind != 'm') {
            this.psettings.apply()
        }
    }
    this.message.msg('choose a passage or a query or a word')
    material_fetched = {'txt_p': false, 'txt_il': false}
}

/*
            $('.verseref').click(function() {
                goto_page('m', $(this).attr('book'), $(this).attr('chapter'), null, null)
                savestate('material', '')
            })
*/

// VIEWLINK

function Viewlink() {
    var js_this = this
    this.name = 'viewlink'
    this.hid = '#'+this.name
    viewfluid = {}
    viewfluid[this.name] = 'x'
    var hide = $(this.hid+'_hide')
    var show = $(this.hid+'_show')
    var content = $(this.hid+'_content')
    this.apply = function() {
        var setting = viewfluid[this.name]
        if (setting == 'v') {
            hide.show()
            show.hide()
            content.show()
            content.val(view_url+getvars())
            content.select()
        }
        else {
            hide.hide()
            show.show()
            content.hide()
        }
    }
    hide.click(function() {
        viewfluid[js_this.name] = 'x'
        js_this.apply()
    })
    show.click(function() {
        viewfluid[js_this.name] = 'v'
        js_this.apply()
    })
}

// MATERIAL: SELECTION

function MSelect() {
    var settings = viewstate['material']['']
    var pagekind = settings['pagekind']
    var select = '#select_contents_chapter'
    this.name = 'select_passage'
    this.hid = '#'+this.name
    if (pagekind == 'm') {
        this.up = new SelectBook()
        this.select = new SelectItems(this.up)
        this.apply = function() {
            this.up.apply()
            this.select.apply()
        }
    }
    else {
        this.apply = function() {
            $(this.hid).hide()
        }
    }
}

function PSelect() {
    var settings = viewstate['material']['']
    var pagekind = settings['pagekind']
    var select = '#select_contents_page'
    this.name = 'select_pages'
    this.hid = '#'+this.name
    if (pagekind != 'm') {
        this.select = new SelectItems(null)
        this.apply = function() {
            this.select.apply()
        }
        this.add = function(response) {
            $(select).html(response.children(select).html())
        }
    }
    else {
        this.apply = function() {
            $(this.hid).hide()
        }
    }
}

function SelectBook() {
    var js_this = this
    var settings = viewstate['material']['']
    this.name = 'select_book'
    this.hid = '#'+this.name
    this.content = $(this.hid)
    this.apply = function () {
        var thebook = settings['book']
        this.content.show()
        this.content.val(thebook)
        this.chapters.gen_html('chapter')
        this.chapters.apply()
    }
    this.content.change(function () {
        settings['book'] = js_this.content.val()
        savestate('material', '')
        page.go('m', null, null, null, null)
    })
    this.gen_html = function() {
        var ht = '<option value="x">choose a book ...</option>'
        for (i in thebooksorder) {
            book =  thebooksorder[i]
            ht += '<option value="'+book+'">'+book+'</option>'
        }
        this.content.append($(ht))
    }
    this.gen_html()
    this.content.val(settings['book'])
}

function SelectItems(up) {
    var js_this = this
    var settings = viewstate['material']['']
    var pagekind = settings['pagekind']
    this.key = (pagekind == 'm')?'chapter':'page'
    this.up = up
    this.name = 'select_contents_'+this.key
    this.hid = '#'+this.name
    this.control = '#select_control_'+this.key
    if (this.up) {
        this.up.chapters = this
    }
    this.present = function() {
        $(this.hid).dialog({
            autoOpen: false,
            dialogClass: 'items',
            closeOnEscape: true,
            modal: false,
            title: 'choose '+js_this.key,
            position: {my: 'right top', at: 'left top', of: $(js_this.up.hid)},
            width: '450px',
        })
    }
    this.gen_html = function() {
        if (this.key == 'chapter') {
            var thebook = settings['book']
            var theitem = settings['chapter']
            var nitems = (thebook != 'x')?thebooks[thebook]:0
            var itemlist = new Array(nitems)
            for  (i = 0; i < nitems; i++) {itemlist[i] = i+1}
        }
        else { // 'page'
            var theitem = settings['pg']
            var nitems = $('#rp_pages').val()
            var itemlist = $('#rp_pagelist').val()
        }
        var ht = ''
        if (nitems != 0) {
            ht = '<div class="pagination"><ul>'
            for (i in itemlist) {
                item = itemlist[i]
                if (theitem == item) {
                    ht += '<li class="active"><a class="itemnav" href="#" item="'+item+'">'+item+'</a></li>'
                }
                else {
                    ht += '<li><a class="itemnav" href="#" item="'+item+'">'+item+'</a></li>'
                }
            }
            ht += '</ul></div>'
        }
        $(this.hid).html(ht)
        return nitems
    }
    this.add_item = function(item) {
        item.click(function() {
            var settings = viewstate['material']['']
            var pagekind = settings['pagekind']
            var newobj = $(this).closest('li')
            var isloaded = newobj.hasClass('active')
            if (!isloaded) {
                var settings = viewstate['material']['']
                var newitem = $(this).attr('item')
                settings[js_this.key] = newitem 
                savestate('material', '')
                page.go('m', null, null, null, null)
            }
        })
    }
    this.apply = function() {
        var nitems = 0
        if ($(this.hid).html() != '') {
            nitems = this.gen_html() 
        }
        if (nitems == 0) {
            $(this.control).hide()
        }
        else {
            $('.itemnav').each(function() {
                js_this.add_item($(this))
            })
            $(this.control).show()
        }
        this.present()
        if ($(this.hid).dialog('instance') && $(this.hid).dialog('isOpen')) {$(this.hid).dialog('close')}
    }
    $(this.control).click(function () {
        $(js_this.hid).dialog('open')
        savestate('material', '')
    })
}

// MATERIAL (messages when retrieving, storing the contents)

function MMessage() {
    this.name = 'material_message'
    this.hid = '#'+this.name
    this.add = function(response) {
        $(this.hid).html(response.children(this.hid).html())
    }
    this.msg = function(m) {
        $(this.hid).html(m)
    }
}

function MContent() {
    var settings = viewstate['material']['']
    var tps = {txt_p: 'txt_il', txt_il: 'txt_p'}
    this.name_text = 'material_text'
    this.name_data = 'material_data'
    this.hid_text = '#'+this.name_text
    this.hid_data = '#'+this.name_data
    this.hid_content = '#material_content'
    this.select = function() {
        var tp = settings['tp']
        this.name_yes = 'material_'+tp
        this.name_no = 'material_'+tps[tp]
        this.hid_yes = '#'+this.name_yes
        this.hid_no = '#'+this.name_no
    }
    this.add = function(response) {
        this.select()
        $(this.hid_yes).html(response.children(this.hid_content).html())
    }
    this.show = function() {
        this.select()
        $(this.hid_yes).show()
        $(this.hid_no).hide()
    }
}

// MATERIAL SETTINGS (for the highlight color and the data to show)

function MSettings(content) {
    var js_this = this
    var settings = viewstate['material']['']
    var hltext = $('#mtxt_p')
    var hldata = $('#mtxt_il')
    var legend = $('#datalegend')
    var legendc = $('#datalegend_control')
    this.name = 'material_settings'
    this.hid = '#'+this.name
    this.content = content
    this.hebrewsettings = new HebrewSettings()
    $('.mhradio').click(function() {
        var activen = $(this).attr('id').substring(1)
        settings['tp'] = activen 
        savestate('material','')
        page.go('m')
    })
    legendc.click(function () {
        legend.dialog({
            dialogClass: 'legend',
            closeOnEscape: true,
            modal: false,
            title: 'choose data features',
            position: {my: 'right top', at: 'left top', of: $(js_this.hid)},
            width: '550px',
        })
    })
    this.apply = function() {
        var settings = viewstate['material']['']
        var tp = settings['tp']
        var hlradio = $('.mhradio')
        hlradio.removeClass('ison')
        $('#m'+tp).addClass('ison')
        this.content.show()
        if (tp == 'txt_il') {
            legendc.show()
            this.hebrewsettings.apply()
        }
        else {
            legend.hide()
            legendc.hide()
        }
    }
}

// HEBREW DATA

function HebrewSettings() {
    var settings = viewstate['hebrewdata']['']
    for (fld in settings) {
        this[fld] = new HebrewSetting(fld)
    }
    this.apply = function() {
        for (fld in settings) {
            this[fld].apply()
        }
    }
}

function HebrewSetting(fld) {
    var js_this = this
    var settings = viewstate['hebrewdata']['']
    this.name = fld
    this.hid = '#'+this.name
    $(this.hid).click(function() {
        settings[fld] = $(this).prop('checked')?'v':'x'
        savestate('hebrewdata')
        js_this.applysetting()
    })
    this.apply = function() {
        var val = settings[this.name]
        $(this.hid).prop('checked', val == 'v')
        this.applysetting()
    }
    this.applysetting = function() {
        if (settings[this.name] == 'v') {
            $('.'+this.name).each(function () {$(this).show()})
        }
        else {
            $('.'+this.name).each(function () {$(this).hide()})
        }
    }
}

// SIDEBARS

function SSettings(k) {
    this.name = 'side_settings_'+k
    this.hid = '#'+this.name
}

function Sidebars() {
    this.m = Sidebar('m')
    for (k in viewstate['highlights']) {
        this.k = Sidebar(k)
    }
    this.apply = function() {
    }
}

function Sidebar(k) {
    this.name = 'side_bar_'+k
    this.hid = '#'+this.name
    this.kind = k
    this.settings = new Settings(k)
    this.apply = function() {
    }
}

function SContents() {
    this.name = 'side_material_'+k
    this.hid = '#'+this.name
}

// SIDELIST CONTROLS

function setup_sidelists() {
    for (k in viewstate['highlights']) {
        setup_sidelist(k)
    }
}

function setup_sidelist(k) {
    var hidelist = $('#side_hide_'+k)
    var showlist = $('#side_show_'+k)
    var viewlist = $('#side_settings_'+k)
    var thelist = $('#side_material_'+k)
    showlist.click(function(){
        viewstate['highlights'][k]['get'] = 'v'
        savestate('highlights',k)
        fetch_sideitems(k, thelist)
        hidelist.show()
        thelist.show()
        viewlist.show()
        showlist.hide()
    })
    hidelist.click(function(){
        viewstate['highlights'][k]['get'] = 'x'
        savestate('highlights',k)
        showlist.show()
        thelist.hide()
        viewlist.hide()
        hidelist.hide()
    })
}

function apply_sidelists() {
    side_fetched = {}
    for (k in viewstate['highlights']) {
        apply_sidelist(k)
    }
}

function apply_sidelist(k) {
    var hidelist = $('#side_hide_'+k)
    var showlist = $('#side_show_'+k)
    var viewlist = $('#side_settings_'+k)
    var thelist = $('#side_material_'+k)
    thelist.html('')
    side_fetched[k] = false
    if (viewstate['highlights'][k]['get'] == 'v') {
        fetch_sideitems(k, thelist)
        showlist.hide()
    }
    else {
        hidelist.hide()
        thelist.hide()
        viewlist.hide()
    }
}

function hide_sidelist(k) {
    side = $('#side_material_'+k)
    side.hide()
}

function apply_sideview(k, vid) {
    $('#colorpicker_m').load(color_url+'?k='+k+'&vid='+vid, function (response, stats, xhr) {
        jscolorpicker(k, vid)
        paint_highlights(k, vid, null)
    }, 'html')
}

// SIDELIST MATERIAL

function fetch_sideitems(k, thelist) {
    var settings = viewstate['material']['']
    var thebook = settings['book']
    var thechapter = settings['chapter']
    var viewlist = $('#side_settings_'+k)
    if (!side_fetched[k] && thechapter) {
        thelist.load(side_url+k, {book: thebook, chapter: thechapter}, function () {
            side_fetched[k] = true
            viewlist.show()
            setup_sidelistitems(k)
            apply_highlightsettings()
        }, 'html')
    }
}

function setup_sidelistitems(k) {
    var klist = $('#side_list_'+k+' li')
    klist.each(function(index, item) {
        var vid = $(item).attr('vid')
        setup_sidelistitem(k, vid)
        jscolorpicker(k, vid)
    })
}

function setup_sidelistitem(k,vid) {
    var more = $('#m_'+k+vid) 
    var head = $('#h_'+k+vid) 
    var desc = $('#d_'+k+vid) 
    desc.hide()
    more.click(function() {
        desc.toggle()
    })
}

// HIGHLIGHTS

function setup_highlightsettings() {
    for (k in viewstate['highlights']) {
        setup_highlightsetting(k)
    }
}

function setup_highlightsetting(k) {
    $('.hradio_'+k).click(function() {
        viewstate['highlights'][k]['active'] = $(this).attr('id').substring(1)
        xapply_highlights(k)
        savestate('highlights',k)
    })
}


function apply_highlightsettings() {
    for (k in viewstate['highlights']) {
        apply_highlightsetting(k)
    }
}

function apply_highlightsetting(k) {
    var klist = $('#side_list_'+k+' li')
    klist.each(function() {
        var vid = $(this).attr('vid')
        var title = $(this).attr('title')
        title[k][vid] = title
    })
}

function setup_onepickers() {
    var settings = viewstate['material']['']
    var pagekind = settings['pagekind']
    var thevid = settings[pagekind+'id']
    jscolorpicker(k, thevid)
}

function apply_oneview() {
    var settings = viewstate['material']['']
    var pagekind = settings['pagekind']
    var thevid = settings[pagekind+'id']
    if (thevid) {
        paint_highlights(pagekind, thevid, null)
    }
}

function xapply_highlights(k, picked) {
    var activen = viewstate['highlights'][k]['active']
    var active = $('#'+k+activen)
    var klist = $('#side_list_'+k+' li')
    var selo = $('#sel_'+k+'one')
    var hlradio = $('.hradio_'+k)
    var hloff = $('#'+k+'hloff')
    var hlone = $('#'+k+'hlone')
    var hlcustom = $('#'+k+'hlcustom')
    var hlmany = $('#'+k+'hlmany')
    var hlreset = $('#'+k+'hlreset')
    var stl = style[k]['prop']
    var selclr = selo.css(stl)

    if (picked && activen != 'hlcustom' && activen != 'hlone') {
        viewstate['highlights'][k]['active'] = 'hlcustom'
        activen = 'hlcustom'
        active = $('#'+k+activen)
    }
    hlradio.removeClass('ison')
    active.addClass('ison')

    if (activen == 'hloff') {
        klist.each(function(index, item) {
            paint_highlights(k, $(item).attr('vid'), style[k]['off'])
        })
    }
    else if (activen == 'hlone') {
        klist.each(function(index, item) {
            paint_highlights(k, $(item).attr('vid'), selclr)
        })
    }
    else if (activen == 'hlcustom') {
        var colormap = viewstate['colormap'][k]
        klist.each(function(index, item) {
            var vid =  $(item).attr('vid')
            paint_highlights(k, vid, (vid in colormap)?null:selclr)
        })
    }
    else if (activen =='hlmany') {
        klist.each(function(index, item) {
            paint_highlights(k, $(item).attr('vid'), null)
        })
    }
    else if (activen == 'hlreset') {
        var selclr2 = selo.attr('defn')
        hlreset.removeClass('ison')
        hlcustom.addClass('ison')
        selo.css(stl, vcolors[selclr2][k])
        viewstate['highlights'][k]['active'] = 'hlcustom'
        viewstate['highlights'][k]['sel_one'] = selclr2
        viewstate['colormap'][k] = {}
        klist.each(function(index, item) {
            var vid =  $(item).attr('vid')
            var sel = $('#sel_'+k+vid)
            var selc = $('#selc_'+k+vid)
            var selclr = sel.attr('defn')
            sel.css(stl, vcolors[selclr][k])
            selc.prop('checked', false)
            paint_highlights(k, vid, vcolors[selclr2][k])
        })
    }
}

function xapply_highlight(k, vid) {
    var sel = $('#sel_'+k+vid)
    var selo = $('#sel_'+k+'one')
    var hlcustom = $('#'+k+'hlcustom')
    var hlmany = $('#'+k+'hlmany')
    var defc = sel.attr('defc')
    var defn = sel.attr('defn')
    var iscust = vid in viewstate['colormap'][k]
    var stl = style[k]['prop']
    if (!hlcustom || hlcustom.html() == undefined) {
        paint_highlights(k, vid, null)
    }
    else {
        var hlcustomon = hlcustom.hasClass('ison') 
        var hlmanyon = hlmany.hasClass('ison') 
        if (hlmanyon || hlcustomon) {
            if (hlmanyon) {
                paint_highlights(k, vid, null)
            }
            else {
                if (iscust) {
                    paint_highlights(k, vid, null)
                }
                else {
                    selclr = selo.css(stl)
                    paint_highlights(k, vid, selclr)
                }
            }
        }
    }
}

function paint_highlights(k, vid, clr) {
    var pagekind = viewstate['material']['']['pagekind']
    var monads = (pagekind == 'm')? $.parseJSON($('#'+k+vid).attr('monads')) : themonads
    var stl = style[k]['prop']

    var hc = (clr == null)? $('#sel_'+k+vid).css(stl) : clr
    $.each(monads, function(index, item) {
        $('span[m="'+item+'"]').css(stl, hc)
    })
}

// COLOR PICKERS

function setup_hlpickers() {
    for (k in viewstate['highlights']) {
        jscolorpicker2(k, 'one')
    }
}

function jscolorpicker(k, vid) {
    var sel = $('#sel_'+k+vid)
    var selc = $('#selc_'+k+vid)
    var picker = $('#picker_'+k+vid)
    var stl = style[k]['prop']
    var colorn = viewstate['colormap'][k][vid]
    picker.hide()
    sel.click(function() {
        picker.dialog({
            dialogClass: 'picker_dialog',
            closeOnEscape: true,
            modal: true,
            title: 'choose a color',
            position: {my: 'right top', at: 'left top', of: selc},
            width: '200px',
        })
    })
    selc.click(function() {
        var was_cust = vid in viewstate['colormap'][k]
        if (picker.dialog('isOpen')) {picker.dialog('close')}
        if (was_cust) {
            sel.css(stl, vcolors[sel.attr('defn')][k])
            delete viewstate['colormap'][k][vid]
        }
        else {
            viewstate['colormap'][k][vid] = sel.attr('defn')
        }
        selc.prop('checked', vid in viewstate['colormap'][k])
        xapply_highlight(k, vid)
        savestate('colormap', k)
    })
    $('.cc.'+k+vid).click(function() {
        if (picker.dialog('isOpen')) {picker.dialog('close')}
        sel.css(stl, $(this).css(stl))
        viewstate['colormap'][k][vid] = $(this).html()
        selc.prop('checked', true)
        xapply_highlight(k, vid)
        savestate('colormap', k)
    })
    if (colorn == undefined) {colorn = sel.attr('defn')}
    $('.cc.'+k+vid).each(function() {$(this).css(stl, vcolors[$(this).html()][k])})
    sel.css(stl, vcolors[colorn][k])
    selc.prop('checked', vid in viewstate['colormap'][k])
}

function jscolorpicker2(k, lab) {
    var sel = $('#sel_'+k+lab)
    var picker = $('#picker_'+k+lab)
    var stl = style[k]['prop']
    var colorn = viewstate['highlights'][k]['sel_'+lab]
    picker.hide()
    sel.click(function() {
        picker.dialog({
            dialogClass: 'picker_dialog',
            closeOnEscape: true,
            modal: true,
            title: 'choose a color',
            position: {my: 'right top', at: 'left top', of: sel},
            width: '200px',
        })
    })
    $('.cc.'+k+lab).click(function() {
        if (picker.dialog('isOpen')) {picker.dialog('close')}
        sel.css(stl, $(this).css(stl))
        viewstate['highlights'][k]['sel_'+lab] = $(this).html()
        xapply_highlights(k, true)
        savestate('highlights',k)
    })
    if (colorn == undefined) {colorn = sel.attr('defn')}
    $('.cc.'+k+lab).each(function() {$(this).css(stl, vcolors[$(this).html()][k])})
    sel.css(stl, vcolors[colorn][k])
}

// SAVING STATE

function getvars() {
    var vars = ''
    var sep = '?'
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

function savestate(group, k) {$.cookie(group+k, viewstate[group][k])}

