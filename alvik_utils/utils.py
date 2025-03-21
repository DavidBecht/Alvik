import sys
def is_micropython() -> bool:
    return sys.implementation.name == "micropython"