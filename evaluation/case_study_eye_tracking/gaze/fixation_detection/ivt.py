import math
from collections import deque

import numpy as np
import streaminghub_datamux as datamux

from .sg import SG
from .typing import FixationEvent, Point, SaccadeEvent

SACCADE_STATE = 0
FIXATION_STATE = 1
SG_SMOOTH = 0
SG_DERIV1 = 1
SG_DERIV2 = 2
BLANK_POINT = Point(t=0, x=0, y=0, d=0)


class IVT(datamux.PipeTask):

    sg_window_len_k = 5  # dfwidth: savitzky-golay filter width 2k+1 = 2(5)+1 =11
    sg_window_len_k = 25  # dfwidth: savitzky-golay filter width 2k+1 = 2(5)+1 =11
    sg_polynomial_degree = 9  # dfdegree: savitzky-golay filter degree
    differentiate_order = 1

    def __init__(
        self,
        width: int,
        height: int,
        hertz: int,
        dist: float,
        screen: float,
        vt: float,
        transform=None,
    ) -> None:
        super().__init__(transform)
        self.width = float(width)
        self.height = float(height)
        self.herz = float(hertz)
        self.dist = float(dist)
        self.screen = float(screen)
        self.vt = vt

        self.period = 1.0 / self.herz  # sampling period: sec
        self.D = self.dist  # distance: in
        self.dpi = math.sqrt(self.width**2 + self.height**2) / self.screen  # dpi: px/in
        self.window_len = (self.sg_window_len_k * 2) + 1
        self.sg_x = SG(self.sg_window_len_k, self.sg_polynomial_degree, 0)
        self.sg_y = SG(self.sg_window_len_k, self.sg_polynomial_degree, 0)
        self.sg_dx = SG(self.sg_window_len_k, self.sg_polynomial_degree, 1)
        self.sg_dy = SG(self.sg_window_len_k, self.sg_polynomial_degree, 1)

        self.state = FIXATION_STATE  # initial state: fixation
        self.data_n = 0
        self.gazepoints = deque([BLANK_POINT] * self.window_len, self.window_len)
        self.smthpoints = deque([BLANK_POINT] * self.window_len, self.window_len)
        self.temp_fixpoints: list[Point] = []
        self.temp_sacpoints: list[Point] = []
        self.velocities: list[float] = []

    def clamp(self, *args: float) -> tuple[float, ...]:
        return tuple(np.clip(args, a_min=0.0, a_max=1.0).tolist())

    def sg_filter(self, mode: int) -> Point:
        if mode == SG_SMOOTH:
            f_x, f_y = self.sg_x, self.sg_y
        elif mode == SG_DERIV1:
            f_x, f_y = self.sg_dx, self.sg_dy
        else:
            raise ValueError()
        mid_p = self.gazepoints[self.sg_window_len_k]
        x = f_x.apply([p.x for p in self.gazepoints])
        y = f_y.apply([p.y for p in self.gazepoints])
        return Point(t=mid_p.t, x=x, y=y, d=mid_p.d)

    def make_fixation(self, pT: Point) -> FixationEvent | None:

        pts = self.temp_fixpoints

        if len(pts) > 1:
            t_entry = pts[0].t
            t_exit = pT.t
            x_mean = np.mean([p.x for p in pts]).item()
            y_mean = np.mean([p.y for p in pts]).item()
            d_mean = np.mean([p.d for p in pts]).item()

            return FixationEvent(
                t_entry=t_entry,
                t_exit=t_exit,
                x_mean=x_mean,
                y_mean=y_mean,
                d_mean=d_mean,
            )

    def make_saccade(self, pT: Point) -> SaccadeEvent | None:

        pts = self.temp_sacpoints
        vel = self.velocities
        assert len(pts) == len(vel)

        if len(pts) > 1 and len(vel) > 1:
            t_entry, x_entry, y_entry = pts[0].t, pts[0].x, pts[0].y
            t_exit, x_exit, y_exit = pT.t, pT.x, pT.y
            vel_mean = np.mean(vel).item()
            vel_peak = np.max(vel).item()
            d_mean = np.mean([s.d for s in pts]).item()

            return SaccadeEvent(
                t_entry=t_entry,
                t_exit=t_exit,
                x_entry=x_entry,
                x_exit=x_exit,
                y_entry=y_entry,
                y_exit=y_exit,
                vel_mean=vel_mean,
                vel_peak=vel_peak,
                d_mean=d_mean,
            )

    def __call__(self, *args, **kwargs) -> None:
        """
        compress gaze stream (t, x, y, d) into a fixation/saccade event stream
        v_threshold = 600 #px/s -> normal threshold is 0.5 o5 0.6 px/ms

        Reference: "Review and evaluation of eye movement event detection algorithms. Birawo, B., & Kasprowski, P. (2022), Sensors, 22(22), 8810."

        """

        t: float
        x: float
        y: float
        d: float

        item = self.source.get()
        if item is None:
            return

        t, x, y, d = item["t"], item["x"], item["y"], item["d"]

        # nan-safety and clamping
        x = x or 0.0
        y = y or 0.0
        x, y = self.clamp(x, y)
        self.data_n += 1

        # append data
        if self.data_n < self.window_len:
            gazePoint = Point(t=t, x=x, y=y, d=d)
            self.gazepoints.append(gazePoint)

        # otherwise re-compute fixations and append incoming data
        else:
            if self.data_n >= self.window_len:
                gazePoint = Point(t=t, x=x, y=y, d=d)
                self.gazepoints.append(gazePoint)

                # get smoothed point
                p = self.sg_filter(mode=SG_SMOOTH)
                p.x *= self.width
                p.y *= self.height
                self.smthpoints.append(p)

                # differentiate smoothed points with SG filter
                dp = self.sg_filter(mode=SG_DERIV1)
                dp.x *= self.width
                dp.y *= self.height
                # convert to degrees
                dp_θx = math.degrees(math.atan2(dp.x / self.dpi, self.D))
                dp_θy = math.degrees(math.atan2(dp.y / self.dpi, self.D))
                # velocity (deg/second)
                velocity = math.fabs(math.sqrt(dp_θx**2 + dp_θy**2) / self.period)

                if velocity > self.vt:
                    # velocity > T
                    if self.state == FIXATION_STATE and len(self.temp_fixpoints) > 0:
                        assert len(self.temp_sacpoints) == 0
                        # fixation -> saccade (fixation ends)
                        fxn_duration = self.temp_fixpoints[-1].t - self.temp_fixpoints[0].t
                        # min fix duration 60 ms
                        if fxn_duration >= 0.06:
                            fxtn = self.make_fixation(p)
                            assert fxtn is not None
                            self.target.put_nowait(fxtn)
                        else:
                            # does not qualify as fixation - move to temp saccades
                            self.temp_sacpoints.extend(self.temp_fixpoints)
                        self.temp_fixpoints.clear()
                        while len(self.velocities) > len(self.temp_sacpoints):
                            self.velocities.pop(0)

                    # state -> saccade
                    self.state = SACCADE_STATE
                    self.temp_sacpoints.append(p)
                    self.velocities.append(velocity)

                else:
                    # "velocity < T"
                    #  saccade -> fixation
                    if self.state == SACCADE_STATE and len(self.temp_sacpoints) > 0:
                        assert len(self.temp_fixpoints) == 0
                        # saccade -> fixation (fixation starts)
                        sacc = self.make_saccade(p)
                        if sacc is not None:
                            self.target.put_nowait(sacc)
                        else:
                            # does not qualify as saccade - move to temp fixations
                            self.temp_fixpoints.extend(self.temp_sacpoints)
                        self.temp_sacpoints.clear()
                        while len(self.velocities) > len(self.temp_fixpoints):
                            self.velocities.pop(0)

                    # state -> fixation
                    self.state = FIXATION_STATE
                    self.temp_fixpoints.append(p)
                    self.velocities.append(velocity)
