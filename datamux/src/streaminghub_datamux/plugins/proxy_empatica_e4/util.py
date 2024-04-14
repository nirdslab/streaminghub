class E4SSCommand:
    """
    Server Commands
    """

    DEVICE_DISCOVER_LIST = "device_discover_list"
    DEVICE_CONNECT_BTLE = "device_connect_btle"
    DEVICE_DISCONNECT_BTLE = "device_disconnect_btle"
    DEVICE_LIST = "device_list"
    DEVICE_CONNECT = "device_connect"
    DEVICE_DISCONNECT = "device_disconnect"
    DEVICE_SUBSCRIBE = "device_subscribe"
    PAUSE = "pause"


class E4ServerState:
    """
    Server States
    """

    NEW = "new"
    WAITING = "waiting"
    NO_DEVICES = "no_devices"
    DEVICES_FOUND = "devices_found"
    CONNECTED_TO_DEVICE = "connected"
    READY_TO_SUBSCRIBE = "ready_to_subscribe"
    SUBSCRIBE_COMPLETED = "subscribe completed"
    STREAMING = "streaming"
