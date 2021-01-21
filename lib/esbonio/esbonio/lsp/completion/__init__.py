"""Completions."""


class CompletionHandler:
    """Base class for completion handlers."""

    def __call__(self, rst, match, line, doc):
        return self.suggest(rst, match, line, doc)

    def suggest(self, rst, match, line, doc):
        raise NotImplementedError("suggest")
