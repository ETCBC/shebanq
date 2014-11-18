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

function getdataviewvars(asstr) {
    var vars = ''
    var jvars = {}
    $('#txt_p, #txt_il, #legend input').each(function() {
        name = $(this).attr('id')
        val = $(this).prop('checked')?1:0
        vars += "&" + name + "=" + val
        jvars[name] = val
    })
    $('#dataviewvars').val(JSON.stringify(jvars))
    return asstr?vars:jvars
}

function savedataviewvars() {
    getdataviewvars(true)
    ajax(dataview_url, ['dataviewvars'], ':eval')
}

function getqueryviewvars(asstr) {
    var vars = ''
    var jvars = {}
    $('.qhradio').each(function() {
        name = $(this).attr('id')
        val = $(this).hasClass('ison')?1:0
        vars += "&" + name + "=" + val
        jvars[name] = val
    })
    name = 'sel_one'
    val = $('#'+name).prop('cname')
    vars += "&" + name + "=" + val
    jvars[name] = val
    name = 'get_queries'
    val = $('#'+name).is(':hidden')?1:0
    vars += "&" + name + "=" + val
    jvars[name] = val
    $('#queryviewvars').val(JSON.stringify(jvars))
    return asstr?vars:jvars
}

function savequeryviewvars() {
    getqueryviewvars(true)
    ajax(queryview_url, ['queryviewvars'], ':eval')
}

function getquerymapvars(asstr) {
    var vars = ''
    var jvars = {}
    $('.cc_sel').each(function() {
        name = $(this).attr('id').substring(4)
        val = $(this).prop('cname')
        iscust = $(this).prop('iscust')
        if (iscust) {
            vars += "&" + name + "=" + val
            jvars[name] = val
        }
    })
    $('#querymapvars').val(JSON.stringify(jvars))
    return asstr?vars:jvars
}

function savequerymapvars(remove) {
    getquerymapvars(true)
    $.ajax({
        dataType: 'json',
        url: querymap_url,
        data: {querymapvars: $('#querymapvars').val(), remove: remove}, 
        success: function (dt, tstatus) {
            var vars = ''
            var jvars = {}
            for (name in dt) {
                vars += "&q" + name + "=" + dt[name]
                jvars[name] = dt[name]
            }
            $('#querymapvarsq').val(vars)
            $('#querymapvars').val(JSON.stringify(jvars))
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
        savedataviewvars()
    })
}

function set_q(fld, init) {
    if (init) {
        $('#'+fld).addClass('ison')
    }
    else {
        $('#'+fld).removeClass('ison')
    }
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
        savequerymapvars()
        $('#cviewlink').val(view_url + getdataviewvars(true) + $('#querymapvarsq').val() + getqueryviewvars(true))
        $('#cviewlink').each(function() {
            $(this).show()
            $(this).select()
        })
    })
}

function jsqueriesview(init) {
    $('#h_queries').hide()
    $('#get_queries').click(function(){
        $('#get_queries').hide()
        $('#h_queries').show()
        $('#qbar').show()
        savequeryviewvars()
    })
    $('#h_queries').click(function(){
        $('#h_queries').hide()
        $('#get_queries').show()
        $('#qbar').hide()
        savequeryviewvars()
    })
    if (init == 1) {
       $('#fetchqueries').click()
       $('#get_queries').hide()
    }
}

function jsqueryview(qid) {
    $('#l_' + qid).hide()
    $('#d_' + qid).hide()
    $('#l_' + qid).click(function() {
        $('#l_' + qid).hide()
        $('#h_' + qid).show()
        $('#d_' + qid).hide()
    })
    $('#m_' + qid).click(function() {
        $('#l_' + qid).show()
        $('#h_' + qid).hide()
        $('#d_' + qid).show()
    })
}

function jscolorpicker(qid, initc, monads) {
    var sel = $('#sel_'+qid)
    var selc = $('#selc_'+qid)
    var picker = $('#picker_'+qid)
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
            change_highlight(monads, qid, qid)
        }
        else {
            sel.prop('iscust', true)
            change_highlight(monads, qid, null)
        }
        var iscust = sel.prop('iscust')
        selc.prop('checked', iscust)
    })
    $('.cc.' + qid).click(function() {
        picker.hide()
        sel.css('background-color', $(this).css('background-color'))
        sel.prop('cname', $(this).html())
        sel.prop('iscust', true)
        selc.prop('checked', true)
        change_highlight(monads, qid, null)
    })
    if (initc != '') {
        sel.css('background-color', initc)
    }
    var iscust = sel.attr('iscust')
    sel.prop('iscust', (iscust=='true')?true:false)
    var iscust = sel.prop('iscust')
    selc.prop('checked', iscust)
}

