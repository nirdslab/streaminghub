import numpy as np
import pandas as pd
import streaminghub_datamux as dm

from fixation_detection.typing import Fixation, Saccade


class WhiteNoiseSimulator(dm.PipeTask):
    """
    Simulate iid Gaussian Noise Conditioned on Most Recent Fixation

    """
    last_item = None

    def __init__(self, freq: float = 60.0, xy_scale: float = 0.1, d_scale: float = 0.001, transform=None) -> None:
        super().__init__(transform)
        self.freq = freq
        self.dt = 1.0 / freq
        self.xy_scale = xy_scale
        self.d_scale = d_scale

    def generate_white_noise(self, num_samples: int):
        return np.random.randn(num_samples)

    def synthesize_fixation(self, f: Fixation) -> list[dict]:
        num_samples = int(np.round((f.t_exit - f.t_entry) * self.freq)) + 1
        t_sim = np.linspace(f.t_entry, f.t_exit, num_samples)
        x_sim = f.x_mean + self.generate_white_noise(num_samples) * self.xy_scale
        y_sim = f.y_mean + self.generate_white_noise(num_samples) * self.xy_scale
        return pd.DataFrame(dict(t=t_sim, x=x_sim, y=y_sim, event="fixation")).to_dict("records")

    def synthesize_saccade(self, s: Saccade) -> list[dict]:
        num_samples = int(np.round((s.t_exit - s.t_entry) * self.freq)) + 1
        t_sim = np.linspace(s.t_entry, s.t_exit, num_samples)
        x_sim = np.linspace(s.x_entry, s.x_exit, num_samples) + self.generate_white_noise(num_samples) * self.xy_scale
        y_sim = np.linspace(s.y_entry, s.y_exit, num_samples) + self.generate_white_noise(num_samples) * self.xy_scale
        return pd.DataFrame(dict(t=t_sim, x=x_sim, y=y_sim, event="saccade")).to_dict("records")
    
    def close(self) -> None:
        self.target.put(self.last_item)

    def step(self, item) -> int | None:
        if not isinstance(item, (Fixation, Saccade)):
            return
        if isinstance(item, Saccade):
            data = self.synthesize_saccade(item)
        if isinstance(item, Fixation):
            data = self.synthesize_fixation(item)
        for row in data[:-1]:
            self.target.put(dict(row))
        self.last_item = data[-1]


class PinkNoiseSimulator(dm.PipeTask):
    """
    Simulate Pink Noise Conditioned on Most Recent Fixation

    """
    last_item = None

    def generate_pink_noise(self, n_samples: int):
        white_noise = np.random.randn(n_samples)
        white_fft = np.fft.rfft(white_noise, n_samples)
        freqs = np.fft.rfftfreq(n_samples, d=1 / self.freq)
        scale = np.zeros_like(freqs)
        scale[1:] = 1 / np.sqrt(freqs[1:])  # Exclude DC component
        pink_fft = white_fft * scale
        pink_noise = np.fft.irfft(pink_fft, n_samples)
        return pink_noise

    def __init__(self, freq: float = 60.0, xy_scale: float = 0.1, d_scale: float = 0.001, transform=None) -> None:
        super().__init__(transform)
        self.freq = freq
        self.dt = 1.0 / freq
        self.xy_scale = xy_scale
        self.d_scale = d_scale

    def synthesize_fixation(self, f: Fixation) -> list[dict]:
        num_samples = int(np.round((f.t_exit - f.t_entry) * self.freq)) + 1
        t_sim = np.linspace(f.t_entry, f.t_exit, num_samples)
        x_sim = f.x_mean + self.generate_pink_noise(num_samples) * self.xy_scale
        y_sim = f.y_mean + self.generate_pink_noise(num_samples) * self.xy_scale
        return pd.DataFrame(dict(t=t_sim, x=x_sim, y=y_sim, event="fixation")).to_dict("records")

    def synthesize_saccade(self, s: Saccade) -> list[dict]:
        num_samples = int(np.round((s.t_exit - s.t_entry) * self.freq)) + 1
        t_sim = np.linspace(s.t_entry, s.t_exit, num_samples)
        x_sim = np.linspace(s.x_entry, s.x_exit, num_samples) + self.generate_pink_noise(num_samples) * self.xy_scale
        y_sim = np.linspace(s.y_entry, s.y_exit, num_samples) + self.generate_pink_noise(num_samples) * self.xy_scale
        return pd.DataFrame(dict(t=t_sim, x=x_sim, y=y_sim, event="saccade")).to_dict("records")
    
    def close(self) -> None:
        self.target.put(self.last_item)

    def step(self, item) -> int | None:
        if not isinstance(item, (Fixation, Saccade)):
            return
        if isinstance(item, Saccade):
            data = self.synthesize_saccade(item)
        if isinstance(item, Fixation):
            data = self.synthesize_fixation(item)
        for row in data[:-1]:
            self.target.put(dict(row))
        self.last_item = data[-1]
