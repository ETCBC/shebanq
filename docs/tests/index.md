# Tests

We use *functional testing* to test SHEBANQ.

We do not have set up unit testing (yet).
A good candidate for unit testing would be the python files
in the *modules* directory, because nearly all the business
logic on the server is located there.
The *controllers* are very lean, and delegate all their work
to them.

However, such unit-testing leaves out many things that are needed
for a proper working SHEBANQ:

*   database layer
*   views
*   translation from URL to functions as defined by the framework
*   mechanics of the browser
*   javascript code

A few of these could be covered by *integration tests*, but
if we really want to test the proper functioning of the website,
we need *functional* tests.

SHEBANQ has been working well from 2013 till 2021, but the
update in autumn 2021 involves a massive refactoring.

So far, we did not use any testing framework.
Still, at the module level, everything seems to work well,
even after the refactoring.
We have observed that by intensely visiting the website and verifying
that every interaction with it works as expected.

The biggest gains lie in the automation of visiting the website,
and this is exactly *functional* testing.

There is a framework for that, [Selenium]({{selenium}}),
which works with the concept of a *browser driver*.
It has a Python interface, and it can work with Safari
out of the box, without installing something extra.

In order to organize a massive amount of tests, we use the
popular test framework [PyTest]({{pytest}}))

There is documentation on individual tests, see
[individual test scripts](bymodule/index.md).

If you have followed the hint in [operation][]
you can run tests by

```
shb test arguments
```

which will resolve to

```
cd ~/github/etcbc/shebanq
python3 build.py tests arguments
```

This will in turn resolve to

```
cd ~/github/etcbc/shebanq
pytest ftests arguments
```

where arguments are options to feed to `pytest`
(do `pytest --help` to see which options you've got).
