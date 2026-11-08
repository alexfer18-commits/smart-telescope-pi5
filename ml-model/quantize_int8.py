#!/usr/bin/env python3
"""Post-training static INT8 quantization of the star detector.

    python ml-model/quantize_int8.py model.onnx model_int8.onnx \
        --calibration data/calibration_frames --samples 300

Calibration frames are 8-bit grayscale PNG/FITS crops. The calibration reader
feeds them in the model's declared input layout; if the graph expects a
different size the frames are resized, because a calibration set that silently
mismatches the input shape produces a model that quantizes perfectly and
predicts nothing.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np


def load_frame(path: Path, height: int, width: int) -> np.ndarray:
    if path.suffix.lower() in {".fits", ".fit"}:
        from astropy.io import fits
        data = fits.getdata(path).astype(np.float32)
        data -= data.min()
        data /= max(data.max(), 1e-6)
        image = (data * 255).astype(np.uint8)
    else:
        import cv2
        image = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
        if image is None:
            raise ValueError(f"cannot read {path}")
    import cv2
    image = cv2.resize(image, (width, height), interpolation=cv2.INTER_AREA)
    return image[None, ..., None].astype(np.float32) / 255.0


def make_reader(frames: list[Path], height: int, width: int):
    def reader() -> np.ndarray:
        for frame in frames:
            yield load_frame(frame, height, width)
    return reader


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--calibration", type=Path, required=True)
    parser.add_argument("--samples", type=int, default=300)
    parser.add_argument("--per-channel", action="store_true",
                        help="quantize activations per channel (slower, more accurate)")
    args = parser.parse_args()

    from onnxruntime.quantization import (CalibrationDataReader, CalibrationMethod,
                                          QuantFormat, QuantType, quantize_static)

    import onnxruntime as ort
    session = ort.InferenceSession(str(args.model), providers=["CPUExecutionProvider"])
    shape = session.get_inputs()[0].shape
    height, width = (int(shape[1]), int(shape[2]))

    patterns = ("*.png", "*.jpg", "*.jpeg", "*.fits", "*.fit")
    frames = sorted(p for pattern in patterns
                    for p in args.calibration.glob(pattern))[: args.samples]
    if not frames:
        raise SystemExit(f"no calibration frames under {args.calibration}")

    class Reader(CalibrationDataReader):
        def __init__(self) -> None:
            self._it = make_reader(frames, height, width)()
            self._name = session.get_inputs()[0].name

        def get_next(self):
            try:
                return {self._name: next(self._it)}
            except StopIteration:
                return None

    quantize_static(
        model_input=str(args.model),
        model_output=str(args.output),
        calibration_data_reader=Reader(),
        quant_format=QuantFormat.QDQ,
        per_channel=args.per_channel,
        activation_type=QuantType.QInt8,
        weight_type=QuantType.QInt8,
        calibrate_method=CalibrationMethod.MinMax,
    )
    print(f"wrote {args.output} from {len(frames)} calibration frames "
          f"at {width}x{height}")


if __name__ == "__main__":
    main()
