"""Module with only private symbols -- no public API."""

_INTERNAL_FLAG = True
_counter = 0


def _setup():
    """Private setup function."""
    pass


def _teardown():
    """Private teardown function."""
    pass


class _InternalHelper:
    """Private class."""

    def _do_work(self):
        pass

    def __init__(self):
        pass
