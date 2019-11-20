import sys
from typing import List, Tuple

from Orange.widgets import widget, gui, settings
from Orange.widgets.utils.signals import Output
from pylsl import StreamInfo, resolve_streams, StreamInlet


class OWLSLStream(widget.OWWidget):
    # widget definition
    name = "LSL Stream"
    description = "Read data and metadata streams from LSL"
    icon = "icons/Stream.svg"
    priority = 1

    # Available LSL streams
    streams: List[StreamInfo] = []
    stream_labels: List[Tuple[str, int]] = []

    # Selected LSL stream
    i: List[int] = settings.Setting([])

    class Outputs:
        output_stream = Output("Streams", StreamInlet)

    want_main_area = False

    def __init__(self):
        super().__init__()

        # GUI
        self.wb_control_area = gui.widgetBox(self.controlArea, minimumWidth=400)
        # Selected Stream
        self.wb_selected_stream = gui.widgetBox(self.wb_control_area, box="Selected Stream")
        self.wl_selected_stream = gui.widgetLabel(self.wb_selected_stream, '')
        # Stream Selection
        self.wb_selected_stream = gui.widgetBox(self.wb_control_area, box="Available Streams")
        self.lb_streams = gui.listBox(self.wb_selected_stream, self, labels='stream_labels', value='i', callback=self.on_stream_select)
        self.btn_ok = gui.button(self.buttonsArea, self, 'OK', callback=self.stream_selection_confirmed)

    def on_stream_select(self):
        # Update selected stream description
        if len(self.i) > 0:
            __s = self.streams[self.i[0]]
            self.wl_selected_stream.setText(self.stream_labels[self.i[0]][0])
        else:
            self.wl_selected_stream.setText('Please select a channel and click OK to confirm')

    def stream_selection_confirmed(self):
        if len(self.i) > 0:
            # Send stream as output
            __s = self.streams[self.i[0]]
            __output = StreamInlet(__s)

        else:
            # Send None as output
            __output = None
        self.Outputs.output_stream.send(__output)
        print('Sent: %s' % str(__output))
        self.close()

    @staticmethod
    def gen_stream_desc(x: StreamInfo):
        return "%s (%d-Ch %s) - %s Hz" % (x.name(), x.channel_count(), x.type(), x.nominal_srate())

    def fetch_lsl_streams(self):
        # Set loading labels
        self.wl_selected_stream.setText('None')
        # Fetch data
        self.streams = resolve_streams()
        self.stream_labels = list(map(lambda x: (self.gen_stream_desc(x), 3), self.streams))
        # Update labels
        s = 'Please select a channel and click OK to confirm' if len(self.streams) == 0 else self.stream_labels[0][0]
        self.wl_selected_stream.setText(s)

    def showEvent(self, event):
        super().showEvent(event)
        self.fetch_lsl_streams()


def main(argv=sys.argv):
    from AnyQt.QtWidgets import QApplication
    app = QApplication(list(argv))

    ow = OWLSLStream()
    ow.show()
    ow.raise_()
    ow.handleNewSignals()
    app.exec_()
    return 0


if __name__ == "__main__":
    sys.exit(main())
