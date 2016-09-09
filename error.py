import functools


class Error(Exception):
    pass


def display_errors(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Error as e:
            sublime.error_message("Invoker: %s" % e)

    return wrapper
