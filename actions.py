import sublime

import os

from .error       import Error
from .sinks       import SinkShowManager, PanelSink
from Default.exec import AsyncProcess, ProcessListener


SINK_SHOW_MAPPING = {
    True: SinkShowManager.ALWAYS_SHOW,
    False: SinkShowManager.NEVER_SHOW,
    "on_write": SinkShowManager.SHOW_ON_WRITE,
}

SINK_HIDE_MAPPING = {
    True: SinkShowManager.ALWAYS_HIDE,
    False: SinkShowManager.NEVER_HIDE,
    "if_empty": SinkShowManager.HIDE_IF_EMPTY,
}


class Action:
    def __init__(self, seq, window):
        self.seq = seq
        self.window = window

    def stop(self):
        pass


class SublimeCommandAction(Action):
    def run(self, *, command, args=None):
        self.window.active_view().run_command(command, args)
        self.seq.run_next()


class ExecAction(Action, ProcessListener):
    def run(self, *, cmd, sink=None, **kwargs):
        view = self.window.active_view()
        assert view
        if view.file_name() is None:
            self.seq.cancel()
            sublime.status_message("Cancelled")
            return

        cmd = sublime.expand_variables(cmd, self.window.extract_variables())
        if sink is not None:
            self.sink_manager = self._create_sink_manager(**sink)
        else:
            self.sink_manager = None

        try:
            os.chdir(os.path.dirname(view.file_name()))
        except OSError as e:
            print("{0.__class__.__name__}: {0}".format(e))
        self.aproc = AsyncProcess(cmd, None, { }, self, **kwargs)

    def _create_sink_manager(self, *, type, show=True, hide="if_empty", **kwargs):
        if type == "panel":
            sink = PanelSink(self.window, **kwargs)
        else:
            raise Error('Only "panel" sink type is supported for now.')

        try:
            behavoiur = SINK_SHOW_MAPPING[show]
        except KeyError:
            raise Error('sink.show must be true, false, or "on_write"')

        try:
            behavoiur |= SINK_HIDE_MAPPING[hide]
        except KeyError:
            raise Error('sink.hide must be true, false, or "if_empty"')

        return SinkShowManager(sink, behavoiur)


    def stop(self):
        self.aproc.kill()
        if self.sink_manager is not None:
            self.sink_manager.write("Aborted.")
            self.sink_manager.finish()

    def on_data(self, aproc, data):
        if self.sink_manager is not None:
            self.sink_manager.write(data.decode(errors="replace"))

    def on_finished(self, aproc):
        if self.sink_manager is not None:
            self.sink_manager.finish()
        if aproc.exit_code(): # May return None, so don't compare with 0.
            self.seq.cancel()
            sublime.status_message("Terminated")
        else:
            self.seq.run_next()
