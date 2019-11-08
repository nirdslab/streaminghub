import sys
from typing import List, Tuple

import Orange.data
import numpy
from Orange.widgets import widget, gui
from Orange.widgets.utils.signals import Output


class OWLSLStream(widget.OWWidget):
    name = "LSL Stream"
    description = "Read data and metadata from LSL streams"
    icon = "icons/Stream.svg"
    priority = 1
    streams: List[Tuple[str, int]] = []
    selection = []

    class Outputs:
        output_data = Output("Data", Orange.data.Table)
        output_metadata = Output("Metadata", Orange.data.Table)

    def connect_control(self, name, func):
        super().connect_control(name, func)

    want_main_area = False

    def __init__(self):
        super().__init__()

        # GUI
        box = gui.widgetBox(self.controlArea)
        self.selected_stream = gui.widgetLabel(box, "No stream selected, waiting for selection.")
        self.streams_list = gui.listBox(box, self, labels='streams', value='selection', callback=self.stream_selected)
        self.selected_stream_metadata = gui.widgetLabel(box, '')
        self.ok = gui.button(self.controlArea, self, 'OK')

    def stream_selected(self):
        print(self.selection[0])

    def set_data(self, dataset):
        if dataset is not None:
            self.selected_stream.setText("%d instances in input data set" % len(dataset))
            indices = numpy.random.permutation(len(dataset))
            indices = indices[:int(numpy.ceil(len(dataset) * 0.1))]
            sample = dataset[indices]
            self.streams = list((str(x) + '!', 0) for x in range(100))
            self.selected_stream_metadata.setText("%d sampled instances" % len(sample))
            self.Outputs.output_data.send(sample)
        else:
            self.selected_stream.setText(
                "No data on input yet, waiting to get something.")
            self.selected_stream_metadata.setText('')
            self.Outputs.output_data.send(None)


def main(argv=sys.argv):
    from AnyQt.QtWidgets import QApplication
    app = QApplication(list(argv))
    args = app.arguments()
    if len(args) > 1:
        filename = args[1]
    else:
        filename = "iris"

    ow = OWLSLStream()
    ow.show()
    ow.raise_()

    dataset = Orange.data.Table(filename)
    ow.set_data(dataset)
    ow.handleNewSignals()
    app.exec_()
    return 0


if __name__ == "__main__":
    sys.exit(main())
