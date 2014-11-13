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

function getdataviewvars() {
    var vars = ''
    var jvars = {}
    $('#txt_p, #txt_il, #legend input').each(function() {
        name = $(this).attr('id')
        val = $(this).prop('checked')?1:0
        vars += "&" + name + "=" + val
        jvars[name] = val
    })
    $('#dataviewvars').val(JSON.stringify(jvars))
    return vars
}

function savedataviewvars() {
    getdataviewvars()
    ajax(dataview_url, ['dataviewvars'], ':eval')
}

function getqueryviewvars() {
    var vars = ''
    var jvars = {}
    $('#qhlon, #qhlone').each(function() {
        name = $(this).attr('id')
        val = $(this).prop('checked')?1:0
        vars += "&" + name + "=" + val
        jvars[name] = val
    })
    val = $('#sel_one').html()
    vars += "&" + "sel_one" + "=" + val
    jvars['sel_one'] = val
    $('#queryviewvars').val(JSON.stringify(jvars))
    return vars
}

function savequeryviewvars() {
    getqueryviewvars()
    ajax(queryview_url, ['queryviewvars'], ':eval')
}

function getquerymapvars() {
    var vars = ''
    var jvars = {}
    $('.cc_sel').each(function() {
        name = 'q_' + $(this).attr('id').substring(4)
        val = $(this).html()
        vars += "&" + name + "=" + val
        jvars[name] = val
    })
    $('#querymapvars').val(JSON.stringify(jvars))
    return vars
}

function savequerymapvars() {
    getquerymapvars()
    ajax(querymap_url, ['querymapvars'], ':eval')
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
        $('#cviewlink').val(view_url + getdataviewvars() + getquerymapvars() + getqueryviewvars())
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
    add_highlights(null, qid, null)
}

function jscolorpicker(qid, initc, monads) {
    $('#picker_' + qid).hide()
    $('#sel_' + qid).click(function() {
        $('#picker_' + qid).show()
    })
    $('.cc.' + qid).click(function() {
        $('#picker_' + qid).hide()
        $('#sel_' + qid).css('background-color', $(this).css('background-color'))
        $('#sel_' + qid).html($(this).html())
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
        $('#sel_one').html($(this).html())
        change_highlights(bcol)
        savequeryviewvars()
    })
}

function colorinit2(initn, initc) {
    $('#sel_one').css('background-color', initc)
    $('#sel_one').html(initn)
    change_highlights(initc)
}

function change_highlights(clr) {
    isonbox =  $('#qhlon')
    isonebox =  $('#qhlone')
    isonelab =  $('#qhlonelab')
    isonecol =  $('#sel_one')
    ison = isonbox.prop('checked')
    isone = isonebox.prop('checked')
    $('#queries li').each(function(index, item) {
        if (ison) {
            isonebox.show()
            isonelab.show()
            if (isone) {
                isonecol.show()
                add_highlights($(item).attr('monads'), null, clr)
            }
            else {
                isonecol.hide()
                add_highlights($(item).attr('monads'), $(item).attr('qid'), null)
            }
        }
        else {
            isonebox.hide()
            isonelab.hide()
            isonecol.hide()
            add_highlights($(item).attr('monads'), null, '#ffffff')
        }
    })
    savequeryviewvars()
}

function set_highlights() {
    $('#qhlon').click(function() {
        change_highlights('#ffff00')
    })
    $('#qhlone').click(function() {
        change_highlights('#ffff00')
    })
}

function add_highlights(monads, qid, clr) {
    var mn = (monads == null)? $('#query_' + qid).attr('monads') : monads
    mn = $.parseJSON(mn);

    qhc = (clr == null)? $('#sel_' + qid).css('background-color') : clr
    $.each(mn, function(index, item) {
        $('span[m="' + item + '"]').css('background-color', qhc);
    })
}

/*****************************************************************************/


$(document).ready(function () {
    get_last_chapter_num();             // Chapter options
});
