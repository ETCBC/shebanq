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
var view_url, material_url, item_url, side_url, color_url
var page
var subtract = 250


// TOP LEVEL: DYNAMICS, PAGE, SKELETON

function dynamics() {
    viewfluid = {}
    page = new Page()
    page.go()
}

function Page() {
    var settings = viewstate['material']['']
    var vsettings = viewstate['highlights']
    this.skeleton = new Skeleton()
    this.prev = {}
    for (x in settings) {
        this.prev[x] = null
    }
    this.apply = function() {
        var pagekind = settings['pagekind']
        var otherpagekind = (pagekind == 'w')?'q':(pagekind == 'q')?'w':''
        var thechapter = settings['chapter']
        var thepage = settings['page']
        this.skeleton.apply()
        $('#theitemlabel').html((pagekind == 'm')?'':style[pagekind]['Tag'])
        $('#thechapter').html((thechapter > 0)?thechapter:'')
        $('#thepage').html((thepage > 0)?'page '+thepage:'')
        for (x in settings) {
            this.prev[x] = settings[x]
        }
    }
    this.go = function() {
        var pagekind = settings['pagekind']
        if (
            settings['pagekind'] != this.prev['pagekind'] ||
            (this.prev['pagekind'] == 'm' && (settings['book'] != this.prev['book'] || settings['chapter'] != this.prev['chapter'])) ||
            (this.prev['pagekind'] != 'm' && (settings[pagekind+'id'] != this.prev['vid'] || settings['page'] != this.prev['page']))
        ) {
            material_fetched = {txt_p: false, txt_il: false}
        }
        savestate('material','')
        this.apply()
    }
}

