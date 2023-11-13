# Installation and maintenance

## Motivation

**The promise of SHEBANQ to its users is that the queries and notes
they have saved on SHEBANQ will be accessible by a fixed URL
for the indefinite future.**

Therefore it is vitally important to backup this data and store
those backups in a variety of places,
not only on the server that hosts SHEBANQ,
however well that server is being managed.

The following tasks must be addressed:

*   **Server migration**

    Servers do not have eternal life,
    so every now and then SHEBANQ has to migrate
    from one server to another.

*   **'Foreign' servers**

    We encourage people to host their own SHEBANQ,
    so we must support new installations on third party servers.
    Those servers must be equally maintainable as
    the official servers.

*   **Software updates**

    In order to keep SHEBANQ alive over the years,
    software updates must be carried out,
    not only of the web app,
    but also of its supporting systems,
    [Emdros](https://emdros.org),
    [Web2py](http://web2py.com),
    [Python](https://www.python.org),
    and
    [MariaDB](https://mariadb.org)
    (a replacement of
    [MySQL](https://dev.mysql.com/downloads/mysql/)
    ).

* **Data updates**

    The [ETCBC](http://www.etcbc.nl), as the provider of the
    textual and linguistic data of the Hebrew Bible,
    produces data updates through its
    [BHSA](https://github.com/etcbc/bhsa) repository.
    These data updates must be applied to the
    servers that host SHEBANQ.


There are some additional requirements which are vital for 
the long-term support of SHEBANQ.

*   **Security**

    SHEBANQ servers should be secure.
    They must be hardened against attacks,
    and the user data must be kept safe,
    even if only the bare minimum
    of personal data is stored
    (names, email addresses, password hashes).

*   **Automation**

    Maintaining a server requires countless nitty-gritty
    steps, which are easily forgotten.
    That is the prime reason to automate all these steps.
    People that are new to SHEBANQ should be able to
    maintain SHEBANQ in a straightforward way.

*   **Documentation**

    The maintenance of SHEBANQ should be well
    [documented](documentation.md).
    Together with automation it is the best help we can offer
    to the maintainers of SHEBANQ in the years to come.

*   **Testing**

    Whenever parts of the SHEBANQ code base are changed,
    it is immensely helpful to run a battery of tests
    as an indication that nothing has been broken by the
    changes.
    This is in an early stage of development.
    We have set up the framework and implemented a couple of tests,
    just to show the mechanism.
    The test themselves are also documented.
    See (testing)[../tests/index.md] 

## Operation

SHEBANQ has a build script by which you can take care of
a few standard maintenance tasks:

*  documentation building and publishing
*  committing changes to GitHub


Just do 

```
cd ~/github/etcbc/shebanq
python3 build.py --help
```

to look at the options, or inspect the
[source code]({{repo}}/blob/master/build.py).

!!! hint "Shell function"
    Write a shell function and put it into your `.zshrc` or `bashrc` like this

    ```
    function shb {
        cd ~/github/etcbc/shebanq
        python3 build.py "$@"
    }
    ```

    now you can run `shb` (i.e. shebanq-build) from any directory.
