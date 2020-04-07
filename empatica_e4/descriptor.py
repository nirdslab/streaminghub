from pylsl import IRREGULAR_RATE

from core.types import DeviceDesc, StreamDesc

device_info = DeviceDesc(
    name='Empatica E4',
    device_type='Wristband'
)

streams = {
    # 3-axis acceleration (unit - gravity)
    'acc': StreamDesc(
        name='acceleration',
        unit='g',
        freq=32,
        channel_count=3,
        channels=['acc_x', 'acc_y', 'acc_z']
    ),
    # Blood Volume Pulse (unit - lumen)
    'bvp': StreamDesc(
        name='blood volume pulse',
        unit='lm',
        freq=64,
        channel_count=1,
        channels=['bvp']

    ),
    # Galvanic Skin Response (unit - micro siemens)
    'gsr': StreamDesc(
        name='galvanic skin response',
        unit='μS',
        freq=IRREGULAR_RATE,
        channel_count=1,
        channels=['gsr']
    ),
    # Inter-Beat Interval (unit - seconds)
    'ibi': StreamDesc(
        name='inter-beat interval',
        unit='s',
        freq=IRREGULAR_RATE,
        channel_count=1,
        channels=['ibi']
    ),
    # Heart rate (unit - beats per minute)
    'hr': StreamDesc(
        name='heart rate',
        unit='bpm',
        freq=IRREGULAR_RATE,
        channel_count=1,
        channels=['hr']
    ),
    # Skin Temperature (unit - celsius)
    'tmp': StreamDesc(
        name='skin temperature',
        unit='c',
        freq=IRREGULAR_RATE,
        channel_count=1,
        channels=['tmp']
    ),
    # Device Battery (unit - percent)
    'bat': StreamDesc(
        name='battery level',
        unit='%',
        freq=IRREGULAR_RATE,
        channel_count=1,
        channels=['bat']
    ),
    # Tag taken from the device (unit - none, value=1)
    'tag': StreamDesc(
        name='tag',
        unit='',
        freq=IRREGULAR_RATE,
        channel_count=1,
        channels=['tag']
    )
}
