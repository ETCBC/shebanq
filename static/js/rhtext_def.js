
function set_toggle_txt_il(init) {
    $("#toggle_txt_il").attr('checked', init);
    if (!init) {
        $('.txt_il').each(function () {
            $( this ).toggle();
        });
    }
    $("#toggle_txt_il").change(function() {
        $('.txt_il').each(function () {
            $( this ).toggle();
        });
        ajax(save_url + '?tg=toggle_txt_il', ['toggle_txt_il'], 'curviewlnk')
    });
}

function set_toggle_txt_p(init) {
    $("#toggle_txt_p").attr('checked', init);
    if (!init) {
        $('.txt_p').each(function () {
            $( this ).toggle();
        });
    }
    $("#toggle_txt_p").change(function() {
        $('.txt_p').each(function () {
            $( this ).toggle();
        });
        ajax(save_url + '?tg=toggle_txt_p', ['toggle_txt_p'], 'curviewlnk')
    });
}

function set_toggle_ht(init) {
    $("#toggle_ht").attr('checked', init);
    if (!init) {
        $('.ht').each(function () {
            $( this ).toggle();
        });
    }
    $("#toggle_ht").change(function() {
        $('.ht').each(function () {
            $( this ).toggle();
        });
        ajax(save_url + '?tg=toggle_ht', ['toggle_ht'], 'curviewlnk')
    });
}

function set_toggle_hl(init) {
    $("#toggle_hl").attr('checked', init);
    if (!init) {
        $('.hl').each(function () {
            $( this ).toggle();
        });
    }
    $("#toggle_hl").change(function() {
        $('.hl').each(function () {
            $( this ).toggle();
        });
        ajax(save_url + '?tg=toggle_hl', ['toggle_hl'], 'curviewlnk')
    });
}

function set_toggle_tt(init) {
    $("#toggle_tt").attr('checked', init);
    if (!init) {
        $('.tt').each(function () {
            $( this ).toggle();
        });
    }
    $("#toggle_tt").change(function() {
        $('.tt').each(function () {
            $( this ).toggle();
        });
        ajax(save_url + '?tg=toggle_tt', ['toggle_tt'], 'curviewlnk')
    });
}

function set_toggle_tl(init) {
    $("#toggle_tl").attr('checked', init);
    if (!init) {
        $('.tl').each(function () {
            $( this ).toggle();
        });
    }
    $("#toggle_tl").change(function() {
        $('.tl').each(function () {
            $( this ).toggle();
        });
        ajax(save_url + '?tg=toggle_tl', ['toggle_tl'], 'curviewlnk')
    });
}

function set_toggle_gl(init) {
    $("#toggle_gl").attr('checked', init);
    if (!init) {
        $('.gl').each(function () {
            $( this ).toggle();
        });
    }
    $("#toggle_gl").change(function() {
        $('.gl').each(function () {
            $( this ).toggle();
        });
        ajax(save_url + '?tg=toggle_gl', ['toggle_gl'], 'curviewlnk')
    });
}

function set_toggle_wd1(init) {
    $("#toggle_wd1").attr('checked', init);
    if (!init) {
        $('.wd1').each(function () {
            $( this ).toggle();
        });
    }
    $("#toggle_wd1").change(function() {
        $('.wd1').each(function () {
            $( this ).toggle();
        });
        ajax(save_url + '?tg=toggle_wd1', ['toggle_wd1'], 'curviewlnk')
    });
}

function set_toggle_wd1_subpos(init) {
    $("#toggle_wd1_subpos").attr('checked', init);
    if (!init) {
        $('.wd1_subpos').each(function () {
            $( this ).toggle();
        });
    }
    $("#toggle_wd1_subpos").change(function() {
        $('.wd1_subpos').each(function () {
            $( this ).toggle();
        });
        ajax(save_url + '?tg=toggle_wd1_subpos', ['toggle_wd1_subpos'], 'curviewlnk')
    });
}

function set_toggle_wd1_pos(init) {
    $("#toggle_wd1_pos").attr('checked', init);
    if (!init) {
        $('.wd1_pos').each(function () {
            $( this ).toggle();
        });
    }
    $("#toggle_wd1_pos").change(function() {
        $('.wd1_pos').each(function () {
            $( this ).toggle();
        });
        ajax(save_url + '?tg=toggle_wd1_pos', ['toggle_wd1_pos'], 'curviewlnk')
    });
}

function set_toggle_wd1_lang(init) {
    $("#toggle_wd1_lang").attr('checked', init);
    if (!init) {
        $('.wd1_lang').each(function () {
            $( this ).toggle();
        });
    }
    $("#toggle_wd1_lang").change(function() {
        $('.wd1_lang').each(function () {
            $( this ).toggle();
        });
        ajax(save_url + '?tg=toggle_wd1_lang', ['toggle_wd1_lang'], 'curviewlnk')
    });
}

