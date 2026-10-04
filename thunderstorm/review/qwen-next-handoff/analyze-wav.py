#!/usr/bin/env python3
"""Read-only WAV QA using existing ffmpeg/ffprobe and numpy.

Usage: python3 analyze_wav.py PATH [PATH ...] --output report.json
PATH may be a WAV file or a directory (all .wav below it are inspected).
No network, synthesis, credentials, or automated transcript claims.
Pitch estimates are only supporting diagnostics, not speaker identity tests.
"""
import argparse
import json
import math
import subprocess
from pathlib import Path

import numpy as np


def db(value):
    return round(20 * math.log10(max(float(value), 1e-12)), 2)


def analyze(path):
    report = {"file": str(path.resolve()), "warnings": []}
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
        capture_output=True, text=True,
    )
    if probe.returncode:
        report.update(decode_ok=False, error=probe.stderr.strip())
        return report
    info = json.loads(probe.stdout)
    stream = next((s for s in info["streams"] if s["codec_type"] == "audio"), None)
    if stream is None:
        report.update(decode_ok=False, error="No audio stream")
        return report
    report.update(codec=stream.get("codec_name"), sample_rate=int(stream["sample_rate"]),
                  channels=stream["channels"], source_size_bytes=path.stat().st_size)
    decoded = subprocess.run(
        ["ffmpeg", "-v", "error", "-xerror", "-i", str(path), "-f", "f32le", "-ac", "1", "-ar", "24000", "pipe:1"],
        capture_output=True,
    )
    if decoded.returncode:
        report.update(decode_ok=False, error=decoded.stderr.decode(errors="replace").strip())
        return report
    x = np.frombuffer(decoded.stdout, dtype="<f4")
    if not len(x) or not np.isfinite(x).all():
        report.update(decode_ok=False, error="Empty or non-finite decoded samples")
        return report
    duration = len(x) / 24000
    peak = float(np.max(np.abs(x)))
    report.update(decode_ok=True, duration_seconds=round(duration, 3), peak_dbfs=db(peak),
                  rms_dbfs=db(np.sqrt(np.mean(x * x))),
                  clipping_fraction=round(float(np.mean(np.abs(x) >= 0.999)), 8))
    # Envelope at 20 ms resolution; fixed low threshold highlights obvious dead air.
    hop = 480
    padded = np.pad(x, (0, (-len(x)) % hop))
    envelopes = np.sqrt(np.mean(padded.reshape(-1, hop) ** 2, axis=1))
    active = np.flatnonzero(envelopes >= 10 ** (-45 / 20))
    if len(active):
        lead = active[0] * hop / 24000
        tail = max(0, duration - (active[-1] + 1) * hop / 24000)
        report.update(leading_silence_seconds=round(lead, 3), trailing_silence_seconds=round(tail, 3),
                      active_seconds=round(len(active) * hop / 24000, 3))
    else:
        report.update(leading_silence_seconds=round(duration, 3), trailing_silence_seconds=round(duration, 3), active_seconds=0)
        report["warnings"].append("No speech-strength frames above -45 dBFS")
    if duration < 0.5:
        report["warnings"].append("Duration below 0.5 s")
    if report["sample_rate"] != 24000 or report["channels"] != 1:
        report["warnings"].append("Unexpected source sample rate/channels (expected 24000 Hz mono)")
    if report["clipping_fraction"] > 0.0001:
        report["warnings"].append("Potential clipping: >0.01% samples at full scale")
    if report["leading_silence_seconds"] > 1.0 or report["trailing_silence_seconds"] > 1.5:
        report["warnings"].append("Long leading/trailing silence")
    if db(peak) < -25:
        report["warnings"].append("Very low peak level")
    # 40 ms Hann-window autocorrelation, coarse 60-450 Hz range.
    # Drama emotion and Mandarin tones legitimately move pitch; octave errors exist.
    # Do not use these estimates to certify same-character voice consistency.
    pitches = []
    window = 960
    taper = np.hanning(window)
    min_lag, max_lag = 53, 400
    for start in range(0, len(x) - window + 1, hop):
        frame = x[start:start + window]
        if np.sqrt(np.mean(frame ** 2)) < 10 ** (-40 / 20):
            continue
        y = (frame - np.mean(frame)) * taper
        corr = np.correlate(y, y, mode="full")[window - 1:]
        if corr[0] <= 0:
            continue
        # Prefer the first substantial local peak to reduce common octave errors.
        segment = corr[min_lag:max_lag + 1] / corr[0]
        local = np.flatnonzero((segment[1:-1] > segment[:-2]) & (segment[1:-1] >= segment[2:])) + 1
        plausible = local[segment[local] >= 0.40]
        if not len(plausible):
            continue
        best = plausible[np.argmax(segment[plausible])]
        near_best = plausible[segment[plausible] >= segment[best] * 0.90]
        lag = int(near_best[0] + min_lag)
        pitches.append(24000 / lag)
    if pitches:
        p = np.array(pitches)
        report.update(coarse_pitch_hz={"p10": round(float(np.percentile(p, 10)), 1),
                                       "median": round(float(np.median(p)), 1),
                                       "p90": round(float(np.percentile(p, 90)), 1)},
                      coarse_pitch_frames=len(pitches))
    report["content_verification"] = "Not verified by this tool; this script does not execute ASR"
    report["voice_identity_verification"] = "Not verified by this tool; pitch is supporting evidence only"
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    paths = []
    for item in args.paths:
        p = Path(item)
        paths.extend(sorted(p.rglob("*.wav")) if p.is_dir() else [p])
    paths = list(dict.fromkeys(paths))
    result = {"files_count": len(paths), "files": [analyze(p) for p in paths]}
    output = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output + "\n")
    print(output)


if __name__ == "__main__":
    main()
