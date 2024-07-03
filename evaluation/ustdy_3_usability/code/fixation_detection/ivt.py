import math
from collections import deque
from typing import Literal

import numpy as np

import streaminghub_datamux as datamux

from .sg import SG
from .typing import Fixation, Point, PointX, Saccade

SACCADE_STATE = 0
FIXATION_STATE = 1
SG_SMOOTH = 0
SG_DERIV1 = 1
SG_DERIV2 = 2
BLANK_POINT = Point(t=0, x=0, y=0, d=0)


class IVT(datamux.PipeTask):

    def __init__(
        self,
        screen_wh: tuple[float, float],
        diag_dist: tuple[float, float],
        freq: int,
        vt: float,  # deg/s
        transform=None,
        origin: Literal["corner", "center"] = "corner",
        sg_window_hwidth: int = 5,
        sg_poly_deg: int = 7,
    ) -> None:
        super().__init__(transform)
        self.w, self.h = screen_wh
        diag, dist = diag_dist
        self.d = dist / diag * math.sqrt(self.w**2 + self.h**2)
        self.freq = float(freq)
        self.period = 1.0 / self.freq  # sampling period: sec
        self.vt = vt
        self.origin = origin
        self.sg_hwidth = sg_window_hwidth
        self.sg_poly_deg = sg_poly_deg

        self.window_len = (self.sg_hwidth * 2) + 1
        self.sg_x = SG(self.sg_hwidth, self.sg_poly_deg, 0)
        self.sg_y = SG(self.sg_hwidth, self.sg_poly_deg, 0)
        self.sg_dx = SG(self.sg_hwidth, self.sg_poly_deg, 1)
        self.sg_dy = SG(self.sg_hwidth, self.sg_poly_deg, 1)

        self.state = FIXATION_STATE  # initial state: fixation
        self.buf = deque([BLANK_POINT] * self.window_len, self.window_len)
        self.cache: list[PointX] = []

    def clamp_and_rescale(self, x: float, y: float) -> tuple[float, float]:
        if self.origin == "corner":
            min_x, max_x = 0, self.w
            min_y, max_y = 0, self.h
        elif self.origin == "center":
            min_x, max_x = -self.w / 2, self.w / 2
            min_y, max_y = -self.h / 2, self.h / 2
        else:
            raise ValueError()
        x = min(max(x, min_x), max_x) + min_x
        y = min(max(y, min_y), max_y) + min_y
        return x, y

    def sg_filter(self, mode: int) -> Point:
        if mode == SG_SMOOTH:
            f_x, f_y = self.sg_x, self.sg_y
        elif mode == SG_DERIV1:
            f_x, f_y = self.sg_dx, self.sg_dy
        else:
            raise ValueError()
        mid_p = self.buf[self.sg_hwidth]
        x = f_x.apply([p.x for p in self.buf])
        y = f_y.apply([p.y for p in self.buf])
        return Point(t=mid_p.t, x=x, y=y, d=mid_p.d)

    def get_filtered_point(self) -> PointX:
        # get smoothed point
        p = self.sg_filter(mode=SG_SMOOTH)
        # get smoothed derivative
        dp = self.sg_filter(mode=SG_DERIV1)
        # convert to degrees
        dp_θx = math.degrees(math.atan2(dp.x, self.d))
        dp_θy = math.degrees(math.atan2(dp.y, self.d))
        # velocity (deg/second)
        v = math.fabs(math.sqrt(dp_θx**2 + dp_θy**2) / self.period)
        return PointX(t=p.t, x=p.x, y=p.y, d=p.d, v=v)

    def make_fixation(self, pT: PointX | None, check_duration: bool = True) -> Fixation | None:
        # if pT is given, its a saccade point
        pts = self.cache
        if len(pts) > 1:
            t_entry = pts[0].t
            pT = pT or pts[-1]
            t_exit = pT.t
            x_mean = np.mean([p.x for p in pts]).item()
            y_mean = np.mean([p.y for p in pts]).item()

            proceed = ((t_exit - t_entry) >= 0.06) or (not check_duration)
            if proceed:
                return Fixation(
                    t_entry=t_entry,
                    t_exit=t_exit,
                    x_mean=x_mean,
                    y_mean=y_mean,
                )

    def make_saccade(self, pT: PointX | None) -> Saccade | None:
        # if pT is given, its a fixation point
        pts = self.cache
        if len(pts) > 1:
            t_entry, x_entry, y_entry = pts[0].t, pts[0].x, pts[0].y
            pT = pT or pts[-1]
            t_exit, x_exit, y_exit = pT.t, pT.x, pT.y
            vel = [p.v for p in pts]
            vel_mean = np.mean(vel).item()
            vel_peak = np.max(vel).item()
            return Saccade(
                t_entry=t_entry,
                t_exit=t_exit,
                x_entry=x_entry,
                x_exit=x_exit,
                y_entry=y_entry,
                y_exit=y_exit,
                vel_mean=vel_mean,
                vel_peak=vel_peak,
            )
        
    def close(self) -> None:
        # release accumulated points
        if self.state == SACCADE_STATE:
            sacc = self.make_saccade(None)
            if sacc is not None:
                self.target.put(sacc)
        if self.state == FIXATION_STATE:
            fxtn = self.make_fixation(None, check_duration=False)
            if fxtn is not None:
                self.target.put(fxtn)


    def step(self, item) -> int | None:
        """
        compress gaze stream (t, x, y, d) into a fixation/saccade event stream
        v_threshold = 600 #px/s -> normal threshold is 0.5 o5 0.6 px/ms

        Reference: "Review and evaluation of eye movement event detection algorithms. Birawo, B., & Kasprowski, P. (2022), Sensors, 22(22), 8810."

        """

        t: float = item["t"]
        x: float = item["x"]
        y: float = item["y"]
        d: float = item["d"]
        
        if np.isnan(x) or np.isnan(y):
            self.logger.debug(f"ignoring nan at t={t}")
            return
        # nan-safety and scaling
        x, y = self.clamp_and_rescale(x, y)

        # append data point to buffer
        p = Point(t=t, x=x, y=y, d=d)
        self.buf.append(p)

        # run once all blank spots are filled (NOTE adds lag)
        if BLANK_POINT not in self.buf:
            # get filtered point (with velocity)
            p = self.get_filtered_point()

            # velocity thresholding
            if p.v > self.vt:
                if self.state == FIXATION_STATE:
                    # fixation -> saccade (fixation ends)
                    fxtn = self.make_fixation(p)
                    if fxtn is not None:
                        self.target.put(fxtn)
                        self.cache.clear()
                # state -> saccade
                self.state = SACCADE_STATE
            else:
                if self.state == SACCADE_STATE:
                    # saccade -> fixation (fixation starts)
                    sacc = self.make_saccade(p)
                    if sacc is not None:
                        self.target.put(sacc)
                        self.cache.clear()
                # state -> fixation
                self.state = FIXATION_STATE

            # add p to cache
            self.cache.append(p)
