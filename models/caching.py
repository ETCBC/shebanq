from gluon import current


CACHING_ENABLED = True

"""Whether we should also cache on disk

!!! caution "Do not cache on disk"
    Two problems: some of the cached objects cannot be pickled:
    [M viewdefs.Make][viewdefs.Make.setupValidation] caches
    validation *functions*.
    We could work around this.

    But:

    It causes deadlock. In order to write to the cache file,
    the file must be locked, but the process somehow never allows
    the lock to be obtained.

"""
CACHING_RAM_ONLY = True


class CACHING:
    """Handles all caching requests.

    !!! caution "The cache is used for global data structures"
        In Web2py the cache is global to the threads, but local to the process.
        Since we use the cache to maintain a live index between queries and chapters,
        the index in one process might get out of touch with the situation
        in another process. For example if a query is run and different or new
        results are obtained. It will trigger an update of certain cache values,
        but other processes do not see that.

        So configure a SHEBANQ server to use 1 process and multiple threads.

    !!! caution "other location"
        This module is not in the `modules` directory but in the `models` directory.
        In the module an instance of this class is created and added to
        [current]({{web2py}}) (a Web2py concept),
        which means that the object is available for each request.
    """

    def __init__(self):
        pass

    def get(self, cacheKey, func, expire):
        """Get the value of function `func` from the cache.

        When called, it is first determined of the cache contains a value
        for the key `cacheKey`. If so, this value is returned.
        If not, `func` is called with zero arguments, and the result is
        stored in the cache under key `cacheKey`.
        Then the result is returned.

        If the expiration time is not None, the result stays in the cache
        for that many seconds.

        Parameters
        ----------
        func: function
            a function with zero arguments.
        cacheKey: string
            a string which is used to lookup the value of `func()` by.
        expire: integer
            time in seconds after which the stored result expires.
            If `None`, the result stays in the cache permanently.

        Returns
        -------
        data
            Whatever `func()` returns

        """
        cache = current.cache

        if CACHING_ENABLED and cache is not None:
            if CACHING_RAM_ONLY:
                result = cache.ram(cacheKey, func, time_expire=expire)
            else:
                result = cache.ram(
                    cacheKey,
                    lambda: cache.disk(cacheKey, func, time_expire=expire),
                    time_expire=expire,
                )
        else:
            result = func()
        return result

    def clear(self, cacheKeys):
        cache = current.cache

        if CACHING_ENABLED and cache is not None:
            cache.ram.clear(regex=cacheKeys)
            if not CACHING_RAM_ONLY:
                cache.disk.clear(regex=cacheKeys)


current.Caching = CACHING()
