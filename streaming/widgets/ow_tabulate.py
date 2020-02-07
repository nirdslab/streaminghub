import concurrent.futures
import sys
from time import sleep
from typing import List, Optional

import numpy as np
from Orange.data import Table, Domain, ContinuousVariable
from Orange.widgets import widget, gui
from Orange.widgets.utils.concurrent import FutureWatcher, ThreadExecutor
from Orange.widgets.utils.signals import Output
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

    def _update(self):
        if self._task is not None:
            # First make sure any pending tasks are cancelled.
            self.cancel()
        assert self._task is None

        if self.streams is None:
            return

        self._task = task = Task()
        task.future = self._executor.submit(task.run, self.streams, 0.5, self.Outputs.data)

    def onDeleteWidget(self):
        self.cancel()
        super().onDeleteWidget()

    def cancel(self):
        """
        Cancel the current task (if any).
        """
        if self._task is not None:
            self._task.cancel()
            assert self._task.future.done()
            # disconnect the `_task_finished` slot
            # if self._task.watcher is not None:
            #     self._task.watcher.done.disconnect(self._task_finished)
            self._task = None


class Task:
    """
    A class that will hold the state for an learner evaluation.
    """

    #: A concurrent.futures.Future with our (eventual) results.
    #: The OWLearningCurveC class must fill this field
    future = ...  # type: concurrent.futures.Future

    #: FutureWatcher. Likewise this will be filled by OWLearningCurveC
    watcher = ...  # type: FutureWatcher

    #: True if this evaluation has been cancelled. The OWLearningCurveC
    #: will setup the task execution environment in such a way that this
    #: field will be checked periodically in the worker thread and cancel
    #: the computation if so required. In a sense this is the only
    #: communication channel in the direction from the OWLearningCurve to the
    #: worker thread
    cancelled = False  # type: bool

    def run(self, inlets: List[StreamInlet], sleep_time: float, out: Output):
        while not self.cancelled:
            for inlet in inlets:
                samples, timestamps = inlet.pull_chunk()
                if len(timestamps) == 0:
                    continue
                timestamps = np.expand_dims(np.array(timestamps), -1)
                samples = np.array(samples)
                data = np.concatenate((timestamps, samples), axis=-1)
                try:
                    table = Table.from_numpy(Domain([*map(ContinuousVariable, ['timestamp', 'x', 'y', 'z'])]), data)
                    out.send(table)
                except Exception as e:
                    print(e)
            sleep(sleep_time)

    def cancel(self):
        """
        Cancel the task.

        Set the `cancelled` field to True and block until the future is done.
        """
        # set cancelled state
        self.cancelled = True
        # cancel the future. Note this succeeds only if the execution has
        # not yet started (see `concurrent.futures.Future.cancel`) ..
        self.future.cancel()
        # ... and wait until computation finishes
        concurrent.futures.wait([self.future])


if __name__ == "__main__":
    from AnyQt.QtWidgets import QApplication

    app = QApplication(sys.argv)

    ow = OWTabulate()
    ow.show()
    ow.raise_()
    ow.handleNewSignals()
    app.exec_()
    sys.exit()
