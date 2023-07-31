#!/usr/bin/env python3

import math

from .butterworth import apply_bw_filter
from .fixation import Fixation
from .monitor import Monitor
from .point import Point
from .savitzky_golay import apply_sg_filter


class Process:

  def __init__(self, w, h, screen, dist, f):
    """
    This class encapsulates the analysis program
    """
    self.fileName = None
    self.w = w  # screen width (px)
    self.h = h  # screen height (px)
    self.screen = screen  # screen diameter (in)
    self.dist = dist  # distance from screen (in)
    self.f = f  # sampling frequency (Hz)
    self.pupil_d = []  # pupil diameter (raw, corrected for PFE)
    self.pupil_s = []  # pupil diameter (smoothed, corrected for PFE)
    self.gaze_points = []
    self.smooth_points = []
    self.velocity = []
    self.magnitude = []
    self.acceleration = []
    self.fixations = []
    self.fix_points = []
    self.sac_points = []

  def parse_file(self, file_name):
    self.fileName = file_name
    assert self.fileName.rsplit('.')[-1].lower() == 'csv', "Expected CSV"
    try:
      f = open(self.fileName, 'r')
    except IOError:
      print("Can't open file: " + self.fileName)
      return

    # read lines, throwing away first one (header)
    lines = f.read().splitlines()
    is_first_line = True
    assert lines[0] == 't,x,y,d'  # ensure csv is in expected format

    st = 0.0
    for line in lines[1:]:
      entry = line.split(',')

      # coords should already be normalized
      t = float(entry[0])
      x = float(entry[1])
      y = float(entry[2])
      d = float(entry[3])
      err = 'None'

      # record first time stamp
      if is_first_line:
        is_first_line = False
        st = t

      # make time relative to start, convert to seconds from milliseconds
      t = (t - st) / 1000.0
      x, y = self.clamp(x, y)
      self.gaze_points.append(Point(x, y, t, err))

      # correct the pupil diameter via PFE (pupil foreshortening effect)
      monitor = Monitor(self.w, self.h, self.screen, self.dist)
      cx, cy = 0.5, 0.5  # assume normalized gaze coordinates (0,1) with screen center (.5,.5)
      dx, dy = x - cx, y - cy
      dpi_x = math.sqrt(dx * dx + dy * dy)
      deg = monitor.px_to_deg(dpi_x)
      pfe = math.sqrt(math.cos(math.radians(deg)))
      #     this is the more aggressive variant, but maxes out at 0.94 at center when it should be 1.0
      #     pfe = math.sqrt(0.992 * math.cos((math.radians(deg + 5.3) / 1.121)))
      self.pupil_d.append(Point(d, d / pfe, t, err))

  def smooth(self, sf_degree, sf_cutoff, smooth):
    if smooth:
      # use Butterworth filter for smoothing
      self.smooth_points = apply_bw_filter(self.gaze_points, sf_degree, self.f, sf_cutoff)
    else:
      self.smooth_points = self.gaze_points

    # self.write_smooth_to_file(file_name, w, h)

  def differentiate(self, df_width, df_degree, df_o):

    # differentiate smoothed points with SG filter
    diff_points = apply_sg_filter(self.smooth_points, df_width, df_degree, df_o)
    accel_points = apply_sg_filter(diff_points, df_width, df_degree, df_o)

    # sampling period in s
    period = float(1.0 / float(self.f))
    dt = period * float(df_width)

    r = math.sqrt(float(self.w) * float(self.w) + float(self.h) * float(self.h))
    dpi = r / float(self.screen)

    d = float(self.dist)

    def get_deg(_pt):
      # distance covered in pixels (across diff filter window size)
      dx = _pt.at(0) * float(self.w)
      dy = _pt.at(1) * float(self.h)

      # assume D is in inches
      _deg_x = 2 * math.degrees(math.atan2((dx / dpi), (2 * d)))
      _deg_y = 2 * math.degrees(math.atan2((dy / dpi), (2 * d)))
      return [_deg_x, _deg_y]

    def get_rate(_deg_x, _deg_y):
      # deg_x, deg_y is degrees per filter window, div by dt to get per second
      _rate_x = _deg_x / dt
      _rate_y = _deg_y / dt
      return [_rate_x, _rate_y]

    for pt in diff_points:
      deg_x, deg_y = get_deg(pt)
      vel_x, vel_y = get_rate(deg_x, deg_y)
      self.magnitude.append(Point(deg_x, deg_y, pt.get_timestamp(), pt.get_status()))
      self.velocity.append(Point(vel_x, vel_y, pt.get_timestamp(), pt.get_status()))

    for pt in accel_points:
      deg_x, deg_y = get_deg(pt)
      acc_x, acc_y = get_rate(deg_x, deg_y)
      self.acceleration.append(Point(acc_x, acc_y, pt.get_timestamp(), pt.get_status()))

    # self.write_differentiate_to_file(file_name, w, h)

  def threshold(self, vt, monitor, t_type, proximity):

    # state table
    # state         |   input    |  output
    # ------------------------------------
    # (1) fixation  | a < T (1)  |    1
    # (0) saccade   | a < T (1)  |    1
    # (1) fixation  | a > T (0)  |    0
    # (0) saccade   | a > T (0)  |    0
    #

    # fixation state enums
    fixation = 1
    saccade = 0

    # assuming starting state = fixation
    state = fixation

    st = 0.
    ux = 0.
    uy = 0.
    k = 0

    # initialize list of micro-saccade indices (for each fixation)
    ms_indices = []

    # initialize list of saccade indices (for each saccade)
    s_indices = []

    if len(self.velocity) > 0:

      for i in range(len(self.smooth_points)):

        # (smoothed) data we are classifying
        x = self.smooth_points[i].at(0)
        y = self.smooth_points[i].at(1)

        # corresponding velocity
        vx = self.velocity[i].at(0)
        vy = self.velocity[i].at(1)

        # saccade velocity
        sac_vel = math.sqrt(vx ** 2 + vy ** 2)

        if math.fabs(sac_vel) > float(vt) / 2:

          # amplitude > T
          if state == fixation:
            # state transition from fixation to saccade (fixation ends)

            # get end time of current point, compute duration
            et = self.smooth_points[i].get_timestamp()
            tt = et - st

            # don't add fixation with -ve duration
            # (due to spurious timestamp in .raw file)
            if st > 0.0 and tt > 0.0:
              ux, uy = self.clamp(ux, uy)
              if t_type in monitor.n_dict:
                # need to clamp fixation centroid: it could have gone negative

                sx = monitor.S[monitor.n_dict[t_type], 0]
                sy = monitor.S[monitor.n_dict[t_type], 1]

                dx = ux - sx
                dy = uy - sy
                dist = math.sqrt(dx * dx + dy * dy)

                #             how I used to do it in old micro-saccade code
                #             dx = 2*math.degrees(math.atan2((ux - sx)/dpi,2*D))
                #             dy = 2*math.degrees(math.atan2((uy - sy)/dpi,2*D))
                #             f_deg_away = math.sqrt(dx*dx + dy*dy)
                # if we restrict to 3.0 or 3.5 degrees, we won't get enough
                # micro-saccades (not enough fixations)
              else:
                # fixation centroids not defined, calculate distance based on current mean
                dist = math.sqrt(ux * ux + uy * uy)

              if proximity and monitor.px_to_deg(dist) < 3.0:
                self.fixations.append(Fixation(ux, uy, st, tt))

                # append list of indices (sequence of points within this fixation)
                if len(ms_indices) > 0:
                  self.fix_points.append(ms_indices)
              else:
                self.fixations.append(Fixation(ux, uy, st, tt))

                # append list of indices (sequence of points within this fixation)
                if len(ms_indices) > 0:
                  self.fix_points.append(ms_indices)

            # saccade starts
            # reset list of saccade indices for this saccade
            s_indices.clear()

          else:
            # state transition from saccade to saccade (saccade continues)
            #           pass

            # add in current index into s_indices
            s_indices.append(i)

          state = saccade

        else:

          # amplitude < T
          if state == fixation:
            # state transition from fixation to fixation (fixation continues)
            pass
          else:
            # state transition from saccade to fixation (fixation starts)

            # set start time
            st = self.smooth_points[i].get_timestamp()

            # reset running mean and counter
            ux = 0.
            uy = 0.
            k = 0

            # reset list of micro-saccade indices for this fixation
            ms_indices.clear()

            # saccade ends
            # append list of indices (sequence of points within this saccade)
            if len(s_indices) > 0:
              self.sac_points.append(s_indices)

          # compute running mean
          # from Brown, Robert Grover, "Introduction to Random Signal
          #   Analysis and Kalman Filtering", John Wiley & Sons, New York, NY
          #   1983 [p.182] TK5102.5 .B696
          ux = float(k) / float(k + 1) * ux + 1.0 / float(k + 1) * x
          uy = float(k) / float(k + 1) * uy + 1.0 / float(k + 1) * y
          k += 1

          # add in current index into indices
          ms_indices.append(i)

          state = fixation

    # compute mean fixation duration
    if len(self.fixations) > 1:
      durations = [0.0] * len(self.fixations)
      for i in range(len(self.fixations)):
        durations[i] = self.fixations[i].get_duration()
      min_dur = min(durations)
      max_dur = max(durations)
    elif len(self.fixations) == 1:
      avg_dur = self.fixations[0].get_duration()
      min_dur = avg_dur
      max_dur = avg_dur
    else:
      avg_dur = 0.0
      min_dur = avg_dur
      max_dur = avg_dur

    # normalize
    for i in range(len(self.fixations)):
      self.fixations[i].normalize_duration(min_dur, max_dur)

  def write_smooth_to_file(self, file_name):
    outfile = open(file_name, 'w')
    outfile.write("t,x,y\n")  # csv header
    for pt in self.smooth_points:
      x = pt.at(0) * float(self.w)
      y = pt.at(1) * float(self.h)
      t = pt.get_timestamp()
      text = "%.12f,%.12f,%.12f\n" % (t, x, y)
      outfile.write(text)
    outfile.close()

  def write_differentiate_to_file(self, file_name):
    outfile = open(file_name, 'w')
    outfile.write("t,x,y\n")  # csv header
    for pt in self.velocity:
      # don't scale by w,h here, already did so above
      x = pt.at(0)
      y = pt.at(1)
      t = pt.get_timestamp()
      line = "%.12f,%.12f,%.12f\n" % (t, x, y)
      outfile.write(line)
    outfile.close()

  def write_threshold_to_file(self, file_name):
    outfile = open(file_name, 'w')
    outfile.write("t,x,y,fd,sa,sd\n")  # csv header
    sac_dur = 0.0
    for i in range(len(self.fixations)):
      t = self.fixations[i].get_timestamp()
      x = self.fixations[i].at(0)  # * float(w) (commented out to keep normalized coordinates)
      y = self.fixations[i].at(1)  # * float(h) (commented out to keep normalized coordinates)
      fxn_dur = self.fixations[i].get_duration()
      st = t  # fixation timestamp is its start_time (st)
      tt = fxn_dur  # fixation duration is its end_time - start_ime (et - st)
      et = st + tt
      if i < len(self.fixations) - 1:
        dx = x - (self.fixations[i + 1].at(0))  # * float(w))
        dy = y - (self.fixations[i + 1].at(1))  # * float(h))
        sac_dur = self.fixations[i + 1].get_timestamp() - et
        sac_amp = math.sqrt(dx ** 2 + dy ** 2)
      else:
        sac_amp = 0.0
      # line = "%f %f %f %f %f %f\n" % (x, y, fxn_dur, sac_amp, sac_dur, t)
      line = "%.12f,%.12f,%.12f,%.12f,%.12f,%.12f\n" % (t, x, y, fxn_dur, sac_amp, sac_dur)
      outfile.write(line)

    outfile.close()

  @staticmethod
  def clamp(x, y):
    if x < 0:
      x = 0.0
    if y < 0:
      y = 0.0
    if x > 1:
      x = 1.0
    if y > 1:
      y = 1.0
    return x, y
