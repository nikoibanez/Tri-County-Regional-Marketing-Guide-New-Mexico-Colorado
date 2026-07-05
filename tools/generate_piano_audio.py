from __future__ import annotations

import math
import wave
from array import array
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "audio"
SAMPLE_RATE = 44_100


def midi_to_hz(note: float) -> float:
    return 440.0 * (2 ** ((note - 69.0) / 12.0))


def envelope(t: float, start: float, duration: float) -> float:
    x = t - start
    if x < 0 or x > duration:
        return 0.0
    attack = 0.018
    decay = 0.46
    release = min(1.9, duration * 0.48)
    if x < attack:
        return x / attack
    if x < decay:
        return 1.0 - 0.44 * ((x - attack) / (decay - attack))
    if x > duration - release:
        return max(0.0, 0.56 * (1.0 - ((x - (duration - release)) / release)))
    return 0.56


def tone_sample(frequency: float, t: float, start: float, duration: float, velocity: float) -> float:
    env = envelope(t, start, duration)
    if env <= 0:
        return 0.0
    x = t - start
    # Piano-ish additive synthesis: a solid fundamental, soft high partials,
    # and a tiny detuned pair to keep the generated asset from sounding sterile.
    partials = (
        (1.000, 0.78, 0.0),
        (2.006, 0.20, 0.2),
        (3.010, 0.085, 0.7),
        (4.018, 0.035, 1.2),
        (1.003, 0.06, 2.1),
    )
    value = 0.0
    for multiplier, level, phase in partials:
        value += level * math.sin((2.0 * math.pi * frequency * multiplier * x) + phase)
    hammer = math.exp(-x * 42.0) * math.sin(2.0 * math.pi * frequency * 9.0 * x) * 0.035
    return (value + hammer) * env * velocity


def render(duration: float, events: list[tuple[float, float, float, float]]) -> list[float]:
    total = int(duration * SAMPLE_RATE)
    samples = [0.0] * total
    for idx in range(total):
        t = idx / SAMPLE_RATE
        value = 0.0
        for start, note, length, velocity in events:
            value += tone_sample(midi_to_hz(note), t, start, length, velocity)
        samples[idx] = value

    # Small room tail: delayed low-level taps, enough to feel like a recorded
    # piano without requiring convolution assets.
    for delay_seconds, amount in ((0.115, 0.10), (0.255, 0.065), (0.410, 0.038)):
        delay = int(delay_seconds * SAMPLE_RATE)
        for idx in range(delay, total):
            samples[idx] += samples[idx - delay] * amount
    return samples


def normalize(samples: list[float], target_peak: float) -> array:
    peak = max(max(samples), abs(min(samples)), 0.0001)
    scale = target_peak / peak
    pcm = array("h")
    for sample in samples:
        limited = max(-0.98, min(0.98, sample * scale))
        pcm.append(int(limited * 32767))
    return pcm


def write_wav(path: Path, samples: list[float], target_peak: float) -> None:
    pcm = normalize(samples, target_peak)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(SAMPLE_RATE)
        handle.writeframes(pcm.tobytes())


def pluck_sample(frequency: float, t: float, start: float, duration: float, velocity: float) -> float:
    x = t - start
    if x < 0 or x > duration:
        return 0.0
    attack = 0.006
    release = duration
    env = min(1.0, x / attack) * math.exp(-x * 1.9) * max(0.0, 1.0 - (x / release) ** 1.8)
    shimmer = (
        math.sin(2.0 * math.pi * frequency * x)
        + 0.42 * math.sin(2.0 * math.pi * frequency * 2.01 * x + 0.35)
        + 0.18 * math.sin(2.0 * math.pi * frequency * 3.04 * x + 1.4)
        + 0.07 * math.sin(2.0 * math.pi * frequency * 4.98 * x + 2.0)
    )
    body = math.sin(2.0 * math.pi * frequency * 0.5 * x) * 0.08
    return (shimmer + body) * env * velocity


