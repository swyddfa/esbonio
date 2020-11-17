import argparse
import logging
import esbonio.lsp as lsp

cli = argparse.ArgumentParser(prog="esbonio", description="Your one true lsp.")

logging.basicConfig(
    level=logging.DEBUG,
    format="[%(levelname)s][%(name)s]: %(message)s",
    filemode="w",
    filename="/home/alex/Projects/esbonio/lib/esbonio/lsp.log",
)

lsp.server.start_io()
