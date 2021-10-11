# Documentation

## User documentation

### User guide of SHEBANQ

How to use SHEBANQ is documented on the
[wiki of the SHEBANQ repository on Github]({{wiki}}).

People with access can edit those pages directly in the browser, if they are logged
in with GitHub.

You can also clone the wiki:

```
cd ~/github/etcbc
git clone {{wiki}}
```

Then you can make as many edits as you like, in whatever tool you like,
and save it back to the online version by

```
cd ~/github/etcbc/shebanq.wiki
git add --all .
git commit "updated docs"
git push origin master
```

### Feature documentation of the BHSA

This is stored in the [BHSA]({{bhsa}}) repository and published
via its GitHub pages method.

The source docs are in its
[docs]({{bhsa}}/tree/master/docs) directory.

If you have cloned you can edit the docs locally,
and then build the docs via [mkdocs]({{mkdocs}}).

You install mkdocs by

```
pip3 install mkdocs
pip3 install mkdocs-material
```

In order to build the documentation you do

```
cd ~/github/etcbc/bhsa
mkdocs build
```

In order to publish it, you do

```
cd ~/github/etcbc/bhsa
mkdocs gh-deploy
```

Note that publishing will trigger a build, so if you want to publish,
you can leave out the build step.

Finally, you can commit the changes to the doc sources by:

```
cd ~/github/etcbc/bhsa
git add --all .
git commit "updated feature docs"
git push origin master
```

### Technical documentation

The technical documentation of SHEBANQ is also by means of mkdocs.

In order to modify it, you have to install it, and a plugin:

```
pip3 install mkdocs
pip3 install mkdocs-material
pip3 install mkdocstrings
pip3 install 'pytkdocs[numpy-style]'
```

You need an extra tool for Javascript documentation:

```
npm install -g jsdoc
npm install -g jsdoc-to-markdown
```

Apart from a nest of markdown files, the documentation consists also
of special comments extract from the Python and Javascript code.

We get the Python docstrings by means of the mkdocs plugin mkdocstrings.

We get the Javascript docstrings by means of jsdoc and jsdoc-to-markdown.

We have [build script](maintenance.md#operation) to automate the maintenance steps,
and it also takes care of documentation handling.

Just do 

```
cd ~/github/etcbc/shebanq
python3 build.py --help
```

to look at the options, or inspect the
[source code]({{repo}}/blob/master/build.py).

#### Why mkdocs?

One of the advantages of mkdocs is that you can 'invoke' docstring documentation
from within markdown files. It will then inject the formatted docstrings
at that place in the documentation.

That is handy, because this SHEBANQ is not a usual Python package, such as
[Text-Fabric]({{textfabric}}) is.
For example, automatically building documentation for the whole SHEBANQ using
[pdoc3]({{pdoc3}}) is not possible, in contrast to Text-Fabric.

A second good point is that mkdocstrings is potentially capable of
doing Javascript as well.
At the moment, there is not yet a handler for Javascript, so this advantage
does not yet materialize.

But still ...

We extract the Javascript documentation using jsdoc(to markdown) and
dump it into our source docs folder.
From there it will be seen by mkdocs, and formatted with the other stuff.

And the excellent thing is the `autorefs` plugin of mkdocs, by which
we can easily cross-reference between all doc sources.

That means that we can put a reference to a Javascript class right in the docstring
of a Python class, *and vice versa*.