function Skeleton() {
    this.material = new Material()
    this.sidebars = new Sidebars()
    this.apply = function() {
        this.material.apply()
        this.sidebars.apply()
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
        var vars = '?pagekind='+pagekind
        vars += '&tp='+tp
        if (pagekind == 'm') {
            vars += '&book='+settings['book']
            vars += '&chapter='+settings['chapter']
            do_fetch = settings['book'] != 'x' && settings['chapter'] > 0
        }
        else {
            vars += '&id='+settings[pagekind+'id']
            vars += '&page='+settings['page']
            do_fetch = settings[pagekind+'id'] >=0
        }
        if (do_fetch && !material_fetched[tp]) {
            this.message.msg('fetching data ...')
            $.get(material_url+vars, function(html) {
                var response = $(html)
                js_this.pselect.add(response)
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
        page.skeleton.sidebars.after_material_fetch()
        if (pagekind != 'm') {
            this.pselect.apply()
            $('a.vref').click(function() {
                settings['book'] = $(this).attr('book')
                settings['chapter'] = $(this).attr('chapter')
                settings['pagekind'] = 'm'
                savestate('material', '')
                page.go('m')
            })
        }
    }
    this.message.msg('choose a passage or a query or a word')
}

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

function MSelect() { // for book and chapter selection
    var settings = viewstate['material']['']
    var select = '#select_contents_chapter'
    this.name = 'select_passage'
    this.hid = '#'+this.name
    this.up = new SelectBook()
    this.select = new SelectItems(this.up, 'chapter')
    this.apply = function() {
        var pagekind = settings['pagekind']
        if (pagekind == 'm') {
            this.up.apply()
            $(this.hid).show()
        }
        else {
            $(this.hid).hide()
        }
    }
}

function PSelect() { // for result page selection
    var settings = viewstate['material']['']
    var select = '#select_contents_page'
    this.name = 'select_pages'
    this.hid = '#'+this.name
    this.select = new SelectItems(null, 'page')
    this.apply = function() {
        var pagekind = settings['pagekind']
        if (pagekind != 'm') {
            this.select.apply()
            $(this.hid).show()
        }
        else {
            $(this.hid).hide()
        }
    }
    this.add = function(response) {
        var pagekind = settings['pagekind']
        if (pagekind != 'm') {
            $(select).html(response.find(select).html())
        }
    }
}

function SelectBook() {
    var js_this = this
    var settings = viewstate['material']['']
    this.name = 'select_book'
    this.hid = '#'+this.name
    this.content = $(this.hid)
    this.selected = null
    this.apply = function () {
        var thebook = settings['book']
        this.content.show()
        this.content.val(thebook)
        if (this.selected != thebook) {
            this.chapters.gen_html()
            this.chapters.apply()
        }
        this.selected = thebook
    }
    this.content.change(function () {
        settings['book'] = js_this.content.val()
        settings['pagekind'] = 'm'
        savestate('material', '')
        page.go()
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

function SelectItems(up, key) { // both for chapters and for result pages
    var js_this = this
    var settings = viewstate['material']['']
    this.key = key
    this.tag = (key == 'chapter')?'passage':'pages'
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
            position: {my: 'right top', at: 'left top', of: $('#select_'+js_this.tag)},
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
            var theitem = settings['page']
            var nitems = $('#rp_pages').val()
            var itemlist = []
            if (nitems) {
                itemlist = $.parseJSON($('#rp_pagelist').val())
            }
        }
        var ht = ''
        if (nitems != undefined) {
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
        }
        return nitems
    }
    this.add_item = function(item) {
        item.click(function() {
            var settings = viewstate['material']['']
            var newobj = $(this).closest('li')
            var isloaded = newobj.hasClass('active')
            if (!isloaded) {
                var newitem = $(this).attr('item')
                settings[js_this.key] = newitem 
                savestate('material', '')
                page.go()
            }
        })
    }
    this.apply = function() {
        var pagekind = settings['pagekind']
        var showit = false
        if (pagekind != 'm' && this.key == 'page') {
            showit = this.gen_html() > 0 
        }
        else if (pagekind == 'm' && this.key == 'chapter') {
            showit = true
        }
        if (!showit) {
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

function MContent() { // the actual Hebrew content, either plain text or interlinear data
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

// MATERIAL SETTINGS (for choosing between plain text and interlnear data)

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
        settings['pagekind'] = 'm'
        savestate('material','')
        page.go()
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

// HEBREW DATA (which fields to show if interlinear text is displayed)

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

function Sidebars() {
    var vsettings = viewstate['highlights']
    this.m = new Sidebar('m')
    for (k in vsettings) {
        this['m'+k] = new Sidebar('m', k)
        this[k+'m'] = new Sidebar(k, 'm')
    }
    side_fetched = {}
    this.apply = function() {
        for (k in vsettings) {
            this['m'+k].apply()
            this[k+'m'].apply()
        }
    }
    this.after_material_fetch = function() {
        for (k in vsettings) {
            delete side_fetched['m'+k]
        }
    }
    this.after_item_fetch = function() {
        for (k in vsettings) {
            delete side_fetched[k+'m']
        }
    }
}

function Sidebar(pagekind, k) {
    var js_this = this
    this.pagekind = pagekind
    this.k = k
    this.name = 'side_bar_'+this.pagekind+this.k
    this.hid = '#'+this.name
    var msettings = viewstate['material']['']
    var vsettings = (this.k == 'm')?{}:viewstate['highlights'][this.k]
    var thebar = $(this.hid)
    var thelist = $('#side_material_'+this.pagekind+this.k)
    var hide = $('#side_hide_'+this.pagekind+this.k)
    var show = $('#side_show_'+this.pagekind+this.k)
    this.ssettings = new SSettings(this.pagekind, this.k)
    this.content = new SContent(this.pagekind, this.k, this.ssettings)
    this.apply = function() {
        var currentpagekind = msettings['pagekind']
        if (currentpagekind != this.pagekind) {
            thebar.hide()
        }
        else {
            thebar.show()
            if (vsettings['get'] == 'x') {
                thelist.hide()
                hide.hide()
                show.show()
            }
            else {
                thelist.show()
                hide.show()
                show.hide()
            }
        }
        this.content.apply()
    }
    show.click(function(){
        vsettings['get'] = 'v'
        savestate('highlights',js_this.k)
        js_this.apply()
    })
    hide.click(function(){
        vsettings['get'] = 'x'
        savestate('highlights',js_this.k)
        js_this.apply()
    })
}

function SSettings(pagekind, k) {
    var js_this = this
    this.pagekind = pagekind
    this.k = k
    var viewlist = $('#side_settings_'+this.pagekind+this.k)
    this.name = 'side_settings_'+this.pagekind+this.k
    this.hid = '#'+this.name
    this.apply = function() {
    }
    this.apply_item = function(vid) {
        this.jscolorpicker(vid)
    }
    this.jscolorpicker = function(vid) {
        var sel = $('#sel_'+this.k+vid)
        var selc = $('#selc_'+this.k+vid)
        var picker = $('#picker_'+this.k+vid)
        var stl = style[this.k]['prop']
        var colorn = viewstate['colormap'][this.k][vid]
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
            var was_cust = vid in viewstate['colormap'][js_this.k]
            if (picker.dialog('isOpen')) {picker.dialog('close')}
            if (was_cust) {
                sel.css(stl, vcolors[sel.attr('defn')][js_this.k])
                delete viewstate['colormap'][js_this.k][vid]
            }
            else {
                viewstate['colormap'][js_this.k][vid] = sel.attr('defn')
            }
            selc.prop('checked', vid in viewstate['colormap'][js_this.k])
            xapply_highlight(js_this.k, vid)
            savestate('colormap', js_this.k)
        })
        $('.c'+this.k+'.'+this.k+vid).click(function() {
            if (picker.dialog('isOpen')) {picker.dialog('close')}
            sel.css(stl, $(this).css(stl))
            viewstate['colormap'][js_this.k][vid] = $(this).html()
            selc.prop('checked', true)
            xapply_highlight(js_this.k, vid)
            savestate('colormap', js_this.k)
        })
        if (colorn == undefined) {colorn = sel.attr('defn')}
        $('.c'+this.k+'.'+this.k+vid).each(function() {$(this).css(stl, vcolors[$(this).html()][js_this.k])})
        sel.css(stl, vcolors[colorn][this.k])
        selc.prop('checked', vid in viewstate['colormap'][this.k])
    }
}

function SContent(pagekind, k, ssettings) {
    var js_this = this
    this.pagekind = pagekind
    this.k = k
    var msettings = viewstate['material']['']
    var vsettings = (this.k == 'm')?{}:viewstate['highlights'][this.k]
    var thebar = $(this.hid)
    var thelist = $('#side_material_'+this.pagekind+this.k)
    var hide = $('#side_hide_'+this.pagekind+this.k)
    var show = $('#side_show_'+this.pagekind+this.k)
    this.name = 'side_material_'+this.pagekind+this.k
    this.hid = '#'+this.name
    this.ssettings = ssettings
    this.msg = function(m) {
        $(this.hid).html(m)
    }
    this.fetch = function() {
        var thebook = msettings['book']
        var thechapter = msettings['chapter']
        var vars = '?pagekind='+this.pagekind+'&k='+this.k
        var do_fetch = false
        var extra = ''
        if (this.pagekind == 'm') {
            vars += '&book='+msettings['book']
            vars += '&chapter='+msettings['chapter']
            do_fetch = msettings['book'] != 'x' && msettings['chapter'] > 0
            extra = 'm'
        }
        else {
            vars += '&id='+msettings[this.pagekind+'id']
            do_fetch = msettings[this.pagekind+'id'] >=0
            extra = this.pagekind+'m'
        }
        if (do_fetch && !side_fetched[this.pagekind+this.k]) {
            this.msg('fetching '+style[this.k]['tags']+' ...')
            if (this.pagekind == 'm') {
                thelist.load(side_url+extra+vars, function () {
                    side_fetched[js_this.pagekind+js_this.k] = true
                    js_this.process()
                }, 'html')
            }
            else {
                $.get(side_url+extra+vars, function (html) {
                    thelist.html(html)
                    side_fetched[js_this.pagekind+js_this.k] = true
                    js_this.process()
                }, 'html')

            }
        }
    }
    this.sidelistitems = function() {
        var klist = $('#side_list_'+this.k+' li')
        klist.each(function() {
            var vid = $(this).attr('vid')
            js_this.sidelistitem(vid)
            js_this.ssettings.apply_item(vid)
        })
    }
    this.sidelistitem = function(vid) {
        var more = $('#m_'+this.k+vid) 
        var head = $('#h_'+this.k+vid) 
        var desc = $('#d_'+this.k+vid) 
        var item = $('#item_'+this.k+vid) 
        desc.hide()
        more.click(function() {
            desc.toggle()
        })
        item.click(function() {
            var msettings = viewstate['material']['']
            var k = js_this.k
            msettings['pagekind'] = k
            msettings[k+'id'] = $(this).attr('vid')
            msettings['page'] = 1
            page.go()
        })
    }
    this.process = function() {
        page.skeleton.sidebars.after_item_fetch()
        this.ssettings.apply()
        this.sidelistitems()
        $('#theitem').html($('#itemtag').val()+':')
                //apply_highlightsettings()
    }
    this.apply = function() {
        var currentpagekind = msettings['pagekind']
        if (currentpagekind == this.pagekind && (this.pagekind != 'm' || vsettings['get'] == 'v')) {
            this.fetch()
        }
    }
}

// SIDELIST CONTROLS


function apply_sideview(k, vid) {
    $('#colorpicker_m').load(color_url+'?k='+k+'&vid='+vid, function (response, stats, xhr) {
        jscolorpicker(k, vid)
        paint_highlights(k, vid, null)
    }, 'html')
}

// SIDELIST MATERIAL

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
    $('.c'+k+'.'+k+lab).click(function() {
        if (picker.dialog('isOpen')) {picker.dialog('close')}
        sel.css(stl, $(this).css(stl))
        viewstate['highlights'][k]['sel_'+lab] = $(this).html()
        xapply_highlights(k, true)
        savestate('highlights',k)
    })
    if (colorn == undefined) {colorn = sel.attr('defn')}
    $('.c'+k+'.'+k+lab).each(function() {$(this).css(stl, vcolors[$(this).html()][k])})
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

function activate_buttons() {
    $('.smb').each(function() {
        $(this).click(function() {
            $('.smb').each(function() {
                var name = $(this).attr('name')
                $('#'+name).val(false)
            })
            var name = $(this).attr('name')
            $('#'+name).val(true)
        })
    })
}
