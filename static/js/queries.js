var pq_url, q_url, record_url
var ns = $.initNamespaceStorage('muting')
var vs = $.initNamespaceStorage('qsview')
var muting = ns.localStorage
var qsview = vs.localStorage
var ftree, msg, rdata
var subtract = 80 // the canvas holding the material gets a height equal to the window height minus this amount

var escapeHTML = (function () {
    'use strict';
    var chr = {
        '&': '&amp;', '<': '&lt;',  '>': '&gt;'
    };
    return function (text) {
        return text.replace(/[&<>]/g, function (a) { return chr[a]; });
    };
}());

var Request = {
    parameter: function(name) {
        return this.parameters()[name]
    },
    parameters: function(uri) {
        var i, parameter, params, query, result;
        result = {};
        if (!uri) {
            uri = window.location.search;
        }
        if (uri.indexOf("?") === -1) {
            return {};
        }
        query = uri.slice(1);
        params = query.split("&");
        i = 0;
        while (i < params.length) {
            parameter = params[i].split("=");
            result[parameter[0]] = parameter[1];
            i++;
        }
        return result;
    }
}

function View() {
    var that = this
    this.prevstate = false
    if (!qsview.isSet('simple')) {
        qsview.set('simple', true)
    }
    this.qvradio = $('.qvradio')
    this.csimple = $('#c_view_simple')
    this.cadvanced = $('#c_view_advanced')

    this.adjust_view = function() {
        var simple = qsview.get('simple');
        this.qvradio.removeClass('ison');
        (simple?this.csimple:this.cadvanced).addClass('ison')
        if (this.prevstate != simple) {
            if (simple) {
                $('.brq').hide()
            }
            else {
                $('.brq').show()
            }
            this.prevstate = simple
        }
    }

    this.csimple.click(function(e) {e.preventDefault();
        qsview.set('simple', true)
        that.adjust_view()
    })
    this.cadvanced.click(function(e) {e.preventDefault();
        qsview.set('simple', false)
        that.adjust_view()
    })
    this.adjust_view()
}

function Level() {
    var that = this
    var levels = {o: 1, p: 2, u: 3, q: 4}
    this.expand_all = function() {
        ftree.ftw.visit(function(n) {
            n.setExpanded(true, {noAnimation: true, noEvents: true})
        }, true)
    }

    this.expand_level = function(level) {
        $('.qlradio').removeClass('ison')
        $('#level_'+level).addClass('ison')
        qsview.set('level', level)
        if (level in levels) {
            var numlevel = levels[level]
            ftree.ftw.visit(function(n) {
                var nlevel = n.getLevel()
                n.setExpanded(nlevel <= numlevel , {noAnimation: true, noEvents: true})
            }, true)
        }
    }

    this.initlevel = function() {
        this.expand_level(qsview.get('level'))
    }
    $('.qlradio').removeClass('ison')
    if (!qsview.isSet('level')) {qsview.set('level', 'o')}
    $('#level_o').click(function(e) {e.preventDefault();that.expand_level('o')})
    $('#level_p').click(function(e) {e.preventDefault();that.expand_level('p')})
    $('#level_u').click(function(e) {e.preventDefault();that.expand_level('u')})
    $('#level_q').click(function(e) {e.preventDefault();that.expand_level('q')})
    $('#level_').click(function(e) {e.preventDefault();that.expand_level('')})
}