function set_toggle_wd1_n(init) {
    $("#toggle_wd1_n").attr('checked', init);
    if (!init) {
        $('.wd1_n').each(function () {
            $( this ).toggle();
        });
    }
    $("#toggle_wd1_n").change(function() {
        $('.wd1_n').each(function () {
            $( this ).toggle();
        });
        ajax(save_url + '?tg=toggle_wd1_n', ['toggle_wd1_n'], 'curviewlnk')
    });
}

function set_toggle_wd2(init) {
    $("#toggle_wd2").attr('checked', init);
    if (!init) {
        $('.wd2').each(function () {
            $( this ).toggle();
        });
    }
    $("#toggle_wd2").change(function() {
        $('.wd2').each(function () {
            $( this ).toggle();
        });
        ajax(save_url + '?tg=toggle_wd2', ['toggle_wd2'], 'curviewlnk')
    });
}

function set_toggle_wd2_gender(init) {
    $("#toggle_wd2_gender").attr('checked', init);
    if (!init) {
        $('.wd2_gender').each(function () {
            $( this ).toggle();
        });
    }
    $("#toggle_wd2_gender").change(function() {
        $('.wd2_gender').each(function () {
            $( this ).toggle();
        });
        ajax(save_url + '?tg=toggle_wd2_gender', ['toggle_wd2_gender'], 'curviewlnk')
    });
}

function set_toggle_wd2_gnumber(init) {
    $("#toggle_wd2_gnumber").attr('checked', init);
    if (!init) {
        $('.wd2_gnumber').each(function () {
            $( this ).toggle();
        });
    }
    $("#toggle_wd2_gnumber").change(function() {
        $('.wd2_gnumber').each(function () {
            $( this ).toggle();
        });
        ajax(save_url + '?tg=toggle_wd2_gnumber', ['toggle_wd2_gnumber'], 'curviewlnk')
    });
}

function set_toggle_wd2_person(init) {
    $("#toggle_wd2_person").attr('checked', init);
    if (!init) {
        $('.wd2_person').each(function () {
            $( this ).toggle();
        });
    }
    $("#toggle_wd2_person").change(function() {
        $('.wd2_person').each(function () {
            $( this ).toggle();
        });
        ajax(save_url + '?tg=toggle_wd2_person', ['toggle_wd2_person'], 'curviewlnk')
    });
}

function set_toggle_wd2_state(init) {
    $("#toggle_wd2_state").attr('checked', init);
    if (!init) {
        $('.wd2_state').each(function () {
            $( this ).toggle();
        });
    }
    $("#toggle_wd2_state").change(function() {
        $('.wd2_state').each(function () {
            $( this ).toggle();
        });
        ajax(save_url + '?tg=toggle_wd2_state', ['toggle_wd2_state'], 'curviewlnk')
    });
}

function set_toggle_wd2_tense(init) {
    $("#toggle_wd2_tense").attr('checked', init);
    if (!init) {
        $('.wd2_tense').each(function () {
            $( this ).toggle();
        });
    }
    $("#toggle_wd2_tense").change(function() {
        $('.wd2_tense').each(function () {
            $( this ).toggle();
        });
        ajax(save_url + '?tg=toggle_wd2_tense', ['toggle_wd2_tense'], 'curviewlnk')
    });
}

function set_toggle_wd2_stem(init) {
    $("#toggle_wd2_stem").attr('checked', init);
    if (!init) {
        $('.wd2_stem').each(function () {
            $( this ).toggle();
        });
    }
    $("#toggle_wd2_stem").change(function() {
        $('.wd2_stem').each(function () {
            $( this ).toggle();
        });
        ajax(save_url + '?tg=toggle_wd2_stem', ['toggle_wd2_stem'], 'curviewlnk')
    });
}

function set_toggle_sp(init) {
    $("#toggle_sp").attr('checked', init);
    if (!init) {
        $('.sp').each(function () {
            $( this ).toggle();
        });
    }
    $("#toggle_sp").change(function() {
        $('.sp').each(function () {
            $( this ).toggle();
        });
        ajax(save_url + '?tg=toggle_sp', ['toggle_sp'], 'curviewlnk')
    });
}

function set_toggle_sp_rela(init) {
    $("#toggle_sp_rela").attr('checked', init);
    if (!init) {
        $('.sp_rela').each(function () {
            $( this ).toggle();
        });
    }
    $("#toggle_sp_rela").change(function() {
        $('.sp_rela').each(function () {
            $( this ).toggle();
        });
        ajax(save_url + '?tg=toggle_sp_rela', ['toggle_sp_rela'], 'curviewlnk')
    });
}

function set_toggle_sp_n(init) {
    $("#toggle_sp_n").attr('checked', init);
    if (!init) {
        $('.sp_n').each(function () {
            $( this ).toggle();
        });
    }
    $("#toggle_sp_n").change(function() {
        $('.sp_n').each(function () {
            $( this ).toggle();
        });
        ajax(save_url + '?tg=toggle_sp_n', ['toggle_sp_n'], 'curviewlnk')
    });
}

