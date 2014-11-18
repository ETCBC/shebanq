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

function gethebrewdatavars(asstr) {
    var vars = ''
    var jvars = {}
    $('#txt_p, #txt_il, #legend input').each(function() {
        name = $(this).attr('id')
        val = $(this).prop('checked')?1:0
        vars += "&" + name + "=" + val
        jvars[name] = val
    })
    $('#hebrewdatavars').val(JSON.stringify(jvars))
    return asstr?vars:jvars
}

function savehebrewdatavars() {
    gethebrewdatavars(true)
    ajax(hebrewdata_url, ['hebrewdatavars'], ':eval')
}

function gethlviewvars(k,asstr) {
    var vars = ''
    var jvars = {}
    $('.'+k+'hradio').each(function() {
        name = $(this).attr('id')
        val = $(this).hasClass('ison')?1:0
        vars += "&"+name+"="+val
        jvars[name] = val
    })
    name = 'sel_one'
    val = $('#'+k+name).prop('cname')
    vars += "&"+k+name+"="+val
    jvars[k+name] = val
    name = 'get'
    val = $('#'+k+name).is(':hidden')?1:0
    vars += "&"+k+name+"="+val
    jvars[k+name] = val
    $('#'+k+hlviewvars').val(JSON.stringify(jvars))
    return asstr?vars:jvars
}

function savehlviewvars(k) {
    gethlviewvars(k,true)
    ajax(hlview_url, [k+'hlviewvars'], ':eval')
}

function getcmapvars(k,asstr) {
    var vars = ''
    var jvars = {}
    $('.cc_sel'+k).each(function() {
        name = $(this).attr('id').substring(4)
        val = $(this).prop('cname')
        iscust = $(this).prop('iscust')
        if (iscust) {
            vars += "&" + name + "=" + val
            jvars[name.substring(1)] = val
        }
    })
    $('#'+k+cmapvars').val(JSON.stringify(jvars))
    return asstr?vars:jvars
}

function savecmapvars(k,remove) {
    var cmapvars = $('#'+k+'cmapvars')
    var cmapvarsq = $('#'+k+'cmapvarsq')
    getcmapvars(k,true)
    $.ajax({
        dataType: 'json',
        url: cmap_url,
        data: {cmapvars: cmapvars.val(), remove: remove}, 
        success: function (dt, tstatus) {
            var vars = ''
            var jvars = {}
            for (name in dt) {
                vars += "&"+k+name+"="+dt[name]
                jvars[name] = dt[name]
            }
            cmapvarsq.val(vars)
            cmapvars.val(JSON.stringify(jvars))
        },
        async: false,
    })
}

function set_d(fld, init) {
    $('#' + fld).attr('checked', init)
    if (!init) {
        $('.' + fld).each(function () {
            $( this ).toggle()
        })
    }
    $('#' + fld).change(function() {
        $('.' + fld).each(function () {
            $( this ).toggle()
        })
        savehebrewdatavars()
    })
}

function jsviewlink() {
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
        var kinds = ['q','w']
        for (i in kinds) {
            k = kinds[i]
            savecmapvars(k)
        }
        $('#cviewlink').val(view_url + gethebrewdatavars(true) + $('#cmapvarsq').val() + gethlviewvars('q',true) + gethlviewvars('w',true))
        $('#cviewlink').each(function() {
            $(this).show()
            $(this).select()
        })
    })
}

function jslistview(k,init) {
    klist = (k == 'q')?'queries':'words'
    hidelist = $('#h_'+klist)
    showlist = $('#s_'+klist)
    thelist = $('#'+k+'bar')
    hidelist.hide()
    showlist.click(function(){
        showlist.hide()
        hidelist.show()
        thelist.show()
        savehlviewvars(k)
    })
    hidelist.click(function(){
        hidelist.hide()
        showlist.show()
        thelist.hide()
        savehlviewvars(k)
    })
    if (init == 1) {
        if (k == 'q') {
            $('#fetchqueries').click()
        }
        showlist.click()
    }
}

function jshlview(k,vid) {
    var less = $('#l_'+k+vid) 
    var more = $('#m_'+k+vid) 
    var head = $('#d_'+k+vid) 
    var desc = $('#d_'+k+vid) 
    less.hide()
    desc.hide()
    less.click(function() {
        less.hide()
        head.show()
        desc.hide()
    })
    more.click(function() {
        less.show()
        head.hide()
        desc.show()
    })
}

function jscolorpicker(k, vid, initc, monads) {
    var sel = $('#sel'+k+'_'+vid)
    var selc = $('#selc'+k+'_'+vid)
    var picker = $('#picker'+k+'_'+vid)
    picker.hide()
    sel.click(function() {
        picker.show()
    })
    selc.click(function() {
        picker.hide()
        var was_cust = sel.prop('iscust')
        if (was_cust) {
            sel.prop('iscust', false)
            sel.prop('cname', sel.attr('defn'))
            sel.css('background-color', sel.attr('defc'))
            change_highlight(k, monads, vid, vid)
        }
        else {
            sel.prop('iscust', true)
            change_highlight(k, monads, vid, null)
        }
        var iscust = sel.prop('iscust')
        selc.prop('checked', iscust)
    })
    $('.cc.'+k+vid).click(function() {
        picker.hide()
        sel.css('background-color', $(this).css('background-color'))
        sel.prop('cname', $(this).html())
        sel.prop('iscust', true)
        selc.prop('checked', true)
        change_highlight(k, monads, vid, null)
    })
    if (initc != '') {
        sel.css('background-color', initc)
    }
    var iscust = sel.attr('iscust')
    sel.prop('iscust', (iscust=='true')?true:false)
    var iscust = sel.prop('iscust')
    selc.prop('checked', iscust)
}

