import os

import sys

# One method to compose them all, one method to hash them
if '__main__' == __name__:
    sys.path.append(os.path.dirname(sys.path[0]))
    from src.parsing.parser import parse_data

    parse_data(print)
