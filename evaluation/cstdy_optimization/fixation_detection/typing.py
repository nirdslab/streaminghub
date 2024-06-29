import pydantic


class Point(pydantic.BaseModel):
    t: float
    x: float
    y: float

class PointX(Point):
    v: float


class Event(pydantic.BaseModel):
    t_entry: float
    t_exit: float


class Fixation(Event):
    x_mean: float
    y_mean: float


class Saccade(Event):
    x_entry: float
    y_entry: float
    x_exit: float
    y_exit: float
    vel_mean: float
    vel_peak: float


class Pupil(pydantic.BaseModel):
    d_mean: float


class AOI(pydantic.BaseModel):
    aoi_id: str | None