def render_plucked(duration: float, events: list[tuple[float, float, float, float]]) -> list[float]:
    total = int(duration * SAMPLE_RATE)
    samples = [0.0] * total
    for start, note, length, velocity in events:
        frequency = midi_to_hz(note)
        start_idx = max(0, int(start * SAMPLE_RATE))
        end_idx = min(total, int((start + length) * SAMPLE_RATE))
        for idx in range(start_idx, end_idx):
            t = idx / SAMPLE_RATE
            samples[idx] += pluck_sample(frequency, t, start, length, velocity)

    # Soft hand-built room and a hint of low desert air. This remains entirely
    # procedural; no sampled recording is embedded.
    for delay_seconds, amount in ((0.092, 0.12), (0.184, 0.08), (0.355, 0.055), (0.710, 0.032)):
        delay = int(delay_seconds * SAMPLE_RATE)
        for idx in range(delay, total):
            samples[idx] += samples[idx - delay] * amount
    return samples


def build_intro() -> None:
    # A definitive opening chord during the black phase. D major with a color
    # tone nods toward the calm Satie/Gymnopedie palette without embedding a
    # copyrighted recording.
    events = [
        (0.08, 50, 4.2, 0.88),
        (0.11, 57, 4.0, 0.76),
        (0.14, 66, 3.8, 0.58),
        (0.17, 73, 3.4, 0.42),
    ]
    write_wav(OUT / "stateline-opening-chord.wav", render(5.2, events), 0.86)


def build_loop() -> None:
    # Original sparse, public-domain-safe piano bed inspired by the research
    # note's Gymnopedie recommendation: slow, warm, rural, and unobtrusive.
    progression = [
        (50, 57, 66, 73),
        (47, 55, 62, 71),
        (45, 52, 61, 69),
        (43, 50, 59, 66),
        (45, 52, 61, 69),
        (47, 55, 62, 71),
        (50, 57, 66, 73),
        (52, 57, 64, 73),
    ]
    events: list[tuple[float, float, float, float]] = []
    beat = 0.0
    for chord_index, chord in enumerate(progression * 2):
        base_velocity = 0.26 if chord_index % 2 == 0 else 0.22
        events.append((beat, chord[0], 5.8, base_velocity * 0.90))
        events.append((beat + 0.78, chord[1], 4.9, base_velocity * 0.70))
        events.append((beat + 1.55, chord[2], 4.4, base_velocity * 0.55))
        events.append((beat + 2.42, chord[3], 3.8, base_velocity * 0.42))
        events.append((beat + 4.95, chord[2], 3.2, base_velocity * 0.34))
        beat += 7.6
    write_wav(OUT / "stateline-gymnopedie-style-loop.wav", render(beat + 2.0, events), 0.62)


def build_yucca_plucked_loop() -> None:
    # Original generated plucked-string bed: slow triads and open fifths, built
    # from code so the web asset is copyright-free and locally reproducible.
    patterns = [
        (45, 52, 57, 64),
        (43, 50, 55, 62),
        (40, 47, 55, 59),
        (42, 49, 54, 61),
        (45, 52, 57, 64),
        (47, 52, 59, 66),
    ]
    events: list[tuple[float, float, float, float]] = []
    beat = 0.0
    for round_index in range(3):
        for chord_index, chord in enumerate(patterns):
            base = 0.30 if (round_index + chord_index) % 2 == 0 else 0.25
            offsets = (0.0, 0.58, 1.16, 1.92, 2.92, 4.10)
            notes = (chord[0], chord[1], chord[2], chord[3], chord[2], chord[1])
            for offset, note in zip(offsets, notes):
                events.append((beat + offset, note, 4.8, base))
            events.append((beat + 5.58, chord[3] + 12, 2.8, base * 0.38))
            beat += 6.4
    write_wav(OUT / "stateline-yucca-plucked-loop.wav", render_plucked(beat + 1.5, events), 0.56)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    build_intro()
    build_loop()
    build_yucca_plucked_loop()
    print(OUT)


if __name__ == "__main__":
    main()
