import streaminghub_datamux as dm
import streaminghub_pydfds as dfds


class SimulationManager(dm.Reader[dfds.Node]):
    """
    Stream Reader for DFDS Simulations.

    Functions:
    * setup(**kwargs)
    * list_sources()
    * list_streams(source_id)
    * on_attach(source_id, stream_id, attrs, q, transform, **kwargs)
    * on_pull(source_id, stream_id, attrs, q, transform, state, rate_limit, strict_time, use_relative_ts, **kwargs)
    * on_detach(source_id, stream_id, attrs, q, transform, state, **kwargs)
    * attach(source_id, stream_id, attrs, q, transform, flag, **kwargs)

    """
