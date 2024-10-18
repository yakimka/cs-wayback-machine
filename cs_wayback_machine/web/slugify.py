class Slugify:
    def __call__(self, text: str) -> str:
        return text.replace(" ", "_")

    def reverse(self, text: str) -> str:
        return text.replace("_", " ")


slugify = Slugify()