function jscolorpicker2() {
    $('#picker_one').hide()
    $('#sel_one').click(function() {
        $('#picker_one').show()
    })
    $('.cc.one').click(function() {
        var bcol = $(this).css('background-color')
        $('#picker_one').hide()
        $('#sel_one').css('background-color', bcol)
        $('#sel_one').prop('cname', $(this).html())
        change_highlights(null)
        savequeryviewvars()
    })
}

function colorinit2(initv, initn, initc) {
    $('#sel_one').css('background-color', initc)
    $('#sel_one').prop('cname', initn)
    change_highlights(initv)
}

function change_highlight(monads, qid, delqid) {
    var qhlmy = $('#qhlmy')
    var qhlmany = $('#qhlmany')
    var sel = $('#sel_'+qid)
    var defc = sel.attr('defc')
    var defn = sel.attr('defn')
    var iscust = sel.prop('iscust')
    savequerymapvars(delqid)
    if (!qhlmy || qhlmy.html() == undefined) {
        add_highlights(monads, qid, null)
    }
    else {
        var qhlmyon = qhlmy.hasClass('ison') 
        var qhlmanyon = qhlmany.hasClass('ison') 
        if (qhlmanyon || qhlmyon) {
            if (qhlmanyon) {
                add_highlights(monads, qid, null)
            }
            else {
                if (iscust) {
                    add_highlights(monads, qid, null)
                }
                else {
                    selclr = $('#sel_one').css('background-color')
                    add_highlights(monads, qid, selclr)
                }
            }
        }
    }
}

function change_highlights(initv) {
    if (initv != null) {
        $('.qhradio').removeClass('ison')
        $('#'+initv).addClass('ison')

        if ($('#qhlone').hasClass('ison') || $('#qhlmy').hasClass('ison')) {
            $('#sel_one').show()
        }
        else {
            $('#sel_one').hide()
        }
    }

    selclr = $('#sel_one').css('background-color')
    if ($('#qhloff').hasClass('ison')) {
        $('#queries li').each(function(index, item) {
            add_highlights($(item).attr('monads'), null, '#ffffff')
        })
    }
    else if ($('#qhlone').hasClass('ison')) {
        $('#queries li').each(function(index, item) {
            add_highlights($(item).attr('monads'), null, selclr)
        })
    }
    else if ($('#qhlmy').hasClass('ison')) {
        savequerymapvars()
        querymap = $.parseJSON($('#querymapvars').val())
        $('#queries li').each(function(index, item) {
            qid =  $(item).attr('qid')
            add_highlights($(item).attr('monads'), qid, (qid in querymap)?null:selclr)
        })
    }
    else if ($('#qhlmany').hasClass('ison')) {
        $('#queries li').each(function(index, item) {
            add_highlights($(item).attr('monads'), $(item).attr('qid'), null)
        })
    }
    else if ($('#qhldel').hasClass('ison')) {
        savequerymapvars('all')
        $('#qhldel').removeClass('ison')
        $('#qhlmy').addClass('ison')
        $('#queries li').each(function(index, item) {
            qid = $(item).attr('qid')
            var sel = $('#sel_'+qid)
            sel.prop('iscust', false)
            sel.prop('cname', sel.attr('defn'))
            sel.css('background-color', sel.attr('defc'))
            selc.prop('checked', false)
            add_highlights($(item).attr('monads'), qid, selclr)
        })
    }
    savequeryviewvars()
}

function set_highlights() {
    $('.qhradio').click(function() {
        change_highlights($(this).attr('id'))
    })
}

function add_highlights(monads, qid, clr) {
    var mn = (monads == null)? $('#query_' + qid).attr('monads') : monads
    mn = $.parseJSON(mn)

    qhc = (clr == null)? $('#sel_' + qid).css('background-color') : clr
    $.each(mn, function(index, item) {
        $('span[m="' + item + '"]').css('background-color', qhc)
    })
}

$(document).ready(function () {
    get_last_chapter_num()
})
