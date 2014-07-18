"""Original code source:
`Web2Py Slices - Widget Select or Add Option <http://www.web2pyslices.com/slice/show/1616/widget-select-or-add-option-ng>`_.
"""


def referenced_data():
    """ shows dialog with reference add/edit form
    the idea is taken from "data" function, just first argument is the id of calling select box
    """
    try:
        references_options_list_id = request.args[0]
    except:
        return T("ERR: references_options_list_id lacking")
    try:
        action = request.args[1]
    except:
        return T("ERR: action lacking")
    try:
        referenced_table = request.args[2]
    except:
        return T("ERR: referenced_table lacking")

    if action == "edit":
        try:
            referenced_record_id = int(request.args[3])
        except:
            response.flash = T("ERR: referenced_record_id lacking")
            return (response.flash)
        form = SQLFORM(db[referenced_table], referenced_record_id)  # edit/update/change
    else:
        form = SQLFORM(db[referenced_table])  # new/create/add

    if form.accepts(request.vars):
        # Then let the user know adding via our widget worked
        response.flash = "done: %s %s" % (T(action), referenced_table)  # added / edited
        # close the widget's dialog box
        response.js = '$( "#%s_%s_dialog-form" ).dialog( "close" ); ' % (references_options_list_id, action)

        def format_referenced(id):
            table = db[referenced_table]
            if isinstance(table._format, str):
                return table._format % table[id]
            elif callable(table._format):
                return table._format(table[id])
            else:
                return "???"

        if action == 'new':
                # update the options they can select their new category in the main form
                response.js += """$("#%s").append("<option value='%s'>%s</option>");""" % (references_options_list_id, form.vars.id, format_referenced(form.vars.id))
                # and select the one they just added
                response.js += """$("#%s").val("%s");""" % (references_options_list_id, form.vars.id)
        if action == 'edit':
            response.js += """$('#%s option[value="%s"]').html('%s')""" % (references_options_list_id, form.vars.id, format_referenced(form.vars.id))
    return BEAUTIFY(form)
