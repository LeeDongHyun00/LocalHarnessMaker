from collections.abc import Iterable
class Catalog:
    def __init__(self, catalogs: dict[str,dict[str,str]], fallbacks: dict[str,list[str]]) -> None:
        self.catalogs = catalogs
        self.fallbacks = fallbacks
    def candidates(self, locale: str) -> tuple[str,...]:
        return tuple([locale] + self.fallbacks.get(locale, []))
    def lookup(self, locale: str, key: str) -> tuple[str,str]:
        for source in [locale] + self.fallbacks.get(locale, []):
            value = self.catalogs.get(source, {}).get(key)
            if value: return value, source
        raise KeyError(key)
    def lookup_many(self, locale: str, keys: Iterable[str]) -> list[tuple[str,str]]:
        return [self.lookup(locale,key) for key in keys]