function jscolorpicker2(k) {
    var sel = $('#sel'+k+'_one')
    var picker = $('#picker'+k+'_one')
    picker.hide()
    sel.click(function() {
        picker.show()
    })
    $('.cc.'+k+'one').click(function() {
        var bcol = $(this).css('background-color')
        picker.hide()
        sel.css('background-color', bcol)
        sel.prop('cname', $(this).html())
        change_highlights(k, null)
        savehlviewvars(k)
    })
}

function colorinit2(k, initv, initn, initc) {
    var sel = $('#sel'+k+'_one')
    sel.css('background-color', initc)
    sel.prop('cname', initn)
    change_highlights(k, initv)
}

function change_highlight(k, monads, vid, delvid) {
    var sel = $('#sel'+k+'_'+vid)
    var selo = $('#sel'+k+'_one')
    var hlmy = $('#'+k+'hlmy')
    var hlmany = $('#'+k+'hlmany')
    var defc = sel.attr('defc')
    var defn = sel.attr('defn')
    var iscust = sel.prop('iscust')
    savecmapvars(k,delvid)
    if (!hlmy || hlmy.html() == undefined) {
        add_highlights(k, monads, vid, null)
    }
    else {
        var hlmyon = hlmy.hasClass('ison') 
        var hlmanyon = hlmany.hasClass('ison') 
        if (hlmanyon || hlmyon) {
            if (hlmanyon) {
                add_highlights(k, monads, vid, null)
            }
            else {
                if (iscust) {
                    add_highlights(k, monads, vid, null)
                }
                else {
                    selclr = selo.css('background-color')
                    add_highlights(k, monads, vid, selclr)
                }
            }
        }
    }
}

function change_highlights(k, initv) {
    var klist = $('#' + ((k=='q')?'queries':'words') + ' li')
    var sel = $('#sel'+k+'_one')
    var hlradio = $('#'+k+'hlradio')
    var hloff = $('#'+k+'hloff')
    var hlone = $('#'+k+'hlone')
    var hlmy = $('#'+k+'hlmy')
    var hlmany = $('#'+k+'hlmany')
    var hlinitv = $('#'+k+initv)
    var hlreset = $('#'+k+'hldel')
    if (initv != null) {
        hlradio.removeClass('ison')
        hlinitv.addClass('ison')

        if (hlone.hasClass('ison') || hlmy.hasClass('ison')) {
            sel.show()
        }
        else {
            sel.hide()
        }
    }

    selclr = sel.css('background-color')
    if (hloff.hasClass('ison')) {
        klist.each(function(index, item) {
            add_highlights(k, $(item).attr('monads'), null, '#ffffff')
        })
    }
    else if (hlone.hasClass('ison')) {
        klist.each(function(index, item) {
            add_highlights(k, $(item).attr('monads'), null, selclr)
        })
    }
    else if (hlmy.hasClass('ison')) {
        savecmapvars(k)
        cmap = $.parseJSON($('#cmapvars').val())
        klist.each(function(index, item) {
            vid =  $(item).attr('vid')
            add_highlights(k, $(item).attr('monads'), vid, (vid in cmap)?null:selclr)
        })
    }
    else if (hlmany.hasClass('ison')) {
        klist.each(function(index, item) {
            add_highlights(k, $(item).attr('monads'), $(item).attr('vid'), null)
        })
    }
    else if (hlreset.hasClass('ison')) {
        savecmapvars(k,'all')
        hlreset.removeClass('ison')
        hlmy.addClass('ison')
        klist.each(function(index, item) {
            vid = $(item).attr('vid')
            var sel = $('#sel'+k+'_'+vid)
            sel.prop('iscust', false)
            sel.prop('cname', sel.attr('defn'))
            sel.css('background-color', sel.attr('defc'))
            selc.prop('checked', false)
            add_highlights(k, $(item).attr('monads'), vid, selclr)
        })
    }
    savehlviewvars(k)
}

function set_highlights() {
    var kinds = ['q','w']
    for (i in kinds) {
        k = kinds[i]
        $('.'+k+'hradio').click(function() {
            change_highlights(k, $(this).attr('id'))
        })
}

function add_highlights(k, monads, vid, clr) {
    var mn = (monads == null)? $('#'+k+vid).attr('monads') : monads
    mn = $.parseJSON(mn)

    hc = (clr == null)? $('#sel'+k+'_'+vid).css('background-color') : clr
    $.each(mn, function(index, item) {
        $('span[m="' + item + '"]').css('background-color', hc)
    })
}
