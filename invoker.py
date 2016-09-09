import sublime
import sublime_plugin

import threading

from .actions import SublimeCommandAction, ExecAction
from .error   import display_errors, Error


current_sequence = None
lock = threading.RLock()


# Helper commands.
class ClearCommand(sublime_plugin.TextCommand):
    """
    Deletes everything in the view.
    """

    def run(self, edit):
        self.view.erase(edit, sublime.Region(0, self.view.size()))


class SaveIfDirtyCommand(sublime_plugin.TextCommand):
    """
    Saves the view iff it contains unsaved changes.
    """

    def is_enabled(self):
        return self.view.is_dirty()

    def run(self, edit):
        self.view.run_command("save")


class InvokerCommand(sublime_plugin.WindowCommand):
    @display_errors
    def run(self, **kwargs):
        with lock:
            global current_sequence
            if current_sequence is None:
                actions = kwargs.get("actions", None)
                if actions is None:
                    actions = [kwargs]
                current_sequence = Sequence(self.window, actions)
                sublime.status_message("Started")
                current_sequence.run_next()
            else:
                sublime.status_message("Already running")


class InvokerStopCommand(sublime_plugin.WindowCommand):
    @display_errors
    def run(self):
        with lock:
            if current_sequence is not None:
                current_sequence.abort()
                sublime.status_message("Aborted")
            else:
                sublime.status_message("Nothing to stop")


class InvokerEventListener(sublime_plugin.EventListener):
    def on_query_context(self, view, key, operator, operand, match_all):
        if key == "invoker_running":
            if operator in (sublime.OP_EQUAL, sublime.OP_NOT_EQUAL):
                with lock:
                    result = current_sequence is not None
                return (result == operand) == (operator == sublime.OP_EQUAL)

            sublime.status_message(
                '"invoker_running" context supports only "equal" and "not_equal" operators!')
            return False


class Sequence:
    def __init__(self, window, actions):
        self.window = window
        self.actions = actions
        self.i = -1
        self.cur = None

    @display_errors
    def run_next(self):
        self.i += 1
        if self.i < len(self.actions):
            self._dispatch_action(**self.actions[self.i])
        else:
            self.cur = None
            self.cancel()
            sublime.status_message("Finished")

    def _dispatch_action(self, *, type, **kwargs):
        if type == "sublime":
            cls = SublimeCommandAction
        elif type == "exec":
            cls = ExecAction
        else:
            raise Error('type must be either "sublime" or "exec"')

        self.cur = cls(self, self.window)
        self.cur.run(**kwargs)

    def abort(self):
        if self.cur is not None:
            self.cur.stop()
            self.cur = None

        self.cancel()

    def cancel(self):
        global current_sequence
        current_sequence = None
