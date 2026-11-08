# ML model

The solver's first stage is a star detector: a per-pixel star probability map
from which centroids are recovered. Everything here is about getting that model
from a training checkpoint onto three different substrates without changing
its behaviour.

## Backbones

| Variant | Why | Params | Where it runs |
|---|---|---|---|
| MobileNetV3-Small (U-Net decoder) | depthwise-separable ops map cleanly onto both CPU and the Hailo operator set | 1.5 M | all three substrates |
| Distilled transformer encoder | tests the reported weakness of vision NPUs on attention ops | 2.1 M | all three substrates |

The transformer is not decoration. The edge-AI literature reports that
transformer operators are where NPUs degrade, so if it holds here the negative
result is reportable; if it does not, the accelerator's applicability is wider
than expected.

## Pipeline

```bash
# 1. train on synthetic Gaia-rendered fields (see experiments/README.md)
python train.py --backbone mobilenetv3_small --out checkpoints/mnv3.ckpt

# 2. export to ONNX (opset 17, static shapes) — from the training script
python -c "
import torch
m = torch.load('checkpoints/mnv3.ckpt', map_location='cpu').eval()
torch.onnx.export(m, torch.zeros(1, 1, 256, 256), 'ml-model/mnv3.onnx',
                  opset_version=17, input_names=['image'], output_names=['prob'])
"

# 3. quantize to INT8 with a calibration set drawn from real and synthetic frames
python ml-model/quantize_int8.py ml-model/mnv3.onnx ml-model/mnv3_int8.onnx \
    --calibration data/calibration_frames --samples 300

# 4. compile for the accelerator (needs the Hailo Dataflow Compiler, x86 host)
hailo compiler --hw-arch hailo8l --input ml-model/mnv3_int8.onnx \
               --output ml-model/mnv3.hef

# 5. benchmark the three substrates
python benchmarks/compare_inference.py --model ml-model/mnv3_int8.onnx --episodes 300
```

## Calibration is not accuracy

`quantize_int8.py` selects its calibration set by minimising the 95th percentile
of *angular* error after solving, not by minimising a classification metric.
That is the deliberate departure from standard practice described in the
proposal: the quantity that matters is arcminutes of pointing, and a model with
a slightly worse probability map can produce a better centroid.

Verify the export did not change behaviour before benchmarking:

```bash
python ml-model/check_equivalence.py ml-model/mnv3.onnx ml-model/mnv3_int8.onnx
```

It reports the maximum centroid displacement between the FP32 and INT8 graphs on
the calibration frames, in pixels and arcseconds. Anything above 0.2 px is a
quantization problem, not a tuning problem.
