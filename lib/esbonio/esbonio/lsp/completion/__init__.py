"""Completions."""


class CompletionHandler:
    def __call__(self, rst, match, line, doc):
        return self.suggest(rst, match, line, doc)
