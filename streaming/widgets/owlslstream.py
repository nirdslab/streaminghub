import sys
from typing import List, Tuple

from Orange.widgets import widget, gui
from Orange.widgets.utils.signals import Output
from pylsl import StreamInfo, resolve_streams, StreamInlet


class OWLSLStream(widget.OWWidget):
    name = "LSL Stream"
    description = "Read data and metadata from LSL stream_labels"
    icon = "icons/Stream.svg"
    priority = 1
    # List of available LSL stream_labels
    streams: List[StreamInfo] = []
    stream_labels: List[Tuple[str, int]] = []
    # Selected LSL stream(s)
    i = []

    class Outputs:
        output_streams = Output("Streams", StreamInlet)

    def connect_control(self, name, func):
        super().connect_control(name, func)

    want_main_area = False

    def __init__(self):
        super().__init__()

        # GUI
        self.box = gui.widgetBox(self.controlArea, minimumWidth=350)
        self.streams_list_label = gui.widgetLabel(self.box, '')
        self.streams_list = gui.listBox(self.box, self, labels='stream_labels', value='i',
                                        callback=self.stream_selection_changed)
        self.selected_stream_label = gui.widgetLabel(self.box, '')
        self.ok = gui.button(self.buttonsArea, self, 'OK', callback=self.stream_selection_confirmed)

    def stream_selection_changed(self):
        # Update i text
        if len(self.i) > 0:
            __s = self.streams[self.i[0]]
            self.selected_stream_label.setText("Selection: %s" % self.gen_stream_desc(__s))
        else:
            self.selected_stream_label.setText('Please select a channel and click OK to confirm')

    def stream_selection_confirmed(self):
        if len(self.i) > 0:
            # Send stream as output
            __s = self.streams[self.i[0]]
            __output = StreamInlet(__s)

        else:
            # Send None as output
            __output = None
        self.Outputs.output_streams.send(__output)
        print('Sent: %s' % str(__output))

    @staticmethod
    def gen_stream_desc(x: StreamInfo):
        return "%s (%d-Ch %s) - %s Hz" % (x.name(), x.channel_count(), x.type(), x.nominal_srate())

    def fetch_lsl_streams(self):
        # Set loading labels
        self.streams_list_label.setText("Hang on while we load the available LSL stream_labels...")
        self.selected_stream_label.setText('')
        # Fetch data
        self.streams = resolve_streams()
        self.stream_labels = list(map(lambda x: (x, 3), map(self.gen_stream_desc, self.streams)))
        # Update labels
        if self.stream_labels is not None and len(self.stream_labels) > 0:
            # Update labels
            self.streams_list_label.setText("%d LSL stream(s) available. Please select one" % len(self.stream_labels))
            self.selected_stream_label.setText('Please select a channel and click OK to confirm')
        else:
            # Update labels
            self.streams_list_label.setText("No LSL stream_labels! Please ensure there's at least one LSL stream")
            self.selected_stream_label.setText('')


def main(argv=sys.argv):
    from AnyQt.QtWidgets import QApplication
    app = QApplication(list(argv))

    ow = OWLSLStream()
    ow.show()
    ow.raise_()

    ow.fetch_lsl_streams()
    ow.handleNewSignals()
    app.exec_()
    return 0


if __name__ == "__main__":
    sys.exit(main())
