CACHING_ENABLED = True
CACHING_RAM_ONLY = True


class CACHING:
    def __init__(self, cache):
        self.cache = cache

    def get(self, cacheKey, func, expire):
        cache = self.cache

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
        cache = self.cache

        if CACHING_ENABLED and cache is not None:
            cache.ram.clear(regex=cacheKeys)
            if not CACHING_RAM_ONLY:
                cache.disk.clear(regex=cacheKeys)
