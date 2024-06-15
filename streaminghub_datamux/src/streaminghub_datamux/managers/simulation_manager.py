import streaminghub_datamux as datamux
import streaminghub_pydfds as dfds


class SimulationManager(datamux.Reader[dfds.Node]):
    """
    Stream Reader for DFDS Simulations.

    Functions:
    * setup(**kwargs)
    * list_sources()
    * list_streams(source_id)
    * on_attach(source_id, stream_id, attrs, q, transform, **kwargs)
    * on_pull(source_id, stream_id, attrs, q, transform, state, **kwargs)
    * on_detach(source_id, stream_id, attrs, q, transform, state, **kwargs)
    * attach(source_id, stream_id, attrs, q, transform, flag, **kwargs)

    """
