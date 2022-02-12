"""Script to preview completion item documentation."""
import argparse
import json
import re

from rich.markdown import Markdown
from rich.panel import Panel
from textual.app import App
from textual.widget import Widget
from textual.widgets import Footer
from textual.widgets import Header
from textual.widgets import ScrollView


class ItemList(Widget):
    def __init__(self, items, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.items = items
        self.selected = -1

    def render(self) -> Panel:

        content = []
        for idx, item in enumerate(self.items):
            name = item[: item.index("(")]
            if idx == self.selected:
                content.append(f"[bold]{name}[/bold]")
            else:
                content.append(name)

        return Panel("\n".join(content))

    def select_next(self):
        self.selected += 1
        if self.selected >= len(self.items):
            self.selected = 0

        self.refresh()
        return self.items[self.selected]

    def select_previous(self):
        self.selected -= 1
        if self.selected < 0:
            self.selected = len(self.items) - 1

        self.refresh()
        return self.items[self.selected]


class DocViewer(App):
    """A simple app for viewing bundled CompletionItem documentation."""

    def __init__(self, filenames, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.filenames = filenames
        self.documentation = {}
        self.reload_files()

    def reload_files(self):
        docs = {}
        for file in self.filenames:
            with open(file) as f:
                docs.update(json.load(f))

        self.documentation = docs

    async def on_load(self):
        await self.bind("q", "quit", "Quit")
        await self.bind("n", "select_next", "Next")
        await self.bind("p", "select_previous", "Previous")
        await self.bind("r", "reload", "Reload")

    async def on_mount(self):
        """Constructs the UI."""
        await self.view.dock(Header(tall=False), edge="top")
        await self.view.dock(Footer(), edge="bottom")

        self.preview = ScrollView()
        self.items = ItemList(sorted(self.documentation.keys()))

        await self.view.dock(
            ScrollView(self.items), edge="left", size=48, name="sidebar"
        )
        await self.view.dock(self.preview, edge="top")
        await self.action_select_next()

    async def action_reload(self):
        self.reload_files()
        self.items.selected = -1
        self.items.items = sorted(self.documentation.keys())
        await self.action_select_next()

    async def action_select_next(self):
        key = self.items.select_next()
        await self.render_item(key)

    async def action_select_previous(self):
        key = self.items.select_previous()
        await self.render_item(key)

    async def render_item(self, key):
        doc = self.documentation[key]
        content = [
            re.match(r".+\((.+)\)", key).group(1),
            "",
            "----",
            "",
            *doc["description"],
        ]
        md = Markdown("\n".join(content))

        await self.preview.update(Panel(md))


cli = argparse.ArgumentParser(
    description="Preview the CompletionItem documentation we bundle with the language server."
)
cli.add_argument("files", nargs="+")

if __name__ == "__main__":
    args = cli.parse_args()
    DocViewer.run(title="Documentation Viewer", filenames=args.files)
