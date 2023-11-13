# Bottlenecks

## The query-chapter index

The problem is that in order to present the list of queries that have results in a specific chapter,
an expensive SQL statement must be executed.

Our work around that is to maintain an index between queries and chapters.

That works, the sidebar generation is now crisp.

But there are disadvantages:

1.  it takes time to compute the index, roughly 30 seconds. It has to be done after every restart.
    This makes every update of the SHEBANQ code into a disturbance.
1.  the index is stored in the cache, the most global place there is.
    Still, it is local to the current process. So you cannot configure SHEBANQ with more than 1 process.
    So far, multiple threads compensate for that, but this limitation is not ideal.

Idea: store the index in the database as a simple cross-table between queries and chapters,
more precisely: queries, versions and chapters.

It will overcome both disadvantages.
In order to make it work, we need to update the cross table whenever query results change.

So we must make sure that saving query results and updating this table happens in one transaction.

Also, this will change the data model of the `shebanq_web` database.
That means that it will be difficult to restore older backups.
We can accommodate that by making new backups immediately.
