import sys
from typing import List, Optional

import numpy as np
import pandas as pd
from Orange.data import Table, Domain, ContinuousVariable
from Orange.widgets import widget, gui
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
    _data = None  # type: pd.DataFrame

    def begin(self, streams: List[StreamInlet], out: Output):
        self._streams = streams
        self._out = out
        self._timer.timeout.connect(lambda: self._run(self._streams, self._out))
        self._timer.start(1000)

    def _run(self, inlets: List[StreamInlet], out: Output):

        def get_ch_labels(_inlet: StreamInlet):
            _labels = []
            _ch = _inlet.info().desc()
            if not _ch.empty():
                _ch = _ch.child("channels")
                if not _ch.empty():
                    _ch = _ch.first_child()
                    while not _ch.empty():
                        _labels.append(_ch.child_value())
                        _ch = _ch.next_sibling()
                    return _labels
            return _labels

        def create_schema(_inlets: List[StreamInlet]):
            _labels = []
            for _inlet in _inlets:
                for _label in get_ch_labels(_inlet):
                    _labels.append(_label)
            return pd.DataFrame(columns=_labels, index=pd.Index([], name='t'))

        # create table schema first
        if self._data is None:
            self._data = create_schema(inlets)

        updated = False

        for inlet in inlets:
            samples, timestamps = inlet.pull_chunk()
            labels = get_ch_labels(inlet)
            if len(timestamps) == 0:
                continue
            samples = np.array(samples).reshape((-1, len(labels)))
            chunk = pd.DataFrame(index=pd.Index(timestamps, name='t'), data=samples, columns=labels)
            # self._data.update(chunk)
            self._data = self._data.fillna(chunk).append(chunk[~chunk.index.isin(self._data.index)], sort=True)
            updated = True

        if updated:
            # emit the aggregate data
            try:
                self._data = self._data.iloc[:1000]
                # create table from self._data (include index as well)
                table_data = np.concatenate([self._data.index.to_numpy().reshape((-1, 1)), self._data.to_numpy()], axis=-1)
                table = Table.from_numpy(Domain([*map(ContinuousVariable, [self._data.index.name, *self._data.columns])]), table_data)
                # send table
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
