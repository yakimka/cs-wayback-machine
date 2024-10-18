from urllib.parse import quote, unquote


class Slugify:
    def __call__(self, text: str) -> str:
        return quote(text.replace(" ", "_"), safe="/()")

    def reverse(self, text: str) -> str:
        return unquote(text.replace("_", " "))


slugify = Slugify()
