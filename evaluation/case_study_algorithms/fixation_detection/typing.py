import pydantic


class Point(pydantic.BaseModel):
    t: float
    x: float
    y: float
    d: float


class FixationEvent(pydantic.BaseModel):

    x_mean: float
    y_mean: float
    t_entry: float
    t_exit: float


class SaccadeEvent(pydantic.BaseModel):
    amp: float
    vel_mean: float
    vel_peak: float
    t_entry: float
    t_exit: float


class PupilEvent(pydantic.BaseModel):
    d_mean: float


class AOIEvent(pydantic.BaseModel):
    aoi_id: str | None


class CompositeFixationEvent(PupilEvent, FixationEvent): ...


class CompositeSaccadeEvent(PupilEvent, SaccadeEvent): ...
