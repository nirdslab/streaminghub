import sys
from typing import List, Tuple

import pylsl
from Orange.widgets import widget, gui
from Orange.widgets.utils.signals import Output

SELECT_STREAM_MSG = 'None Selected'
LOADING_MSG = 'Loading...'


class InletWidget(widget.OWWidget):
  """
  Widget to fetch data and metadata from LSL streams
  """
  name = "Inlet"
  description = "Connect to LSL streams and fetch data and metadata from them"
  icon = "icons/Stream.svg"
  priority = 1

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    # variables
    self.available_streams = []  # type: List[pylsl.StreamInfo]
    self.available_stream_labels = []  # type: List[Tuple[str, int]]
    self.current_selection = []  # type: List[int]
    self.selected_streams = []  # type: List[pylsl.StreamInfo]
    self.selected_inlets = []  # type: List[pylsl.StreamInlet]
    # ui
    self.want_main_area = False
    self.wb_control_area = gui.widgetBox(
      widget=self.controlArea,
      minimumWidth=400
    )
    self.wb_selected_streams = gui.widgetBox(
      widget=self.wb_control_area,
      box="Selected Stream(s)"
    )
    self.wl_selected_streams = gui.widgetLabel(
      widget=self.wb_selected_streams,
      label='None'
    )
    self.wb_available_streams = gui.widgetBox(
      widget=self.wb_control_area,
      box="Available Streams"
    )
    self.lb_streams = gui.listBox(
      widget=self.wb_available_streams,
      master=self,
      selectionMode=gui.OrangeListBox.MultiSelection,
      labels='available_stream_labels',
      value='current_selection',
      callback=self.on_stream_selection_changed
    )
    self.btn_refresh = gui.button(
      widget=self.buttonsArea,
      master=self,
      label='Refresh Streams List',
      callback=self.fetch_lsl_streams
    )
    self.btn_ok = gui.button(
      widget=self.buttonsArea,
      master=self,
      label='OK',
      default=True,
      callback=self.on_stream_selection_confirmed
    )

  class Outputs:
    """
    Outputs
    """
    streams = Output("Streams", pylsl.StreamInlet)

  def on_stream_selection_changed(self):
    """
    This method is called when the stream selection is changed.
    When changed, the variable current_selection will be updated, and should be used to update state.
    """
    if len(self.current_selection) > 0:
      selected_stream_names = [self.available_stream_labels[i][0] for i in self.current_selection]
      self.wl_selected_streams.setText('\n'.join(sorted(selected_stream_names)))
    else:
      self.wl_selected_streams.setText(SELECT_STREAM_MSG)

  def on_stream_selection_confirmed(self):
    """
    This method updates the selected_streams setting variable, and sends stream_inlets as output
    """
    # select streams
    self.selected_streams = [self.available_streams[i] for i in self.current_selection]
    print(f'Selected {len(self.selected_streams)} streams')
    # create stream inlets using selected streams
    self.selected_inlets = list(map(pylsl.StreamInlet, self.selected_streams))
    # send inlets as outputs
    self.Outputs.streams.send(self.selected_inlets)
    self.close()

  @staticmethod
  def gen_stream_label(x: pylsl.StreamInfo):
    """
    Generate a user-friendly label for a stream, using its metadata
    :param x: StreamInfo object
    """
    return f"{x.name()} {x.type()} ({x.channel_count()}ch) -  {x.nominal_srate()} Hz"

  def fetch_lsl_streams(self):
    """
    This method fetches available LSL streams, and updates variables
    """
    # Set loading labels
    self.wl_selected_streams.setText(LOADING_MSG)
    # Fetch data
    self.available_streams = pylsl.resolve_streams()
    self.available_stream_labels = list(map(lambda x: (self.gen_stream_label(x), 3), self.available_streams))
    # Update labels
    self.wl_selected_streams.setText(SELECT_STREAM_MSG)

  def showEvent(self, event):
    super().showEvent(event)
    if len(self.available_streams) == 0:
      self.fetch_lsl_streams()

  def onDeleteWidget(self):
    self.cancel()
    super().onDeleteWidget()

  def cancel(self):
    for inlet in self.selected_inlets:
      inlet.close_stream()


if __name__ == "__main__":
  from AnyQt.QtWidgets import QApplication

  app = QApplication(sys.argv)

  ow = InletWidget()
  ow.show()
  ow.raise_()
  ow.handleNewSignals()
  app.exec_()
  sys.exit()
