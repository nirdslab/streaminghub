import sys
import threading
import time
from typing import List

from Orange.data import Table
from Orange.widgets import widget
from orangewidget.utils.signals import Input, Output


class MonitorWidget(widget.OWWidget):
    """
    Monitor resource utilization and calculate heuristics for a particular transformation
    """
    name = "Monitor"
    description = "Monitor resource usage of a widget, and calculate heuristics"
    icon = "icons/Tabulate.svg"
    priority = 2

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # variables
        self.t_lock = threading.Lock()
        self.t_pre = []  # type: List[int]
        self.t_post = []  # type: List[int]
        self.buf_lock = threading.Lock()
        self.buf = []  # type: List[int]
        self.buf_size = 100
        # ui
        self.want_main_area = False
        self.want_control_area = False
        self.want_basic_layout = False
        self.want_message_bar = False

    class Inputs:
        """
        Inputs
        """
        pre_node = Input("Pre-Node", Table)
        post_node = Input("Post-Node", Table)

    class Outputs:
        """
        Outputs
        """
        heuristics = Output("Heuristics", Table)
        metrics = Output("Metrics", Table)

    @Inputs.pre_node
    def set_pre_node(self, _: Table):
        t = time.time_ns()
        with self.t_lock:
            self.t_pre.append(t)

    @Inputs.post_node
    def set_post_node(self, _: Table):
        t = time.time_ns()
        with self.t_lock:
            self.t_post.append(t)

    def handleNewSignals(self):
        self.calculate_metrics_and_heuristics()

    def calculate_metrics_and_heuristics(self):
        if len(self.t_pre) > 0 and len(self.t_post) > 0:
            with self.t_lock:
                t0 = self.t_pre.pop(0)
                t1 = self.t_post.pop()
                self.t_pre.clear()
                self.t_post.clear()
            # time elapsed for transformation
            dt = round((t1 - t0) * 1e-6, 3)
            with self.buf_lock:
                self.buf.append(dt)
                mean_dt = sum(self.buf) / len(self.buf)
                if len(self.buf) == self.buf_size:
                    self.buf.pop(0)
            # write statistics to stdout
            print('dt: %.3f' % dt)
            print('mean dt: %.3f' % mean_dt)


if __name__ == "__main__":
    from AnyQt.QtWidgets import QApplication

    app = QApplication(sys.argv)

    ow = MonitorWidget()
    ow.show()
    ow.raise_()
    ow.handleNewSignals()
    app.exec_()
    sys.exit()
