# Frontend segmentation/classifier test kit

This folder is a small, synthetic test kit for the frontend landmark stream.
It does not change the Flutter app or the backend implementation.

The sample contains two moving hand bursts with a pause between them. The
runner also adds the same shoulder-centred 3D `normalized_coordinates` shape
emitted by the Flutter stage-3 normalizer, then sends the sample through both
segmentation arms and prints the feature windows and top-k classifier
candidates.

From the repository root, run:

```bash
python3 frontend_segment_classify/run_test.py
```

To try one arm at a time:

```bash
python3 frontend_segment_classify/run_test.py --arm geometry_hysteresis
python3 frontend_segment_classify/run_test.py --arm sliding_window_blank
```

This is synthetic data, so it checks the pipeline wiring and boundary logic;
it is not real ASL training data and will not measure recognition accuracy.

The positions are stored in [sample_positions.json](sample_positions.json).
The runner expands each wrist position into a valid 21-landmark hand before
calling the existing analyzer.

The versioned hand-off schema is in
[schema/processing_contracts.schema.json](schema/processing_contracts.schema.json):

```text
LandmarkFrame
  -> FeatureWindow + BoundaryEvent
  -> top-k gloss scores
  -> GlossLattice
```

The normalized `LandmarkFrame` groups shoulders, arms, pose, hands, and facial
expression data. The `GlossLattice` contains only compact classifier evidence;
it deliberately does not contain the normalized landmark arrays.
