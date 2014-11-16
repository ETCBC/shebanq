/********************** CHAPTER OPTIONS **************************************/
// HELPER function to generate the options from a last chapter number.
function replace_select_options(selectBox, last_chapter_num) {
    $(selectBox).empty();
    for(var i=1; i<=last_chapter_num; i++){
        $(selectBox)
            .append($("<option></option>")
            .attr("value", i)
            .text(i));
    }
};

// Get last chapter number of the current selected book on book option change.
function get_last_chapter_num() {
    $("select#verses_form_Book").change(function () {
        ajax('last_chapter_num', ['Book'], ':eval');
    });

    // Replace chapter options with current chapter options after ajax call
    // finishes.
    $(document).ajaxComplete(function(event, xhr, settings) {
        if (settings.url === 'last_chapter_num') {
            replace_select_options('#verses_form_Chapter', xhr.responseText);
        }
    });
}
/*****************************************************************************/
/********************** HIGHLIGHTS *******************************************/
/* Cases:
 * 1. Get queries: on select 'highlight all queries' checkbox highlight monads
 *    of all queries;
 * 2. Get queries: on select query checkbox highlight selected queries;
 * 3. Request var: on page load highlight specific monads from an input field.
 */

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
    val = $('#sel_one').prop('cname')
    vars += "&" + "sel_one" + "=" + val
    jvars['sel_one'] = val
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
    $('#' + fld).attr('checked', init);
    if (!init) {
        $('.' + fld).each(function () {
            $( this ).toggle();
        });
    }
    $('#' + fld).change(function() {
        $('.' + fld).each(function () {
            $( this ).toggle();
        });
        savedataviewvars()
    });
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
    $("#cviewlink").hide();
    $("#xviewlink").hide();

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
    $('#s_queries').click(function(){
        $('#s_queries').hide()
        $('#h_queries').show()
        $('#qbar').show()
    })
    $('#h_queries').click(function(){
        $('#h_queries').hide()
        $('#s_queries').show()
        $('#qbar').hide()
    })
    if (init == 1) {
       $('#fetchqueries').click()
       $('#s_queries').hide()
    }
}

function jsqueryview(qid) {
    $('#l_' + qid).hide()
    $('#d_' + qid).hide()
    $('#l_' + qid).click(function() {
        $('#l_' + qid).hide()
        $('#m_' + qid).show()
        $('#d_' + qid).hide()
    })
    $('#m_' + qid).click(function() {
        $('#l_' + qid).show()
        $('#m_' + qid).hide()
        $('#d_' + qid).show()
    })
    //add_highlights(null, qid, null)
}

function jscolorpicker(qid, initc, monads) {
    $('#picker_' + qid).hide()
    $('#sel_' + qid).click(function() {
        $('#picker_' + qid).show()
    })
    $('.cc.' + qid).click(function() {
        $('#picker_' + qid).hide()
        $('#sel_' + qid).css('background-color', $(this).css('background-color'))
        $('#sel_' + qid).prop('cname', $(this).html())
        $('#sel_' + qid).prop('iscust', true)
        add_highlights(monads, qid, null);
        savequerymapvars()
    })
    if (initc != '') {
        $('#sel_' + qid).css('background-color', initc)
    }
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
        querymap = $.parseJSON($('#querymapvars').val());
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
        savequerymapvars(true)
        $('#qhldel').removeClass('ison')
        $('#qhlmany').addClass('ison')
        $('#queries li').each(function(index, item) {
            add_highlights($(item).attr('monads'), $(item).attr('qid'), null)
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
    mn = $.parseJSON(mn);

    qhc = clr
    if (qid != null) {
        if (clr == null) {
            qhc = $('#sel_' + qid).css('background-color')
        }
        else {
        }
    }

    qhc = (clr == null)? $('#sel_' + qid).css('background-color') : clr
    $.each(mn, function(index, item) {
        $('span[m="' + item + '"]').css('background-color', qhc);
    })
}

/*****************************************************************************/


$(document).ready(function () {
    get_last_chapter_num();             // Chapter options
});
