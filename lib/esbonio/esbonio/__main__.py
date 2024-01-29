"""Default startup module, identical to calling ``python -m esbonio.server``"""

import sys

from esbonio.server.cli import main

if __name__ == "__main__":
    sys.exit(main())
