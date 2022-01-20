# News

2022-01-20 Small fixes

*   The user agent is not needed anywhere in the SHEBANQ code anymore. `request.user_agent.browser.name` sometimes led to a key error `name`.
*   Rest-PI did not work bacause argument passing was wrong with `getJson` in `modules/verse.py`
*   Regenerated the valence noteset for version `c`

2021-10-20 Big update.

*   New ETCBC dataversion 2021
*   Migration to Python3
*   New versions of Emdros and Web2py and MySQL
*   Completely refactored codebase: all Python, Javascript and CSS code
    chopped up in managable chunks.
*   Install and maintenance scripts
*   Mkdocs framework for technical documentation
*   Maintenance documentation written
*   Shebanq software documentation just started

See also [older news](https://github.com/ETCBC/shebanq/wiki/Changes)


