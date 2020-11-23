from pylsl import StreamInfo


def stream_info_to_dict(x: StreamInfo):
    return {
        'id': x.source_id(),
        'channels': x.channel_count(),
        'name': x.name(),
        'type': x.type()
    }
