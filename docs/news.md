# News

2023-07-?? Upcoming

*   Deployment via a docker container on KNAW/HuC infrastructure (CLARIAH)

2022-05-09 Small fix

*   In the query tree, it was not possible to view and edit details of projects 
    and organizations, due to a glitch in the Javascript code. That has been fixed.

2022-01-20 Small fixes

*   The user agent is not needed anywhere in the SHEBANQ code anymore.
    `request.user_agent.browser.name` sometimes led to a key error `name`.
*   The REST-API did not work because argument passing was wrong with `getJson` in
    `modules/verse.py`
*   Regenerated the valence note set for version `c`

2021-10-20 Big update.

*   New ETCBC data version 2021
*   Migration to Python3
*   New versions of Emdros and Web2py and MySQL
*   Completely refactored code base: all Python, Javascript and CSS code
    chopped up in manageable chunks.
*   Install and maintenance scripts
*   Mkdocs framework for technical documentation
*   Maintenance documentation written
*   Shebanq software documentation just started

See also [older news](https://github.com/ETCBC/shebanq/wiki/Changes)


