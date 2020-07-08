import sys
import threading

import numpy as np
from Orange.data import Table
from Orange.widgets import widget
from PyQt5.QtCore import pyqtSlot
from orangewidget.utils.signals import Input, Output
from streaming.widgets.fixation_detector import FixationDetector


class FixationsWidget(widget.OWWidget):
    """
    Calculate real-time fixations using gaze coordinate data
    """
    name = "Fixations"
    description = "Calculate fixations from gaze data stream"
    icon = "icons/Tabulate.svg"
    priority = 2

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # variables
        self.lock = threading.Lock()
        # ui
        self.want_main_area = False
        self.want_control_area = False
        self.want_basic_layout = False
        self.want_message_bar = False

    class Inputs:
        """
        Inputs
        """
        gaze_data = Input("Gaze Data", Table)

    class Outputs:
        """
        Outputs
        """
        fixation_data = Output("Fixation Data", Table)

    @Inputs.gaze_data
    def set_gaze_data(self, values: Table):
        variable_cols = ['t', *map(str, list(values.domain.variables)[1:])]
        gaze_x: np.array = ...
        gaze_y: np.array = ...
        found = 0
        t = np.array(values.X[:, 0])
        if 'gaze.0_x' in variable_cols and 'gaze.0_y' in variable_cols:
            gaze_x = np.array(values.X[:, variable_cols.index('gaze.0_x')]) + (gaze_x if found > 0 else 0)
            gaze_y = np.array(values.X[:, variable_cols.index('gaze.0_y')]) + (gaze_y if found > 0 else 0)
            found += 1
        if 'gaze.1_x' in variable_cols and 'gaze.1_y' in variable_cols:
            gaze_x = np.array(values.X[:, variable_cols.index('gaze.1_x')]) + (gaze_x if found > 0 else 0)
            gaze_y = np.array(values.X[:, variable_cols.index('gaze.1_y')]) + (gaze_y if found > 0 else 0)
        if found > 0:
            gaze_x /= found
            gaze_y /= found
            eqn = FixationDetector(job=[t, gaze_x, gaze_y], parent=self)
            eqn.output.connect(self.send_output)
            eqn.start()

    @pyqtSlot(Table)
    def send_output(self, output: Table):
        self.Outputs.fixation_data.send(output)


if __name__ == "__main__":
    from AnyQt.QtWidgets import QApplication

    app = QApplication(sys.argv)

    ow = FixationsWidget()
    ow.show()
    ow.raise_()
    ow.handleNewSignals()
    app.exec_()
    sys.exit()
