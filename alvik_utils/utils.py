import sys
def is_micropython() -> bool:
    return sys.implementation.name == "micropython"

def get_error_message(exception: Exception) -> str:
    try:
        import traceback
        return traceback.format_exc()
    except ImportError:
        import sys
        import io
        buf = io.StringIO()
        sys.print_exception(exception, buf)
        return buf.getvalue()