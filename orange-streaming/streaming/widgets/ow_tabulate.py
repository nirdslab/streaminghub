import sys
import typing
from typing import List, Optional, Dict, Callable

import numpy as np
import pandas as pd
from Orange.data import Table, Domain, ContinuousVariable, TimeVariable
from Orange.widgets import widget, gui
from Orange.widgets.utils.signals import Output
from PyQt5.QtCore import pyqtSlot, QThread, QObject, QTimerEvent
from orangewidget.utils.signals import Input
from pylsl import StreamInlet, XMLElement

SELECT_STREAM_MSG = 'None Selected'
LOADING_MSG = 'Loading...'


class TabulateWidget(widget.OWWidget):
    """
    Widget to convert data and metadata from StreamInlet class (LSL) into Table class (Orange)
    """
    name = "Tabulate"
    description = "Convert LSL stream into table form"
    icon = "icons/Tabulate.svg"
    priority = 2

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # variables
        self.task = None  # type: Optional[Task]
        self.streams = []  # type: List[StreamInlet]
        # ui
        self.want_main_area = False
        self.wb_control_area = gui.widgetBox(
            widget=self.controlArea,
            minimumWidth=400
        )

    class Inputs:
        """
        Inputs
        """
        streams = Input("Streams", StreamInlet)

    class Outputs:
        """
        Outputs
        """
        data = Output("Data", Table)

    @Inputs.streams
    def set_streams(self, streams: List[StreamInlet]):
        self.streams = streams

    def handleNewSignals(self):
        # First make sure any pending tasks are cancelled.
        self.cancel_running_tasks()
        if self.streams is not None:
            self.task = Task(streams=self.streams, callback=self.handleTable, buffer_size=1000, parent=self)
            self.task.begin(interval=5000)

    @pyqtSlot(Table)
    def handleTable(self, value: Table):
        assert self.thread() is QThread.currentThread()
        self.Outputs.data.send(value)

    def onDeleteWidget(self):
        self.cancel()
        super().onDeleteWidget()

    def cancel_running_tasks(self):
        if self.task is not None:
            self.task.cancel()
            self.task = None
        assert self.task is None

    def cancel(self):
        self.cancel_running_tasks()


class Task(QObject):
    streams = ...  # type: List[StreamInlet]
    callback = ...  # type: Callable[[Table], None]
    buffer_size = ...  # type: int
    timer_id = ...  # type: int
    df = ...  # type: pd.DataFrame
    ch_map = ...  # type: Dict[str, List[str]]

    def __init__(self,
                 streams: List[StreamInlet],
                 callback: Callable[[Table], None],
                 buffer_size: int,
                 parent: typing.Optional['QObject'] = ...) -> None:
        super().__init__(parent)
        self.streams = streams
        self.callback = callback
        self.buffer_size = buffer_size
        self.init_ch_map()

    def init_ch_map(self):
        self.ch_map = {}
        for inlet in self.streams:
            info = inlet.info()
            ch_labels = []
            ptr: XMLElement = info.desc()
            key = f'{info.name()} {info.type()}'
            if not ptr.empty():
                ptr = ptr.child("channels")
                if not ptr.empty():
                    ptr = ptr.first_child()
                    while not ptr.empty():
                        ch_labels.append(ptr.child_value())
                        ptr = ptr.next_sibling()
            self.ch_map[key] = ch_labels

    def begin(self, interval: int):
        cols = [c for cs in self.ch_map.values() for c in cs]
        self.df = pd.DataFrame(columns=cols, index=pd.Index([], name='t'))
        self.timer_id = self.startTimer(interval)

    def timerEvent(self, a0: QTimerEvent) -> None:
        if a0.timerId() == self.timer_id:
            a0.accept()
            self._run()

    def _run(self):
        df = self.df
        updated = False
        # collect data into df
        for inlet in self.streams:
            # pull samples
            samples, timestamps = inlet.pull_chunk()
            if len(timestamps) == 0:
                continue
            # merge samples to data frame
            info = inlet.info()
            key = f'{info.name()} {info.type()}'
            labels = self.ch_map[key]
            samples = np.array(samples).reshape((-1, len(labels)))
            chunk = pd.DataFrame(index=pd.Index(timestamps, name='t'), data=samples, columns=labels)
            # generate updated chunk of data
            df = chunk.reindex(index=df.index.union(chunk.index).sort_values(), columns=df.columns).fillna(df)
            updated = True
        # retain only the last ${buffer_size} rows
        self.df = df.iloc[-self.buffer_size:]
        # emit the aggregate data
        if updated:
            # create table from self._data (include index as well)
            table_data = np.concatenate([self.df.index.to_numpy().reshape((-1, 1)), self.df.to_numpy()], axis=-1)
            table = Table.from_numpy(Domain([TimeVariable(self.df.index.name), *map(ContinuousVariable, self.df.columns)]), table_data)
            # trigger callback
            self.callback(table)

    def cancel(self):
        self.killTimer(0)


if __name__ == "__main__":
    from AnyQt.QtWidgets import QApplication

    app = QApplication(sys.argv)

    ow = TabulateWidget()
    ow.show()
    ow.raise_()
    ow.handleNewSignals()
    app.exec_()
    sys.exit()
