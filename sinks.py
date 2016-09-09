class SinkShowManager:
    NEVER_SHOW    = 0x0
    ALWAYS_SHOW   = 0x1
    SHOW_ON_WRITE = 0x2
    NEVER_HIDE    = 0x0
    ALWAYS_HIDE   = 0x4
    HIDE_IF_EMPTY = 0x8

    def __init__(self, sink, behavoiur):
        self.sink = sink
        self.empty = True
        self.behavoiur = behavoiur
        if behavoiur & self.ALWAYS_SHOW:
            sink.show()

    def write(self, text):
        if self.behavoiur & self.SHOW_ON_WRITE:
            self.sink.show()
            self.behavoiur ^= self.SHOW_ON_WRITE

        if text:
            self.sink.write(text)
            self.empty = False

    def finish(self):
        if self.behavoiur & self.ALWAYS_HIDE or self.empty and self.behavoiur & self.HIDE_IF_EMPTY:
            self.sink.hide()


class PanelSink:
    def __init__(self, window, name, **kwargs):
        self.window = window
        self.name = "output." + name
        self.endl = False

        self.panel = window.find_output_panel(name)
        if self.panel is None:
            self.panel = window.create_output_panel(name)
        else:
            self.panel.set_read_only(False)
            self.panel.run_command("clear")

        self.panel.set_read_only(True)
        settings = self.panel.settings()
        for key, value in kwargs.items():
            settings.set(key, value)

    def write(self, text):
        text = text.replace("\r\n", '\n')
        if self.endl:
            text = '\n' + text
        if text.endswith('\n'):
            text = text[:-1]
            self.endl = True
        else:
            self.endl = False
        self.panel.run_command("append", args={
            "characters": text,
            "force": True,
            "scroll_to_end": True,
        })

    def show(self):
        self.window.run_command("show_panel", args={ "panel": self.name })

    def hide(self):
        self.window.run_command("hide_panel", args={ "panel": self.name })


# TODO: ViewSink.