function set_toggle_ph(init) {
    $("#toggle_ph").attr('checked', init);
    if (!init) {
        $('.ph').each(function () {
            $( this ).toggle();
        });
    }
    $("#toggle_ph").change(function() {
        $('.ph').each(function () {
            $( this ).toggle();
        });
        ajax(save_url + '?tg=toggle_ph', ['toggle_ph'], 'curviewlnk')
    });
}

function set_toggle_ph_det(init) {
    $("#toggle_ph_det").attr('checked', init);
    if (!init) {
        $('.ph_det').each(function () {
            $( this ).toggle();
        });
    }
    $("#toggle_ph_det").change(function() {
        $('.ph_det').each(function () {
            $( this ).toggle();
        });
        ajax(save_url + '?tg=toggle_ph_det', ['toggle_ph_det'], 'curviewlnk')
    });
}

function set_toggle_ph_fun(init) {
    $("#toggle_ph_fun").attr('checked', init);
    if (!init) {
        $('.ph_fun').each(function () {
            $( this ).toggle();
        });
    }
    $("#toggle_ph_fun").change(function() {
        $('.ph_fun').each(function () {
            $( this ).toggle();
        });
        ajax(save_url + '?tg=toggle_ph_fun', ['toggle_ph_fun'], 'curviewlnk')
    });
}

function set_toggle_ph_typ(init) {
    $("#toggle_ph_typ").attr('checked', init);
    if (!init) {
        $('.ph_typ').each(function () {
            $( this ).toggle();
        });
    }
    $("#toggle_ph_typ").change(function() {
        $('.ph_typ').each(function () {
            $( this ).toggle();
        });
        ajax(save_url + '?tg=toggle_ph_typ', ['toggle_ph_typ'], 'curviewlnk')
    });
}

function set_toggle_ph_n(init) {
    $("#toggle_ph_n").attr('checked', init);
    if (!init) {
        $('.ph_n').each(function () {
            $( this ).toggle();
        });
    }
    $("#toggle_ph_n").change(function() {
        $('.ph_n').each(function () {
            $( this ).toggle();
        });
        ajax(save_url + '?tg=toggle_ph_n', ['toggle_ph_n'], 'curviewlnk')
    });
}

function set_toggle_cl(init) {
    $("#toggle_cl").attr('checked', init);
    if (!init) {
        $('.cl').each(function () {
            $( this ).toggle();
        });
    }
    $("#toggle_cl").change(function() {
        $('.cl').each(function () {
            $( this ).toggle();
        });
        ajax(save_url + '?tg=toggle_cl', ['toggle_cl'], 'curviewlnk')
    });
}

function set_toggle_cl_dom(init) {
    $("#toggle_cl_dom").attr('checked', init);
    if (!init) {
        $('.cl_dom').each(function () {
            $( this ).toggle();
        });
    }
    $("#toggle_cl_dom").change(function() {
        $('.cl_dom').each(function () {
            $( this ).toggle();
        });
        ajax(save_url + '?tg=toggle_cl_dom', ['toggle_cl_dom'], 'curviewlnk')
    });
}

function set_toggle_cl_typ(init) {
    $("#toggle_cl_typ").attr('checked', init);
    if (!init) {
        $('.cl_typ').each(function () {
            $( this ).toggle();
        });
    }
    $("#toggle_cl_typ").change(function() {
        $('.cl_typ').each(function () {
            $( this ).toggle();
        });
        ajax(save_url + '?tg=toggle_cl_typ', ['toggle_cl_typ'], 'curviewlnk')
    });
}

function set_toggle_cl_n(init) {
    $("#toggle_cl_n").attr('checked', init);
    if (!init) {
        $('.cl_n').each(function () {
            $( this ).toggle();
        });
    }
    $("#toggle_cl_n").change(function() {
        $('.cl_n').each(function () {
            $( this ).toggle();
        });
        ajax(save_url + '?tg=toggle_cl_n', ['toggle_cl_n'], 'curviewlnk')
    });
}

function set_toggle_sn(init) {
    $("#toggle_sn").attr('checked', init);
    if (!init) {
        $('.sn').each(function () {
            $( this ).toggle();
        });
    }
    $("#toggle_sn").change(function() {
        $('.sn').each(function () {
            $( this ).toggle();
        });
        ajax(save_url + '?tg=toggle_sn', ['toggle_sn'], 'curviewlnk')
    });
}

function set_toggle_sn_n(init) {
    $("#toggle_sn_n").attr('checked', init);
    if (!init) {
        $('.sn_n').each(function () {
            $( this ).toggle();
        });
    }
    $("#toggle_sn_n").change(function() {
        $('.sn_n').each(function () {
            $( this ).toggle();
        });
        ajax(save_url + '?tg=toggle_sn_n', ['toggle_sn_n'], 'curviewlnk')
    });
}
