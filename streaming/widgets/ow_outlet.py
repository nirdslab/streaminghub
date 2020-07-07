import sys

from Orange.data import Table
from Orange.widgets import widget
from Orange.widgets.utils.signals import Input

SELECT_STREAM_MSG = 'None Selected'
LOADING_MSG = 'Loading...'


class OWOutlet(widget.OWWidget):
    """
    Widget to push data and metadata into LSL streams
    """
    name = "Outlet"
    description = "Publish data and metadata for intermediary analysis results"
    icon = "icons/Stream.svg"
    priority = 1

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # variables
        self.data = ...  # type: Table
        # ui
        self.want_main_area = False
        self.want_basic_layout = False
        self.want_control_area = False
        self.want_message_bar = False

    class Inputs:
        """
        Inputs
        """
        data = Input("Data", Table)

    @Inputs.data
    def set_data(self, data: Table):
        self.data = data




if __name__ == "__main__":
    from AnyQt.QtWidgets import QApplication

    app = QApplication(sys.argv)

    ow = OWOutlet()
    ow.show()
    ow.raise_()
    ow.handleNewSignals()
    app.exec_()
    sys.exit()
