from pylsl import IRREGULAR_RATE

from core.types import DeviceDesc, StreamDesc

device_info = DeviceDesc(
    name='Pupil Core',
    device_type='Eye Tracker'
)

streams = {
    # Camera (Eye 0)
    'frame.eye.0': StreamDesc(
        name='Camera (Eye 0)',
        unit='',
        freq=IRREGULAR_RATE,
        channel_count=3,
        channels=['r', 'g', 'b']
    ),
    # Camera (Eye 1)
    'frame.eye.1': StreamDesc(
        name='Camera (Eye 1)',
        unit='',
        freq=IRREGULAR_RATE,
        channel_count=3,
        channels=['r', 'g', 'b']
    ),
    # Camera (World)
    'frame.world': StreamDesc(
        name='Camera (World)',
        unit='',
        freq=IRREGULAR_RATE,
        channel_count=3,
        channels=['r', 'g', 'b']
    ),
    # Gaze (Eye 0)
    'gaze.3d.0': StreamDesc(
        name='Gaze Position (Eye 0)',
        unit='',
        freq=IRREGULAR_RATE,
        channel_count=3,
        channels=['x', 'y', 'c']
    ),
    # Gaze (Eye 0)
    'gaze.3d.1': StreamDesc(
        name='Gaze Position (Eye 1)',
        unit='',
        freq=IRREGULAR_RATE,
        channel_count=3,
        channels=['x', 'y', 'c']
    ),
    # Gaze (Eye 0)
    'gaze.3d.0': StreamDesc(
        name='Gaze Position (Eye 0)',
        unit='',
        freq=IRREGULAR_RATE,
        channel_count=3,
        channels=['x', 'y', 'c']
    ),
}
