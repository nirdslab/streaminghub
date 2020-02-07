import sys
from typing import List, Optional

import numpy as np
from Orange.data import Table, Domain, ContinuousVariable
from Orange.widgets import widget, gui
from Orange.widgets.utils.concurrent import ThreadExecutor
from Orange.widgets.utils.signals import Output
from PyQt5.QtCore import pyqtSlot, QThread, QObject, QTimer
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
        streams = Input("Streams", StreamInlet)

    # outputs
    class Outputs:
        data = Output("Data", Table)

    # ui
    want_main_area = False

    @Inputs.streams
    def set_streams(self, streams: List[StreamInlet]):
        self.streams = streams

    def __init__(self):
        super().__init__()
        self.wb_control_area = gui.widgetBox(
            widget=self.controlArea,
            minimumWidth=400
        )
        # variables
        self._task = None  # type: Optional[Task]
        self._executor = ThreadExecutor()
        self.streams = []  # type: List[StreamInlet]

    def handleNewSignals(self):
        self._update()

    @pyqtSlot(Table)
    def handleTable(self, value):
        assert self.thread() is QThread.currentThread()
        self.Outputs.data.send(value)

    def _update(self):
        if self._task is not None:
            # First make sure any pending tasks are cancelled.
            self.cancel()
        assert self._task is None

        if self.streams is None:
            return

        self._task = task = Task()
        task.begin(self.streams, self.Outputs.data)

    def onDeleteWidget(self):
        self.cancel()
        super().onDeleteWidget()

    def cancel(self):
        if self._task is not None:
            self._task.cancel()
            self._task = None


class Task(QObject):
    _timer = QTimer()  # type: QTimer
    _streams = ...  # type: List[StreamInlet]
    _out = ...  # type: Output
    _data = None

    def begin(self, streams: List[StreamInlet], out: Output):
        self._streams = streams
        self._out = out
        self._timer.timeout.connect(lambda: self._run(self._streams, self._out))
        self._timer.start(500)

    def _run(self, inlets: List[StreamInlet], out: Output):
        for inlet in inlets:
            samples, timestamps = inlet.pull_chunk()
            if len(timestamps) == 0:
                continue
            timestamps = np.expand_dims(np.array(timestamps), -1)
            samples = np.array(samples)
            chunk = np.concatenate((timestamps, samples), axis=-1)
            labels = ['t']
            if self._data is None:
                self._data = chunk
            else:
                self._data = np.concatenate((self._data, chunk), axis=0)[:1000]
            try:
                n = inlet.info().desc().child("channels").first_child()
                while n.child_value() != '':
                    labels.append(n.child_value())
                    n = n.next_sibling()
                table = Table.from_numpy(Domain([*map(ContinuousVariable, labels)]), self._data)
                out.send(table)
            except Exception as e:
                print(e)

    def cancel(self):
        self._timer.stop()


if __name__ == "__main__":
    from AnyQt.QtWidgets import QApplication

    app = QApplication(sys.argv)

    ow = OWTabulate()
    ow.show()
    ow.raise_()
    ow.handleNewSignals()
    app.exec_()
    sys.exit()
