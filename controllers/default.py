EXPIRE = 3600 * 24 * 30

# def myerror(): return 1/0


# The next bit is used to be able to "import" this file
# for the purposes of documentation generation by mkdocstrings


if "cache" not in globals():

    class Dummy:
        def action(self):
            return lambda f: f

        def requires_signature(self):
            return lambda f: f

    cache = Dummy()
    auth = Dummy()


def index():
    """Serves the **home** page.

    Corresponds with the SHEBANQ logo in the navigation bar.
    """
    session.forget(response)
    response.title = T("SHEBANQ")
    response.subtitle = T("Query the Hebrew Bible through the BHSA database")
    return dict()


def user():
    """Unchanged from Web2py.

    ```
    exposes:
    http://..../[app]/default/user/login
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    http://..../[app]/default/user/manage_users (requires membership in
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    ```
    """

    response.title = T("User Profile")
    return dict(form=auth())


@cache.action()
def download():
    """Unchanged from Web2py.

    ```
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    ```
    """
    return response.download(request, db)


def call():
    """Unchanged from Web2py.

    ```
    exposes services. for example:
    http://..../[app]/default/call/jsonrpc
    decorate with @services.jsonrpc the functions to expose
    supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
    ```
    """
    return service()  # noqa F821


@auth.requires_signature()
def data():
    """Unchanged from Web2py.

    ```
    http://..../[app]/default/data/tables
    http://..../[app]/default/data/create/[table]
    http://..../[app]/default/data/read/[table]/[id]
    http://..../[app]/default/data/update/[table]/[id]
    http://..../[app]/default/data/delete/[table]/[id]
    http://..../[app]/default/data/select/[table]
    http://..../[app]/default/data/search/[table]
    but URLs must be signed, i.e. linked with
      A('table',_href=URL('data/tables',user_signature=True))
    or with the signed load operator
      LOAD('default','data.load',args='tables',ajax=True,user_signature=True)
    ```
    """
    return dict(form=crud())  # noqa F821
