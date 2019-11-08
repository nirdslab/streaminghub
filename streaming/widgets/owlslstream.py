from typing import List

import Orange.data
import numpy
from Orange.widgets import widget, gui
from Orange.widgets.utils.signals import Input, Output

# within-package imports
from streaming import Stream


class OWLSLStream(widget.OWWidget):
    name = "LSL Stream"
    description = "Read data and metadata from LSL streams"
    icon = "icons/Stream.svg"
    priority = 1

    class Inputs:
        input_streams = Input("Stream", List[Stream])

    class Outputs:
        output_data = Output("Data", Orange.data.Table)
        # output_metadata = Output("Metadata", Orange.data.Table)

    want_main_area = False

    def __init__(self):
        super().__init__()

        # GUI
        box = gui.widgetBox(self.controlArea, "Streams")
        # self.streams_list = gui.listBox(box, self, labels="input_streams")
        self.selected_stream = gui.widgetLabel(box, "No stream selected, waiting for selection.")
        self.selected_stream_metadata = gui.widgetLabel(box, '')

    @Inputs.input_streams
    def set_data(self, dataset):
        if dataset is not None:
            self.selected_stream.setText("%d instances in input data set" % len(dataset))
            indices = numpy.random.permutation(len(dataset))
            indices = indices[:int(numpy.ceil(len(dataset) * 0.1))]
            sample = dataset[indices]
            self.selected_stream_metadata.setText("%d sampled instances" % len(sample))
            self.Outputs.output_data.send(sample)
        else:
            self.selected_stream.setText(
                "No data on input yet, waiting to get something.")
            self.selected_stream_metadata.setText('')
            self.Outputs.output_data.send(None)