function Filter() {
    var that = this
    this.patc = $('#filter_contents')

    var re_is_my = new RegExp('class="[^"]*qmy', "");
    var re_is_private = new RegExp('class="[^"]*qpriv', "");

    function is_my(node) {return re_is_my.test(node.title)}
    function is_private(node) {return re_is_private.test(node.title)}

    function in_my(pat) {
        var lpat = pat.toLowerCase()
        return function(node) { 
            return re_is_my.test(node.title) && (pat == '' || node.title.toLowerCase().indexOf(lpat) >= 0)
        }
    }
    function in_private(pat) {
        var lpat = pat.toLowerCase()
        return function(node) {return re_is_private.test(node.title) && (pat == '' || node.title.toLowerCase().indexOf(lpat) >= 0)}
    }

    this.clear = function() {
        ftree.ftw.clearFilter()
        msg.clear('f')
        msg.msg('f', ['good', 'no filter applied'])
        $('.qfradio').removeClass('ison')
        qsview.remove('filter_mode')
        $('#filter_clear').hide()
        $('#amatches').html('')
        $('#cmatches').html('')
        $('#qmatches').html('')
        $('#mmatches').html('')
        $('#rmatches').html('')
        $('#count_o').html(rdata.o)
        $('#count_p').html(rdata.p)
        $('#count_u').html(rdata.u)
        $('#count_q').html(rdata.q)
    }
    this.pqsearch = function(kind) {
        var pat = this.patc.val()
        qsview.set('filter_pat', pat);
        var amatches = 0
        var cmatches = 0
        var qmatches = 0
        var mmatches = 0
        var rmatches = 0
        if (pat == '') {
            amatches = -1
            cmatches = -1
            qmatches = -1
            mmatches = -1
            rmatches = -1
        }
        $('.qfradio').removeClass('ison')
        if (kind == 'm') {
            msg.clear('f')
            msg.msg('f', ['warning', 'my queries'])
        }
        else if (kind == 'r') {
            msg.clear('f')
            msg.msg('f', ['warning', 'private queries'])
        }
        else if (pat == '') {
            this.clear()
            return
        }
        else {
            msg.clear('f')
            msg.msg('f', ['special', 'filter applied'])
        }
        $('#filter_control_'+kind).addClass('ison')
        qsview.set('filter_mode', kind)

        ftree.level.expand_all()
        if (kind == 'a') {
            amatches = ftree.ftw.filterNodes(pat, false)
            $('#amatches').html(amatches>=0?('('+amatches+')'):'')
        }
        else if (kind == 'c') {
            cmatches = ftree.ftw.filterBranches(pat)
            $('#cmatches').html(cmatches>=0?('('+cmatches+')'):'')
        }
        else if (kind == 'q') {
            qmatches = ftree.ftw.filterNodes(pat, true)
            $('#qmatches').html(qmatches>=0?('('+qmatches+')'):'')
        }
        else if (kind == 'm') {
            mmatches = ftree.ftw.filterNodes(in_my(pat), true)
            $('#mmatches').html(mmatches>=0?('('+mmatches+')'):'')
        }
        else if (kind == 'r') {
            rmatches = ftree.ftw.filterNodes(in_private(pat), true)
            $('#rmatches').html((rmatches >= 0)?('('+rmatches+')'):'')
        }
        $('#filter_clear').show()
        var submatch = 'span.fancytree-submatch'
        var match = 'span.fancytree-match'
        var base_o = '#queries>ul>li>ul>li>'
        var match_o = $(base_o+match).length
        var submatch_o = $(base_o+submatch).length
        var base_p = base_o+'ul>li>'
        var match_p = $(base_p+match).length
        var submatch_p = $(base_p+submatch).length
        var base_u = base_p+'ul>li>'
        var match_u = $(base_u+match).length
        var submatch_u = $(base_u+submatch).length
        var base_q = base_u+'ul>li>'
        var match_q = $(base_q+match).length
        $('#count_o').html('<span class="match">'+match_o+'</span> <span class="brq submatch">'+submatch_o+'</span>')
        $('#count_p').html('<span class="match">'+match_p+'</span> <span class="brq submatch">'+submatch_p+'</span>')
        $('#count_u').html('<span class="match">'+match_u+'</span> <span class="brq submatch">'+submatch_u+'</span>')
        $('#count_q').html('<span class="match">'+match_q+'</span>')
        if (ftree.view.simple) {
            $('.brq').hide()
        }
    }

    $('#filter_clear').hide()
    $('#filter_contents').val(qsview.isSet('filter_pat')?qsview.get('filter_pat'):'')
    if (qsview.isSet('filter_mode')) {
        this.pqsearch(qsview.get('filter_mode'))
        $('#filter_clear').show()
    }


    $('#filter_control_a').click(function(e) {e.preventDefault();that.pqsearch('a')})
    $('#filter_control_c').click(function(e) {e.preventDefault();that.pqsearch('c')})
    $('#filter_control_q').click(function(e) {e.preventDefault();that.pqsearch('q')})
    $('#filter_control_m').click(function(e) {e.preventDefault();that.pqsearch('m')})
    $('#filter_control_r').click(function(e) {e.preventDefault();that.pqsearch('r')})

    $('#filter_clear').click(function(e) {e.preventDefault();that.clear()})
}

