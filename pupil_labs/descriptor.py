from pylsl import IRREGULAR_RATE

from core.types import DeviceDesc, StreamDesc

device_info = DeviceDesc(
    name='Pupil Core',
    device_type='Eye Tracker'
)

streams = {
    # Camera (World)
    'camera': StreamDesc(
        name='Camera (World)',
        unit='',
        freq=IRREGULAR_RATE,
        channel_count=3,
        channels=['r', 'g', 'b']  # r,g,b: color channels
    ),
    # Gaze (Eye 0)
    'gaze.0': StreamDesc(
        name='Gaze Position (Eye 0)',
        unit='',
        freq=IRREGULAR_RATE,
        channel_count=3,
        channels=['x', 'y', 'c']  # x,y: normalized coordinates, c: confidence
    ),
    # Gaze (Eye 1)
    'gaze.1': StreamDesc(
        name='Gaze Position (Eye 1)',
        unit='',
        freq=IRREGULAR_RATE,
        channel_count=3,
        channels=['x', 'y', 'c']  # x,y: normalized coordinates, c: confidence
    ),
    # Fixations
    'fixations': StreamDesc(
        name='Fixations',
        unit='',
        freq=IRREGULAR_RATE,
        channel_count=3,
        channels=['x', 'y', 'w', 'd', 'c']  # x,y: normalized coordinates, w: fxn dispersion, d: fxn duration, c: confidence
    ),
}
