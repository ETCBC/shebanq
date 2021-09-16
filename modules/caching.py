CACHING_ENABLED = True
CACHING_RAM_ONLY = True


class CACHING:
    def __init__(self, cache):
        self.cache = cache

    def get(self, ckey, func, expire):
        cache = self.cache

        if CACHING_ENABLED and cache is not None:
            if CACHING_RAM_ONLY:
                result = cache.ram(ckey, func, time_expire=expire)
            else:
                result = cache.ram(
                    ckey,
                    lambda: cache.disk(ckey, func, time_expire=expire),
                    time_expire=expire,
                )
        else:
            result = func()
        return result

    def clear(self, ckeys):
        cache = self.cache

        if CACHING_ENABLED and cache is not None:
            cache.ram.clear(regex=ckeys)
            if not CACHING_RAM_ONLY:
                cache.disk.clear(regex=ckeys)