function Msg() {
    this.destinations = {
        o: $('#dbmsg_o'),
        p: $('#dbmsg_p'),
        q: $('#dbmsg_q'),
        qv: $('#dbmsg_qv'),
        f: $('#filter_msg'),
    }
    this.clear = function(dest) {
        var msgc = this.destinations[dest];
        msgc.html('')
    }
    this.msg = function(dest, msgobj) {
        var msgc = this.destinations[dest];
        var mtext = msgc.html()
        msgc.html(mtext+'<p class="'+msgobj[0]+'">'+msgobj[1]+'</p>')
    }
}

function Tree() {
    var that = this
    this.tps = {o: 'organization', p:'project', q:'query'}

    this.store_select = function(node) {
        if (!node.folder) {
            var iid = node.key
            if (node.selected) {
                muting.set(iid, 1)
            }
            else {
                if (muting.isSet(iid)) {
                    muting.remove(iid)
                }
            }
        }
    }
    this.store_select_deep = function(node) {
        this.store_select(node)
        var children = node.children
        if (children != null) {
            for (n in children) {
                this.store_select_deep(children[n])
            }
        }
    }
    this.dress_queries = function() {
        $('#queries a.md').addClass('ui-icon ui-icon-link')
        $('#queries a.qx').addClass('ui-icon ui-icon-gear')
        $('#queries a[qid]').each(function() {
            $(this).attr('href', q_url+'?iid='+$(this).attr('qid')+'&page=1&mr=r&qw=q')
        })
        $('#queries a.md').click(function(e) {e.preventDefault();
            var uname = $(this).closest('ul').closest('li').find('span[n]').html()
            var tit = $(this).prev()
            var lnk = tit.attr('href')
            var qname = tit.html()
            window.prompt('Press <Cmd-C> and then <Enter> to copy link on clipboard', '['+uname+': '+qname+']('+lnk+')')
        })
    }
    this.record = function(tp, o, update, view) {
        var lid = $('#id_'+tp).val()
        if (!update && lid == '0' && tp != 'q') {
            return
        }
        var senddata = {
            tp: tp,
            upd: update,
            lid: lid,
            name: $('#name_'+tp).val(),
        }
        if (tp == 'q') {
            senddata['description'] = $('#description_'+tp).val()
            senddata['oid'] = $('#fo_q').attr('oid')
            senddata['pid'] = $('#fp_q').attr('pid')
        }
        else {
            senddata['website'] = $('#website_'+tp).val()
        }
        var good = false
        $.post(record_url, senddata, function(json) {
            var tpp = tp
            if (view) {
                tpp = tp + 'v'
            }
            var rec = json.record
            good = json.good
            msg.clear(tpp)
            json.msgs.forEach(function(m) {
                msg.msg(tpp, m)
            })
            if (!update || good) {
                that.selectid('o', rec.oid, null)
                that.selectid('p', rec.pid, o)
            }
            if (!update || (good && senddata.lid != '0')) {
                if (view) {
                    $('#name_'+tpp).html(rec.name)
                }
                else {
                    $('#name_'+tpp).val(rec.name)
                }
                if (tpp == 'q' || tpp == 'qv') {
                    var oname = (rec.oname == undefined)?'':escapeHTML(rec.oname);
                    var pname = (rec.pname == undefined)?'':escapeHTML(rec.pname);
                    $('#description_'+tpp).val(rec.description)
                    $('#description_old_'+tpp).html(rec.description_md)
                    $('#fo_'+tpp).attr('href', rec.owebsite)
                    $('#fo_'+tpp).html(escapeHTML(oname))
                    $('#fp_'+tpp).attr('href', rec.pwebsite)
                    $('#fp_'+tpp).html(escapeHTML(pname))
                    $('#fo_'+tpp).attr('oid', rec.oid)
                    $('#fp_'+tpp).attr('pid', rec.pid)
                }
                else {
                    $('#website_'+tpp).val(rec.website)
                }
                if (update) {
                    var elem = (tpp == 'q')?'a':'span'
                    $('.treehl').find(elem+'[n=1]').html(escapeHTML(rec.name))
                }
            }
            if (update && good && senddata.lid == '0') {
                if (tpp == 'q') {
                    var oname = (rec.oname == undefined)?'':escapeHTML(rec.oname);
                    var pname = (rec.pname == undefined)?'':escapeHTML(rec.pname);
                    $('#fo_'+tpp).attr('href', rec.owebsite)
                    $('#fo_'+tpp).html(escapeHTML(oname))
                    $('#fp_'+tpp).attr('href', rec.pwebsite)
                    $('#fp_'+tpp).html(escapeHTML(pname))
                    $('#fo_'+tpp).attr('oid', rec.oid)
                    $('#fp_'+tpp).attr('pid', rec.pid)
                }
            }
            var orig = $('.treehl')
            var origp = orig.closest('ul').closest('li').closest('ul').closest('li')
            var origo = origp.closest('ul').closest('li')
            var origoid = origo.find('a[lid]').attr('lid')
            var origpid = origp.find('a[lid]').attr('lid')
            if (update && good && (senddata.lid == '0' || origoid != rec.oid || origpid != rec.pid)) {
                $('#reload_tree').show()
            }
            else {
                $('#reload_tree').hide()
            }
        }, 'json')
    }
    this.do_create = function(tp, obj) {
        msg.clear(tp)
        $('.form_l').hide()
        $('#title_'+tp).html('Add new')
        $('#name_'+tp).val('')
        var o = null
        if (tp == 'q') {
            o = obj.closest('ul').closest('li')
            var oid = o.find('a[lid]').attr('lid')
            var p = obj.closest('li')
            var pid = p.find('a[lid]').attr('lid')
            $('#description_'+tp).val('')
            $('#fo_q').attr('oid', oid)
            $('#fp_q').attr('pid', pid)
        }
        else {
            $('#website_'+tp).val('')
            if (tp == 'p') {
                o = obj.closest('li')
            }
        }
        $('#id_'+tp).val(0)
        $('#save_'+tp).html('Add')
        this.record(tp, o, false, false)
        $('#form_'+tp).show()
        $('.old').hide()
    }
    this.do_update = function(tp, obj, lid) {
        var o = null
        if (tp == 'q') {
            o = obj.closest('ul').closest('li').closest('ul').closest('li').closest('ul').closest('li')
        }
        else if (tp == 'p') {
            o = obj.closest('ul').closest('li')
        }
        msg.clear(tp)
        msg.msg(tp, ['info', 'loading ...'])
        $('.form_l').hide()
        $('#title_'+tp).html('Modify')
        $('#id_'+tp).val(lid)
        $('#save_'+tp).html('Update')
        this.record(tp, o, false, false)
        $('#form_'+tp).show()
        $('.old').show()
    }
    this.do_view = function(tp, obj, lid) {
        var o = null
        if (tp == 'q') {
            o = obj.closest('ul').closest('li').closest('ul').closest('li').closest('ul').closest('li')
        }
        else if (tp == 'p') {
            o = obj.closest('ul').closest('li')
        }
        var mtp = tp+'v'
        msg.clear(mtp)
        msg.msg(mtp, ['info', 'loading ...'])
        $('.form_l').hide()
        $('#title_'+tp).html('View')
        $('#id_'+tp).val(lid)
        this.record(tp, o, false, true)
        $('#formv_'+tp).show()
    }
    this.op_selection = function(tp) {
        if (tp == 'q') {
            this.select_clear('o', true)
            this.select_clear('p', true)
        }
        else {
            this.select_hide()
        }
    }
    this.select_hide = function() {
        for (tp in {o: 1, p: 1}) {
            this.select_clear(tp, false)
        }
    }
    this.select_clear = function(tp, show) {
        var objs = $('.selecthl'+tp) 
        var icons = $('.s_'+tp)
        objs.removeClass('selecthl'+tp)
        icons.removeClass('ui-icon-radio-on')
        icons.addClass('ui-icon-radio-off')
        if (show) {
            icons.show()
        }
        else {
            icons.hide()
        }
    }
    this.selectid = function(tp, lid, pr) {
        var jpr = '.s_'+tp+'[lid='+lid+']'
        var icon = (pr == null)?$(jpr):pr.find(jpr)
        var i = icon.closest('li')
        var is = i.children('span')
        this.selectone(tp, icon, is)
    }
    this.selectone = function(tp, icon, obj) {
        var sclass= 'selecthl'+tp
        var objs = $('.'+sclass) 
        var icons = (tp == 'o')?$('.s_'+tp):icon.closest('ul').find('.s_'+tp)
        var iconsr = $('.s_'+tp)
        objs.removeClass(sclass)
        obj.addClass(sclass)
        iconsr.removeClass('ui-icon-radio-on')
        iconsr.addClass('ui-icon-radio-off')
        icon.removeClass('ui-icon-radio-off')
        icon.addClass('ui-icon-radio-on')
    }
    this.viewinit = function() {
        $('.form_l').hide()
        $('.treehl').removeClass('treehl')
        this.select_hide()
    }
    this.bothinit = function() {
        var canvas_left = $('.left-sidebar')
        var canvas_middle = $('.span6')
        var canvas_right = $('.right-sidebar')
        canvas_left.css('width', '15%')
        canvas_middle.css('width','35%')
        canvas_right.css('width', '40%')
        var view = $('.v_q') 
        view.addClass('ui-icon ui-icon-info')
        this.viewtp = function(tp) {
            if (tp != 'q') {
                return
            }
            var objs = $('.v_'+tp);
            objs.click(function(e) {e.preventDefault();
                $('.treehl').removeClass('treehl')
                that.op_selection(tp)
                $(this).closest('span').addClass('treehl')
                var lid = $(this).attr('lid')
                that.do_view(tp, $(this), lid)
                return false
            })
        }
        this.select_init = function(tp) {
            var objs = $('.s_'+tp);
            objs.click(function(e) {e.preventDefault();
                if (tp == 'o') {
                    var o = $(this).closest('li')
                    var oid = o.find('a[lid]').attr('lid')
                    var oname = o.find('span[n=1]').html()
                    $('#fo_q').html(oname)
                    $('#fo_q').attr('oid', oid)
                    that.selectid('o', oid, null)
                }
                else if (tp == 'p') {
                    var o = $(this).closest('ul').closest('li')
                    var oid = o.find('a[lid]').attr('lid')
                    var oname = o.find('span[n=1]').html()
                    var p = $(this).closest('li')
                    var pid = p.find('a[lid]').attr('lid')
                    var pname = p.find('span[n=1]').html()
                    $('#fo_q').html(oname)
                    $('#fp_q').html(pname)
                    $('#fo_q').attr('oid', oid)
                    $('#fp_q').attr('pid', pid)
                    that.selectid('o', oid, null)
                    that.selectid('p', pid, o)
                }
                return false
            })
        }
        for (var t in this.tps) {
            $('#form_'+t).hide()
            $('#formv_'+t).hide()
            this.viewtp(t)
            if (t == 'q') {
                this.select_init('o')
                this.select_init('p')
            }
        }
    }
    this.editinit = function() {
        $('.treehl').removeClass('treehl')
        var select = $('.s_o,.s_p') 
        select.addClass('ui-icon ui-icon-radio-off')
        select.hide()
        var create = $('.n_o, .n_p, .n_q'); 
        create.addClass('ui-icon ui-icon-plus')
        this.createtp = function(tp) {
            var objs = $('.n_'+tp);
            objs.click(function(e) {e.preventDefault();
                $('.treehl').removeClass('treehl')
                that.op_selection(tp)
                $(this).closest('span').addClass('treehl')
                that.do_create(tp, $(this))
                return false
            })
        }
        var update = $('.r_o, .r_p, .r_q') 
        update.addClass('ui-icon ui-icon-pencil')
        this.updatetp = function(tp) {
            var objs = $('.r_'+tp);
            objs.click(function(e) {e.preventDefault();
                $('.treehl').removeClass('treehl')
                that.op_selection(tp)
                $(this).closest('span').addClass('treehl')
                var lid = $(this).attr('lid')
                that.do_update(tp, $(this), lid)
                return false
            })
        }
        this.formtp = function(tp) {
            $('#save_'+tp).click(function(e) {e.preventDefault();
                that.op_selection(tp)
                that.record(tp, null, true, false)
            })
            $('#cancel_'+tp+', #done_'+tp).click(function(e) {e.preventDefault();
                $('.treehl').removeClass('treehl')
                that.select_hide()
                $('#form_'+tp).hide()
                $('#formv_'+tp).hide()
            })
            $('#reload_tree').click(function(e) {e.preventDefault();
                window.location.reload(true)
            })
        }
        for (var t in this.tps) {
            $('#form_'+t).hide()
            $('#formv_'+t).hide()
            this.createtp(t)
            this.updatetp(t)
            this.formtp(t)
        }
    }
    this.gotoquery = function(qid) {
        if (qid != undefined && qid != '0') {
            var qnode = this.ftw.getNodeByKey('q'+qid)
            qnode.makeVisible({noAnimation: true})
            $('.treehl').removeClass('treehl')
            $('a[qid='+qid+']').closest('span').addClass('treehl')
            $(qnode.li)[0].scrollIntoView()
            var editable = $(qnode.li).has('.r_q').length > 0
            if (editable) {
                var qtitle = $('a[qid='+qid+']').nextAll('.r_q')
                this.do_update('q', qtitle, qid)
            }
            else {
                var qtitle = $('a[qid='+qid+']').nextAll('.v_q')
                this.do_view('q', qtitle, qid)
            }
        }
    }

    $("#queries").fancytree({
        extensions: ["persist", "filter"],
        checkbox: true,
        selectMode: 3,
        activeVisible: true,
        toggleEffect: false,
        clickFolderMode: 2,
        focusOnSelect: false,
        quicksearch: true,
        icons: false,
        persist: {
            store: 'local',
            types: 'expanded selected',
        },
        source: {
            url: pq_url,
            dataType: "json",
        },
        filter: {
            mode: 'hide',
        },
        init: function(e, data) {
            muting.removeAll()
            that.ftw =  $("#queries").fancytree('getTree')
            var s = that.ftw.getSelectedNodes(true)
            for (i in s) {
                that.store_select_deep(s[i])
            }
            that.ftw.render(true, true)
            that.dress_queries()
            rdata = that.ftw.rootNode.children[0].data
            $('#count_o').html(rdata.o)
            $('#count_p').html(rdata.p)
            $('#count_u').html(rdata.u)
            $('#count_q').html(rdata.q)
            msg = new Msg()
            that.view = new View()
            that.level = new Level()
            that.filter = new Filter()
            that.level.initlevel()
            if (rdata.uid) {
                that.editinit()
            }
            else {
                that.viewinit()
            }
            that.bothinit()
            that.gotoquery($('#qid').val()) 
            $('#reload_tree').hide()
        },
        expand: function(e, data) {
            if (that.level != undefined) {
                that.level.expand_level('')
            }
        },
        collapse: function(e, data) {
            if (that.level != undefined) {
                that.level.expand_level('')
            }
        },
        select: function(e, data) {
            that.store_select_deep(data.node)
        },
    })
    var standard_height = window.innerHeight - subtract
    var standard_width = window.innerWidth
    var canvas_left = $('.left-sidebar')
    var canvas_middle = $('.span6')
    var canvas_right = $('.right-sidebar')
    canvas_left.css('height', standard_height+'px')
    $('#queries').css('height', standard_height+'px')
    $('#opqforms').css('height', standard_height+'px')
    canvas_right.css('height', standard_height+'px')
}

$(function(){
    ftree = new Tree()
})
