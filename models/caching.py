from gluon import current


CACHING_ENABLED = True
CACHING_RAM_ONLY = True


class CACHING:
    """Handles all caching requests.

    !!! caution "other location"
        This module is not in the `modules` directory but in the `models` directory.
        In the module an instance of this class is created and added to
        [current]({{web2py}}) (a web2py concept),
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
            Whatever `func()` returnss

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
