"""Startup module that launches the real server in a sub process and dumps all comms
to a file."""
import sys
from argparse import Namespace

from lsp_devtools.cmds.record import record


def main():
    args = Namespace(file="lsp.log", format="%(message)s", raw=True)
    cmd = [sys.executable, "-m", "esbonio.lsp.sphinx"] + sys.argv[1:]

    record(args, cmd)


if __name__ == "__main__":
    main()
