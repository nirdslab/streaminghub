import pydantic


class Point(pydantic.BaseModel):
    t: float
    x: float
    y: float
    d: float


class Event(pydantic.BaseModel):
    t_entry: float
    t_exit: float


class Fixation(Event):

    x_mean: float
    y_mean: float


class Saccade(Event):
    amp: float
    vel_mean: float
    vel_peak: float


class Pupil(pydantic.BaseModel):
    d_mean: float


class AOI(pydantic.BaseModel):
    aoi_id: str | None


class FixationEvent(Pupil, Fixation): ...


class SaccadeEvent(Pupil, Saccade): ...
