import streaminghub_datamux as datamux
import streaminghub_pydfds as dfds


class SimulationManager(datamux.Reader[dfds.Node]):
    """
    Stream Reader for DFDS Simulations.

    Functions:
    * attach(source_id, stream_id, q, **kwargs)
    * serve(source_id, stream_id, **kwargs)
    * list_sources()
    * list_streams(source_id)

    """
