import sys
from concurrent.futures.thread import ThreadPoolExecutor
from time import sleep
from typing import List

from Orange.data import Table
from Orange.widgets import widget, gui
from Orange.widgets.utils.signals import Output
from orangewidget.settings import Setting
from orangewidget.utils.signals import Input
from pylsl import StreamInlet

SELECT_STREAM_MSG = 'None Selected'
LOADING_MSG = 'Loading...'


class OWTabulate(widget.OWWidget):
    # widget definition
    name = "Tabulate"
    description = "Convert LSL stream into table form"
    icon = "icons/Tabulate.svg"
    priority = 2

    # inputs
    class Inputs:
        data = Input("Streams", StreamInlet)

    # outputs
    class Outputs:
        data = Output("Table", Table, dynamic=True)

    # Variables
    inlets: List[StreamInlet] = []
    executor = ThreadPoolExecutor(4)
    buffer_size: int = Setting(100)
    sleep_secs: float = Setting(0.5)
    want_main_area = False

    @Inputs.data
    def set_inlets(self, data: List[StreamInlet]):
        for inlet in data:
            self.executor.submit(self.listen_to_inlet, inlet)

    def listen_to_inlet(self, inlet):
        while True:
            samples, timestamps = inlet.pull_chunk()
            for sample, timestamp in zip(samples, timestamps):
                print([sample, timestamp])
            sleep(self.sleep_secs)

    def __init__(self):
        super().__init__()
        self.wb_control_area = gui.widgetBox(
            widget=self.controlArea,
            minimumWidth=400
        )


if __name__ == "__main__":
    from AnyQt.QtWidgets import QApplication

    app = QApplication(sys.argv)

    ow = OWTabulate()
    ow.show()
    ow.raise_()
    ow.handleNewSignals()
    app.exec_()
    sys.exit()
