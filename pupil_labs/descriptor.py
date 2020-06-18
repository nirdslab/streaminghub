from pylsl import IRREGULAR_RATE

from core.types import MetaStream

device_info = MetaStream.DeviceInfo(
    model='Pupil Core',
    manufacturer='PupilLabs',
    category='Eye Tracker'
)

streams = {
    # Camera (World)
    'camera': MetaStream.StreamInfo(
        name='Camera (World)',
        unit='',
        freq=IRREGULAR_RATE,
        channel_count=3,
        channels=['r', 'g', 'b']  # r,g,b: color channels
    ),
    # Gaze (Eye 0)
    'gaze.0': MetaStream.StreamInfo(
        name='Gaze Position (Eye 0)',
        unit='',
        freq=IRREGULAR_RATE,
        channel_count=3,
        channels=['x', 'y', 'c']  # x,y: normalized coordinates, c: confidence
    ),
    # Gaze (Eye 1)
    'gaze.1': MetaStream.StreamInfo(
        name='Gaze Position (Eye 1)',
        unit='',
        freq=IRREGULAR_RATE,
        channel_count=3,
        channels=['x', 'y', 'c']  # x,y: normalized coordinates, c: confidence
    ),
    # Fixations
    'fixations': MetaStream.StreamInfo(
        name='Fixations',
        unit='',
        freq=IRREGULAR_RATE,
        channel_count=3,
        channels=['x', 'y', 'w', 'd', 'c']  # x,y: normalized coordinates, w: fxn dispersion, d: fxn duration, c: confidence
    ),
}
