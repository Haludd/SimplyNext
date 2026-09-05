class FaceLandmark {
  const FaceLandmark({
    required this.index,
    required this.x,
    required this.y,
    required this.z,
    this.visibility = 1,
  });

  final int index;
  final double x;
  final double y;
  final double z;
  final double visibility;

  Map<String, dynamic> toJson() => <String, dynamic>{
    'index': index,
    'x': x,
    'y': y,
    'z': z,
    'visibility': visibility,
  };

  factory FaceLandmark.fromJson(Map<String, dynamic> json) => FaceLandmark(
    index: (json['index'] as num?)?.toInt() ?? 0,
    x: (json['x'] as num).toDouble(),
    y: (json['y'] as num).toDouble(),
    z: (json['z'] as num?)?.toDouble() ?? 0,
    visibility: (json['visibility'] as num?)?.toDouble() ?? 1,
  );
}

class FaceExpressionFeatures {
  const FaceExpressionFeatures({
    required this.confidence,
    required this.label,
    required this.smile,
    required this.frown,
    required this.browRaise,
    required this.browFurrow,
    required this.eyeWide,
    required this.jawOpen,
    required this.mouthPucker,
    required this.landmarks,
    required this.blendshapes,
  });

  final double confidence;
  final String label;
  final double smile;
  final double frown;
  final double browRaise;
  final double browFurrow;
  final double eyeWide;
  final double jawOpen;
  final double mouthPucker;
  final List<FaceLandmark> landmarks;
  final Map<String, double> blendshapes;

  bool get isVisible => confidence >= .5 && landmarks.isNotEmpty;

  Map<String, dynamic> toJson() => <String, dynamic>{
    'confidence': confidence,
    'label': label,
    'smile': smile,
    'frown': frown,
    'brow_raise': browRaise,
    'brow_furrow': browFurrow,
    'eye_wide': eyeWide,
    'jaw_open': jawOpen,
    'mouth_pucker': mouthPucker,
    'landmarks': landmarks.map((landmark) => landmark.toJson()).toList(),
    'blendshapes': blendshapes,
  };

  factory FaceExpressionFeatures.fromJson(Map<String, dynamic> json) {
    final rawBlendshapes = json['blendshapes'] as Map<dynamic, dynamic>?;
    final blendshapes = <String, double>{};
    rawBlendshapes?.forEach((key, value) {
      if (value is num) blendshapes[key.toString()] = value.toDouble();
    });
    return FaceExpressionFeatures(
      confidence: (json['confidence'] as num?)?.toDouble() ?? 0,
      label: json['label'] as String? ?? 'not detected',
      smile: (json['smile'] as num?)?.toDouble() ?? 0,
      frown: (json['frown'] as num?)?.toDouble() ?? 0,
      browRaise: (json['brow_raise'] as num?)?.toDouble() ?? 0,
      browFurrow: (json['brow_furrow'] as num?)?.toDouble() ?? 0,
      eyeWide: (json['eye_wide'] as num?)?.toDouble() ?? 0,
      jawOpen: (json['jaw_open'] as num?)?.toDouble() ?? 0,
      mouthPucker: (json['mouth_pucker'] as num?)?.toDouble() ?? 0,
      landmarks: (json['landmarks'] as List<dynamic>? ?? <dynamic>[])
          .map((value) => FaceLandmark.fromJson(value as Map<String, dynamic>))
          .toList(growable: false),
      blendshapes: blendshapes,
    );
  }
}
