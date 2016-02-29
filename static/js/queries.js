var pq_url, q_url, record_url, queriesr_url
var ns = $.initNamespaceStorage('muting_q')
var vs = $.initNamespaceStorage('qsview')
var muting = ns.localStorage
var qsview = vs.localStorage
var ftree, msgflt, msgopq, rdata
var subtract = 80 // the canvas holding the material gets a height equal to the window height minus this amount
var control_height = 100 // height for messages and controls

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

function Recent() {
    var that = this
    this.loaded = false
    this.queries = []
    this.msgqr = new Msg('msg_qr')
    this.refreshctl = $('#reload_recentq')
    var target = $('#recentqi')

    this.fetch = function() {
        this.msgqr.msg(['info', 'fetching recent queries ...'])
        $.post(queriesr_url, {}, function(json) {
            that.loaded = true
            that.msgqr.clear()
            json.msgs.forEach(function(m) {
                that.msgqr.msg(m)
            })
            if (json.good) {
                that.queries = json.queries
                that.process()
            }
        })
    }
    this.process = function() {
        this.gen_html()
        this.dress_queriesr()
    }
    this.gen_html = function() {
        var queries = this.queries
        var html = ''
        for (var n = 0; n < queries.length; n++) {
            var query = queries[n]
            var qid = query['id']
            var qtxt = query['text']
            var qtit = query['title']
            var qver = query['version']
            html += '<a class="q" qid="'+qid+'" v="'+qver+'" href="#" title="'+qtit+'">'+qtxt+'</a><br/>\n'
        }
        target.html(html)
    }
    this.dress_queriesr = function() {
        $('#recentqi a[qid]').each(function() {
            $(this).click(function(e) {e.preventDefault();
                ftree.filter.clear()
                ftree.gotoquery($(this).attr('qid'))
            })
        })
    }
    this.msgqr.clear()
    this.refreshctl.click(function(e) {e.preventDefault();that.fetch()})
    this.apply = function() {
        this.fetch()
    }
    this.apply()
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
            n.setExpanded(true, {noAnimation: true, noEvents: false})
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
                n.setExpanded(nlevel <= numlevel , {noAnimation: true, noEvents: false})
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
        msgflt.clear()
        msgflt.msg(['good', 'no filter applied'])
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
            msgflt.clear()
            msgflt.msg(['warning', 'my queries'])
        }
        else if (kind == 'r') {
            msgflt.clear()
            msgflt.msg(['warning', 'private queries'])
        }
        else if (pat == '') {
            this.clear()
            return
        }
        else {
            msgflt.clear()
            msgflt.msg(['special', 'filter applied'])
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

function Msg(destination) {
    var that = this
    this.destination = $('#'+destination)
    this.trashc = $('#trash_'+destination)
    this.clear = function() {
        this.destination.html('')
        this.trashc.hide()
    }
    this.trashc.click(function(e) {e.preventDefault();
        that.clear()
    })
    this.msg = function(msgobj) {
        var mtext = this.destination.html()
        this.destination.html(mtext+'<p class="'+msgobj[0]+'">'+msgobj[1]+'</p>')
        this.trashc.show()
    }
    this.trashc.hide()
}

function Tree() {
    var that = this
    this.tps = {o: 'organization', p:'project', q:'query'}
    this.do_new = {}

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
        $('#queries a.md').addClass('fa fa-level-down')
        $('#queries a[qid]').each(function() {
            var vr = $(this).attr('v')
            var extra = (vr == undefined)?'':'&version='+vr;
            $(this).attr('href', q_url+'?iid='+$(this).attr('qid')+extra+'&page=1&mr=r&qw=q')
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
            senddata['oid'] = $('#fo_q').attr('oid')
            senddata['oname'] = $('#nameq_o').val()
            senddata['owebsite'] = $('#websiteq_o').val()
            senddata['pid'] = $('#fp_q').attr('pid')
            senddata['pname'] = $('#nameq_p').val()
            senddata['pwebsite'] = $('#websiteq_p').val()
            senddata['do_new_o'] = this.do_new['o']
            senddata['do_new_p'] = this.do_new['p']
        }
        else {
            senddata['website'] = $('#website_'+tp).val()
        }
        var good = false
        $.post(record_url, senddata, function(json) {
            var rec = json.record
            var orec = json.orecord
            var prec = json.precord
            good = json.good
            ogood = json.ogood
            pgood = json.pgood
            msgopq.clear()
            json.msgs.forEach(function(m) {
                msgopq.msg(m)
            })
            if (update && tp == 'q') {
                if (good) {
                    that.selectid('o', rec.oid, null)
                    that.selectid('p', rec.pid, o)
                }
                else {
                    if (ogood) {
                        that.selectid('o', orec.id, null)
                    }
                    if (pgood) {
                        that.selectid('p', prec.id, o)
                    }
                }
            }
            if (!update) {
                var name = $('#name_'+tp)
                name.prop('readonly', view)
                name.val(rec.name)
                if (tp == 'q') {
                    var oname = (rec.oname == undefined)?'':escapeHTML(rec.oname);
                    var pname = (rec.pname == undefined)?'':escapeHTML(rec.pname);
                    $('#fo_'+tp).attr('href', rec.owebsite)
                    $('#fo_'+tp).html(escapeHTML(oname))
                    $('#fp_'+tp).attr('href', rec.pwebsite)
                    $('#fp_'+tp).html(escapeHTML(pname))
                    $('#fo_'+tp).attr('oid', rec.oid)
                    $('#fp_'+tp).attr('pid', rec.pid)
                }
                else {
                    $('#website_'+tp).val(rec.website)
                    $('#f'+tp+'_v').attr('href', rec.owebsite)
                    $('#f'+tp+'_v').html(escapeHTML(rec.name))
                }
            }
            else if (update && senddata.lid != '0') {
                if (tp == 'q') {
                    if (good) {
                        var oname = (rec.oname == undefined)?'':escapeHTML(rec.oname);
                        var pname = (rec.pname == undefined)?'':escapeHTML(rec.pname);
                        that.hide_new_q(rec.id, 'o')
                        that.hide_new_q(rec.id, 'p')
                        $('#fo_'+tp).attr('href', rec.owebsite)
                        $('#fo_'+tp).html(escapeHTML(oname))
                        $('#fp_'+tp).attr('href', rec.pwebsite)
                        $('#fp_'+tp).html(escapeHTML(pname))
                        $('#fo_'+tp).attr('oid', rec.oid)
                        $('#fp_'+tp).attr('pid', rec.pid)
                        $('#title_q').html('Modify')
                    }
                    else {
                        if (ogood) {
                            var oname = (orec.name == undefined)?'':escapeHTML(orec.name);
                            that.hide_new_q(orec.id, 'o')
                            $('#fo_'+tp).attr('href', orec.website)
                            $('#fo_'+tp).html(escapeHTML(oname))
                            $('#fo_'+tp).attr('oid', orec.id)
                        }
                        if (pgood) {
                            var pname = (prec.name == undefined)?'':escapeHTML(prec.name);
                            that.hide_new_q(prec.id, 'p')
                            $('#fp_'+tp).attr('href', prec.website)
                            $('#fp_'+tp).html(escapeHTML(pname))
                            $('#fp_'+tp).attr('pid', prec.id)
                        }
                    }
                }
                else {
                    $('#website_'+tp).val(rec.website)
                    $('#f'+tp+'_v').attr('href', rec.owebsite)
                    $('#f'+tp+'_v').html(escapeHTML(rec.name))
                }
                var elem = (tp == 'q')?'a':'span'
                var moditem = that.moditem.find(elem+'[n=1]')
                if (moditem != undefined) {
                    moditem.html(escapeHTML(rec.name))
                }
            }
            else if (update && senddata.lid == '0') {
                if (good) {
                    $('#id_'+tp).val(rec.id)
                }
                if (tp == 'q') {
                    if (good) {
                        var oname = (rec.oname == undefined)?'':escapeHTML(rec.oname);
                        var pname = (rec.pname == undefined)?'':escapeHTML(rec.pname);
                        that.hide_new_q(rec.id, 'o')
                        that.hide_new_q(rec.id, 'p')
                        $('#fo_'+tp).attr('href', rec.owebsite)
                        $('#fo_'+tp).html(escapeHTML(oname))
                        $('#fp_'+tp).attr('href', rec.pwebsite)
                        $('#fp_'+tp).html(escapeHTML(pname))
                        $('#fo_'+tp).attr('oid', rec.oid)
                        $('#fp_'+tp).attr('pid', rec.pid)
                        $('#title_q').html('Modify')
                    }
                    else {
                        if (ogood) {
                            var oname = (orec.name == undefined)?'':escapeHTML(orec.name);
                            that.hide_new_q(orec.id, 'o')
                            $('#fo_'+tp).attr('href', orec.website)
                            $('#fo_'+tp).html(escapeHTML(oname))
                            $('#fo_'+tp).attr('oid', orec.id)
                        }
                        if (pgood) {
                            var pname = (prec.name == undefined)?'':escapeHTML(prec.name);
                            that.hide_new_q(prec.id, 'p')
                            $('#fp_'+tp).attr('href', prec.website)
                            $('#fp_'+tp).html(escapeHTML(pname))
                            $('#fp_'+tp).attr('pid', prec.id)
                        }
                    }
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
            if (update && good && tp == 'q') {
                $('#continue_q').attr('href', q_url+'?iid='+$('#id_q').val()+'&page=1&mr=r&qw=q')
                $('#continue_q').show()
            }
            else {
                $('#continue_q').hide()
            }
        }, 'json')
    }
    this.do_edit_controls_q = function() {
        var ctlo = $('#new_ctrl_o')
        var ctlp = $('#new_ctrl_p')
        var ctlxo = $('#newx_ctrl_o')
        var ctlxp = $('#newx_ctrl_p')
        var detailo = $('.detail_o')
        var detailp = $('.detail_p')
        var existo = $('#fo_q')
        var existp = $('#fp_q')
        detailo.hide()
        detailp.hide()
        ctlxo.hide()
        ctlxp.hide()
        ctlo.click(function(e) {e.preventDefault();
            detailo.show()
            ctlxo.show()
            ctlo.hide()
            existo.hide()
            that.do_new['o'] = true
        })
        ctlxo.click(function(e) {e.preventDefault();
            detailo.hide()
            ctlxo.hide()
            ctlo.show()
            existo.show()
            that.do_new['o'] = false
        })
        ctlp.click(function(e) {e.preventDefault();
            detailp.show()
            ctlxp.show()
            ctlp.hide()
            existp.hide()
            that.do_new['p'] = true
            that.select_clear('p', true)
        })
        ctlxp.click(function(e) {e.preventDefault();
            detailp.hide()
            ctlxp.hide()
            ctlp.show()
            existp.show()
        })
    }
    this.hide_new_q = function(lid, tp) {
        $('#new_ctrl_'+tp).show()
        $('#newx_ctrl_'+tp).hide()
        $('.detail_'+tp).hide()
        $('#f'+tp+'_q').show()
        that.do_new[tp] = false
    }
    this.do_view_controls_q = function() {
        var ctlo = $('#new_ctrl_o')
        var ctlp = $('#new_ctrl_p')
        var ctlxo = $('#newx_ctrl_o')
        var ctlxp = $('#newx_ctrl_p')
        var detailo = $('.detail_o')
        var detailp = $('.detail_p')
        var existo = $('#fo_q')
        var existp = $('#fp_q')
        detailo.hide()
        detailp.hide()
        ctlo.hide()
        ctlxo.hide()
        ctlp.hide()
        ctlxp.hide()
    }
    this.do_create = function(tp, obj) {
        msgopq.clear()
        $('.form_l').hide()
        $('.ctrl_l').hide()
        $('#title_'+tp).html('New')
        $('#name_'+tp).val('')
        var o = null
        if (tp == 'q') {
            this.do_new['o'] = false
            this.do_new['p'] = false
            $('#fo_q').attr('oid', 0)
            $('#fp_q').attr('pid', 0)
            this.do_edit_controls_q()
        }
        else {
            $('#website_'+tp).val('')
            if (tp == 'p') {
                o = obj.closest('li')
            }
        }
        $('#id_'+tp).val(0)
        this.record(tp, o, false, false)
        $('#opqforms').show()
        $('#opqctrl').show()
        $('#form_'+tp).show()
        $('#ctrl_'+tp).show()
        $('.old').hide()
    }
    this.do_update = function(tp, obj, lid) {
        var o = null
        if (tp == 'q') {
            this.do_new['o'] = false
            this.do_new['p'] = false
            o = obj.closest('ul').closest('li').closest('ul').closest('li').closest('ul').closest('li')
            this.do_edit_controls_q()
        }
        else if (tp == 'p') {
            o = obj.closest('ul').closest('li')
        }
        this.moditem = obj.closest('span')
        msgopq.clear()
        msgopq.msg(['info', 'loading ...'])
        $('.form_l').hide()
        $('.ctrl_l').hide()
        $('#title_'+tp).html('Modify')
        $('#id_'+tp).val(lid)
        this.record(tp, o, false, false)
        $('#opqforms').show()
        $('#opqctrl').show()
        $('#form_'+tp).show()
        $('#ctrl_'+tp).show()
        $('.old').show()
    }
    this.do_view = function(tp, obj, lid) {
        var o = null
        if (tp == 'q') {
            o = obj.closest('ul').closest('li').closest('ul').closest('li').closest('ul').closest('li')
            this.do_view_controls_q()
        }
        else if (tp == 'p') {
            o = obj.closest('ul').closest('li')
        }
        var mtp = tp+'v'
        msgopq.clear()
        msgopq.msg(['info', 'loading ...'])
        $('.form_l').hide()
        $('.ctrl_l').hide()
        $('#title_'+tp).html('View')
        $('#id_'+tp).val(lid)
        this.record(tp, o, false, true)
        $('#opqforms').show()
        $('#opqctrl').show()
        $('#form_'+tp).show()
        if (tp == 'o' || tp == 'p') {
            $('#nameline_'+tp).hide()
            $('#website_'+tp).hide()
            $('#f'+tp+'_v').show()
        }
        this.select_hide()
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
        icons.removeClass('fa-check-circle')
        icons.addClass('fa-circle-o')
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
        iconsr.removeClass('fa-check-circle')
        iconsr.addClass('fa-circle-o')
        icon.removeClass('fa-circle-o')
        icon.addClass('fa-check-circle')
    }
    this.viewinit = function() {
        $('#lmsg').show()
        $('.form_l').hide()
        $('.ctrl_l').hide()
        $('.treehl').removeClass('treehl')
        this.select_hide()
    }
    this.bothinit = function() {
        var canvas_left = $('.left-sidebar')
        var canvas_middle = $('.span6')
        var canvas_right = $('.right-sidebar')
        canvas_left.css('width', '23%')
        canvas_middle.css('width','40%')
        canvas_right.css('width', '30%')
        var view = $('.v_o, .v_p, .v_q') 
        view.addClass('fa fa-info')
        this.viewtp = function(tp) {
            /*if (tp != 'q') {
                return
            }*/
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
            $('#ctrl_'+t).hide()
            this.viewtp(t)
            if (t == 'q') {
                this.select_init('o')
                this.select_init('p')
            }
        }
    }
    this.editinit = function() {
        $('.treehl').removeClass('treehl')
        $('#lmsg').hide()
        var select = $('.s_o,.s_p') 
        select.addClass('fa-circle-o')
        select.hide()
        var create = $('.n_q'); 
        create.addClass('fa fa-plus')
        this.createtp = function(tp) {
            var objs = $('.n_'+tp);
            objs.click(function(e) {e.preventDefault();
                $('.treehl').removeClass('treehl')
                that.op_selection(tp)
                if (tp == 'q') {
                    $('#id_q').val(0)
                }
                $(this).closest('span').addClass('treehl')
                that.do_create(tp, $(this))
                return false
            })
        }
        var update = $('.r_o, .r_p, .r_q') 
        update.addClass('fa fa-pencil')
        this.updatetp = function(tp) {
            var objs = $('.r_'+tp);
            objs.click(function(e) {e.preventDefault();
                $('.treehl').removeClass('treehl')
                that.op_selection(tp)
                $(this).closest('span').addClass('treehl')
                var lid = $(this).attr('lid')
                if (tp == 'q') {
                    $('#id_q').val(lid)
                }
                that.do_update(tp, $(this), lid)
                return false
            })
        }
        this.formtp = function(tp) {
            $('#save_'+tp).click(function(e) {e.preventDefault();
                that.op_selection(tp)
                that.record(tp, null, true, false)
            })
            $('#cancel_'+tp).click(function(e) {e.preventDefault();
                $('.treehl').removeClass('treehl')
                that.select_hide()
                $('#form_'+tp).hide()
                $('#ctrl_'+tp).hide()
            })
            $('#done_'+tp).click(function(e) {e.preventDefault();
                that.op_selection(tp)
                that.record(tp, null, true, false)
                that.select_hide()
                $('#form_'+tp).hide()
                $('#ctrl_'+tp).hide()
            })
            $('#reload_tree').click(function(e) {e.preventDefault();
                window.location.reload(true)
            })
        }
        for (var t in this.tps) {
            $('#form_'+t).hide()
            $('#ctrl_'+t).hide()
            this.createtp(t)
            this.updatetp(t)
            this.formtp(t)
        }
    }
    this.gotoquery = function(qid) {
        if (qid != undefined && qid != '0') {
            var qnode = this.ftw.getNodeByKey('q'+qid)
            if (qnode != undefined) {
                qnode.makeVisible({noAnimation: true})
                $('.treehl').removeClass('treehl')
                $('a[qid='+qid+']').closest('span').addClass('treehl')
                $(qnode.li)[0].scrollIntoView({
                    behavior: "smooth",
                })
                $('#queries').scrollTop -= 20
                /*
                var editable = $(qnode.li).has('.r_q').length > 0
                if (editable) {
                    var qtitle = $('a[qid='+qid+']').nextAll('.r_q')
                    this.do_update('q', qtitle, qid)
                }
                else {
                    var qtitle = $('a[qid='+qid+']').nextAll('.v_q')
                    this.do_view('q', qtitle, qid)
                }
                */
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
        idPrefix: 'q_',
        persist: {
            cookiePrefix: 'ft-q-',
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
            msgopq = new Msg('opqmsgs')
            msgflt = new Msg('filter_msg')
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
    var form_height = standard_height - control_height
    var standard_width = window.innerWidth
    var canvas_left = $('.left-sidebar')
    var canvas_middle = $('.span6')
    var canvas_right = $('.right-sidebar')
    canvas_left.css('height', standard_height+'px')
    $('#queries').css('height', standard_height+'px')
    //$('#opqforms').css('height', form_height+'px')
    $('#opqctrl').css('height', control_height+'px')
    canvas_right.css('height', standard_height+'px')
}

$(function(){
    recent = new Recent()
    ftree = new Tree()
})
