"""Whole-process single-instance guard for the desktop wrapper.

Two separate OS processes of the app (e.g. a stale copy left running from a
previous launch, or a second launch of a duplicate install) can otherwise run
at once, and if one of them is mid self-update while the other is still
alive, the relaunch after the install swap can collide with the still-live
sibling and die before it ever shows a window (dock icon bounces forever,
nothing logged). Acquiring this lock before the GUI/webview starts and
holding it for the life of the process means a second instance exits
immediately, before it can race an update or open a conflicting window.
"""
import sys

from maven.desktop.paths import get_data_dir

LOCK_FILENAME = "app.lock"

# Keeps the lock file's descriptor alive for the life of the process -- the
# OS releases the lock as soon as every fd referencing it closes, so this
# must not be garbage-collected while still "holding" the lock. That same
# auto-release-on-close behavior is also what makes this work across
# os._exit(0) (the path the self-update install takes) with no explicit
# release() needed.
_lock_file = None


def acquire_singleton_lock():
    """Returns True if this process is the only one running, having taken an
    exclusive, non-blocking lock on a file shared across every copy/version
    of the app for the current user. Returns False if another instance
    already holds it."""
    global _lock_file
    lock_path = get_data_dir() / LOCK_FILENAME
    lock_file = open(lock_path, "a")

    try:
        if sys.platform == "win32":
            import msvcrt

            msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        lock_file.close()
        return False

    _lock_file = lock_file
    return True
