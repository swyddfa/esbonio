import argparse
import sys


def setup_cli(progname: str, description: str) -> argparse.ArgumentParser:
    """Return an argument parser with the default command line options required for
    main.

    In addition to any command line argumments you add, you should attach a function
    that takes the parsed arguments and returns a configured language server::

        cli = setup_cli("lsp-server", "my server's description")
        cli.set_defaults(configure=my_configure_function)
    """

    cli = argparse.ArgumentParser(prog=progname, description=description)
    cli.add_argument(
        "-p",
        "--port",
        type=int,
        default=None,
        help="start a TCP instance of the language server listening on the given port.",
    )
    cli.add_argument(
        "--version", action="store_true", help="print the current version and exit."
    )

    modules = cli.add_argument_group(
        "modules", "include/exclude language server modules."
    )
    modules.add_argument(
        "-i",
        "--include",
        metavar="MOD",
        action="append",
        default=[],
        dest="included_modules",
        help="include an additional module in the server configuration, can be given multiple times.",
    )
    modules.add_argument(
        "-e",
        "--exclude",
        metavar="MOD",
        action="append",
        default=[],
        dest="excluded_modules",
        help="exclude a module from the server configuration, can be given multiple times.",
    )

    return cli


def main(cli: argparse.ArgumentParser):
    """Standard main function for each of the default language servers."""

    # Put these here to avoid circular import issues.
    from esbonio.lsp import __version__
    from esbonio.lsp import create_language_server

    args = cli.parse_args()

    if args.version:
        print(f"v{__version__}")
        sys.exit(0)

    modules = list(args.modules)

    for mod in args.included_modules:
        modules.append(mod)

    for mod in args.excluded_modules:
        modules.remove(mod)

    server = create_language_server(args.server_cls, modules)

    if args.port:
        server.start_tcp("localhost", args.port)
    else:
        server.start_io()
