import {
  FilesetResolver,
  FaceLandmarker,
  HandLandmarker,
  PoseLandmarker,
} from 'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.35/vision_bundle.mjs';

const WASM_ROOT =
  'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.35/wasm';
const MODEL_URL =
  'https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task';
const POSE_MODEL_URL =
  'https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task';
const FACE_MODEL_URL =
  'https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task';

// These are the useful upper-body points from MediaPipe Pose. The model still
// sees the complete pose internally; only this small, stable subset crosses
// the application boundary.
const POSE_LANDMARKS = [
  [0, 'nose'],
  [11, 'left_shoulder'],
  [12, 'right_shoulder'],
  [13, 'left_elbow'],
  [14, 'right_elbow'],
  [15, 'left_wrist'],
  [16, 'right_wrist'],
  [23, 'left_hip'],
  [24, 'right_hip'],
  [25, 'left_knee'],
  [26, 'right_knee'],
];

// Face Mesh indices for the upper-face and mouth regions. The remaining face
// mesh points stay inside MediaPipe and are deliberately not sent to the
// classifier.
const FACE_UPPER_LANDMARKS = [
  [33, 'left_eye_outer'],
  [133, 'left_eye_inner'],
  [160, 'left_eye_upper'],
  [159, 'left_eye_center_upper'],
  [158, 'left_eye_center_lower'],
  [157, 'left_eye_lower'],
  [173, 'left_eye_inner_lower'],
  [362, 'right_eye_outer'],
  [263, 'right_eye_inner'],
  [387, 'right_eye_upper'],
  [386, 'right_eye_center_upper'],
  [385, 'right_eye_center_lower'],
  [384, 'right_eye_lower'],
  [398, 'right_eye_inner_lower'],
  [70, 'left_brow_outer'],
  [63, 'left_brow_inner'],
  [105, 'left_brow_center'],
  [66, 'left_brow_upper'],
  [107, 'left_brow_lower'],
  [336, 'right_brow_outer'],
  [296, 'right_brow_inner'],
  [334, 'right_brow_center'],
  [293, 'right_brow_upper'],
  [300, 'right_brow_lower'],
];

const FACE_MOUTH_LANDMARKS = [
  [61, 'mouth_left'],
  [291, 'mouth_right'],
  [0, 'mouth_top_center'],
  [17, 'mouth_bottom_center'],
  [13, 'upper_lip_center'],
  [14, 'lower_lip_center'],
  [78, 'mouth_left_inner'],
  [308, 'mouth_right_inner'],
  [82, 'upper_lip_left'],
  [312, 'upper_lip_right'],
  [95, 'lower_lip_left'],
  [324, 'lower_lip_right'],
];
const queryBackendEnabled = new URLSearchParams(globalThis.location.search).get(
  'backend',
) === '1';
const BACKEND_ENABLED =
  globalThis.signBridgeEnableBackend === true || queryBackendEnabled;
const configuredDeepFaceUrl = globalThis.signBridgeDeepFaceUrl;
const queryDeepFaceUrl = new URLSearchParams(globalThis.location.search).get(
  'deepface_api',
);
const DEEPFACE_API_URL =
  BACKEND_ENABLED
    ? configuredDeepFaceUrl ||
      queryDeepFaceUrl ||
      'http://127.0.0.1:8000/v1/emotions/analyze'
    : '';
const DEEPFACE_INTERVAL_MS = 1200;
const configuredTrackingWebSocketUrl =
  globalThis.signBridgeTrackingWebSocketUrl;
const queryTrackingWebSocketUrl = new URLSearchParams(
  globalThis.location.search,
).get('tracking_ws');
const TRACKING_WEBSOCKET_URL =
  BACKEND_ENABLED
    ? configuredTrackingWebSocketUrl ||
      queryTrackingWebSocketUrl ||
      'ws://127.0.0.1:8001/v1/tracking'
    : '';
const TRACKING_CHUNK_INTERVAL_MS = 1000;
const TRACKING_MAX_BUFFERED_FRAMES = 120;
const TRACKING_MAX_FRAMES_PER_CHUNK = 36;
const TRACKING_MAX_SOCKET_BUFFER_BYTES = 2_000_000;
const queryTrackingFps = Number(
  new URLSearchParams(globalThis.location.search).get('tracking_fps'),
);
const TRACKING_FPS = Number.isFinite(queryTrackingFps)
  ? Math.min(60, Math.max(30, queryTrackingFps))
  : 30;
const DETECTION_INTERVAL_MS = 1000 / TRACKING_FPS;
const FACE_DETECTION_INTERVAL_MS = 1000 / Math.min(20, TRACKING_FPS);
const SUBJECT_MATCH_DISTANCE = 0.32;
const SUBJECT_FACE_MATCH_DISTANCE = 0.25;
const SUBJECT_ACQUIRE_STABLE_FRAMES = 12;
// Use torso/head points for identity matching. Wrists and elbows are omitted
// because they are expected to move quickly during signing.
const SUBJECT_ANCHOR_INDICES = [0, 11, 12, 23, 24];

let handLandmarker;
let poseLandmarker;
let faceLandmarker;
let video;
let stream;
let animationFrame;
let started = false;
let deepFaceEmotion;
let deepFaceRequestInFlight = false;
let lastDeepFaceRequestAt = 0;
let deepFaceWarningShown = false;
let deepFaceSubjectGeneration = 0;
let emotionCanvas;
let emotionContext;
let trackingSocket;
let trackingSocketReconnectTimer;
let trackingSocketSessionId;
let trackingSocketFrameCount = 0;
let trackingSocketChunkCount = 0;
let trackingSocketWarningShown = false;
let trackingUtteranceId;
let trackingChunkSequence = 0;
let trackingChunkFrames = [];
let trackingChunkStartedAt = 0;
let lastProcessedAt = 0;
let detectionInProgress = false;
let trackingFrameErrorShown = false;
let trackingLoopFrameCount = 0;
let trackingLoopStartedAt = 0;
let trackingLoopLastLogAt = 0;
let lastFaceResult;
let lastFaceProcessedAt = 0;
let previousHandMotion = {
  left: null,
  right: null,
};
let previousMotionTimestamp;
let subjectTrack;
let subjectAcquire;

function cameraElements() {
  return Array.from(
    document.querySelectorAll('[data-signbridge-camera]'),
  );
}

function isVisibleCameraElement(element) {
  const style = globalThis.getComputedStyle(element);
  const rect = element.getBoundingClientRect();
  return (
    style.display !== 'none' &&
    style.visibility !== 'hidden' &&
    style.opacity !== '0' &&
    rect.width > 0 &&
    rect.height > 0
  );
}

function visibleCameraElement() {
  const elements = cameraElements();
  return (
    elements.find((element) => isVisibleCameraElement(element)) ||
    elements[0]
  );
}

function syncVisibleCameraElement() {
  if (!stream) return;
  const nextVideo = visibleCameraElement();
  if (!nextVideo || nextVideo === video) return;

  if (video) video.srcObject = null;
  video = nextVideo;
  video.srcObject = stream;
  video.muted = true;
  video.playsInline = true;
  void video.play().catch((error) => {
    console.warn('Unable to resume the visible camera preview.', error);
  });
}

function posePointToJson(point, index, name) {
  if (!point) return null;
  return {
    index,
    name,
    x: point.x,
    y: point.y,
    z: point.z ?? 0,
    visibility: point.visibility ?? point.presence ?? 0,
    presence: point.presence ?? point.visibility ?? 0,
  };
}

function facePointToJson(point, index, name) {
  if (!point) return null;
  return {
    index,
    name,
    x: point.x,
    y: point.y,
    z: point.z ?? 0,
    visibility: 1,
  };
}

function curatedLandmarks(allLandmarks, definitions, converter) {
  return definitions
    .map(([index, name]) => converter(allLandmarks[index], index, name))
    .filter((point) => point !== null);
}

function poseCandidate(landmarks) {
  const visible = landmarks.filter(
    (point) => (point.visibility ?? point.presence ?? 0) >= 0.35,
  );
  if (visible.length < 4) return null;
  const xs = visible.map((point) => point.x);
  const ys = visible.map((point) => point.y);
  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);
  const centerX = (minX + maxX) / 2;
  const centerY = (minY + maxY) / 2;
  const area = Math.max(0.04, maxX - minX) * Math.max(0.08, maxY - minY);
  const centrality = Math.max(
    0,
    1 - Math.hypot(centerX - 0.5, centerY - 0.5) / 0.71,
  );
  const nose = landmarks[0];
  return {
    landmarks,
    minX,
    maxX,
    minY,
    maxY,
    centerX,
    centerY,
    faceX: nose?.x ?? centerX,
    faceY: nose?.y ?? Math.max(0, centerY - 0.25),
    area,
    score: area * (0.65 + centrality * 0.35),
    anchors: SUBJECT_ANCHOR_INDICES.map((index) => {
      const point = landmarks[index];
      return point &&
        (point.visibility ?? point.presence ?? 0) >= 0.35
        ? {index, x: point.x, y: point.y}
        : null;
    }).filter((point) => point !== null),
  };
}

function lockSubject(candidate) {
  subjectTrack = {
    ...candidate,
    locked: true,
    visible: true,
    missingFrames: 0,
  };
  return subjectTrack;
}

function anchorDistance(first, second) {
  const firstAnchors = first?.anchors ?? [];
  const secondAnchors = second?.anchors ?? [];
  const distances = [];
  for (const previous of firstAnchors) {
    const current = secondAnchors.find((point) => point.index === previous.index);
    if (!current) continue;
    distances.push(Math.hypot(current.x - previous.x, current.y - previous.y));
  }
  if (distances.length < 3) return Number.POSITIVE_INFINITY;
  return distances.reduce((sum, distance) => sum + distance, 0) / distances.length;
}

function acquireStableSubject(candidates) {
  const candidate = candidates[0];
  if (!subjectAcquire) {
    subjectAcquire = {
      ...candidate,
      stableFrames: 1,
    };
  } else {
    const centerDistance = Math.hypot(
      candidate.centerX - subjectAcquire.centerX,
      candidate.centerY - subjectAcquire.centerY,
    );
    const bodyDistance = anchorDistance(candidate, subjectAcquire);
    if (centerDistance <= 0.18 && bodyDistance <= 0.16) {
      subjectAcquire = {
        ...candidate,
        stableFrames: subjectAcquire.stableFrames + 1,
      };
    } else {
      // A different person or an unstable detection appeared before the lock.
      // Start the acquisition window again instead of choosing immediately.
      subjectAcquire = {
        ...candidate,
        stableFrames: 1,
      };
    }
  }

  if (subjectAcquire.stableFrames < SUBJECT_ACQUIRE_STABLE_FRAMES) {
    return null;
  }
  const locked = lockSubject(subjectAcquire);
  subjectAcquire = null;
  return locked;
}

function holdLockedSubject() {
  if (!subjectTrack) return null;
  subjectTrack = {
    ...subjectTrack,
    // Keep the lock identity, but do not reuse stale landmarks as current
    // data. This prevents a new person from being accepted after an occlusion.
    visible: false,
    // Keep counting for diagnostics, but never expire the lock. This allows
    // the original subject to recover after a longer occlusion.
    missingFrames: Math.min(10_000, subjectTrack.missingFrames + 1),
  };
  return subjectTrack;
}

function subjectMatchScore(candidate) {
  if (!subjectTrack) return Number.POSITIVE_INFINITY;
  const centerDistance = Math.hypot(
    candidate.centerX - subjectTrack.centerX,
    candidate.centerY - subjectTrack.centerY,
  );
  if (centerDistance > SUBJECT_MATCH_DISTANCE) return Number.POSITIVE_INFINITY;

  const previousAnchors = subjectTrack.anchors ?? [];
  const currentAnchors = candidate.anchors ?? [];
  const distances = [];
  for (const previous of previousAnchors) {
    const current = currentAnchors.find((point) => point.index === previous.index);
    if (!current) continue;
    distances.push(Math.hypot(current.x - previous.x, current.y - previous.y));
  }
  // A body-anchor match makes a nearby newcomer much less likely to replace
  // the locked signer when MediaPipe briefly loses one pose.
  if (distances.length < 3) return Number.POSITIVE_INFINITY;
  const averageDistance =
    distances.reduce((sum, distance) => sum + distance, 0) / distances.length;
  if (averageDistance > 0.14 || Math.max(...distances) > 0.28) {
    return Number.POSITIVE_INFINITY;
  }
  // Lower is a better continuation of the locked subject. This lets the
  // tracker choose the correct candidate even if another person is closer to
  // the old centre for one frame.
  return averageDistance + centerDistance * 0.35;
}

function selectSubjectPose(poseResult) {
  const candidates = (poseResult?.landmarks ?? [])
    .map(poseCandidate)
    .filter((candidate) => candidate !== null);
  candidates.sort((first, second) => second.score - first.score);
  if (candidates.length === 0) {
    // A subject lock lasts until the tracking session is stopped/restarted.
    // Do not promote a person who enters later to the active subject.
    return holdLockedSubject();
  }

  // The first stable subject becomes the lock. Waiting for several consistent
  // frames avoids choosing a transient detection during camera startup.
  if (!subjectTrack) return acquireStableSubject(candidates);

  const match = candidates
    .map((candidate) => ({
      candidate,
      score: subjectMatchScore(candidate),
    }))
    .filter((entry) => Number.isFinite(entry.score))
    .sort((first, second) => first.score - second.score)[0];
  if (match) {
    return lockSubject(match.candidate);
  }

  // No candidate is close enough to the locked subject. Keep the lock and
  // ignore every other person, even if they are larger or more central.
  return holdLockedSubject();
}

function selectSubjectFace(faceResult, subject) {
  const candidates = faceResult?.faceLandmarks ?? [];
  if (candidates.length === 0 || !subject || subject.visible === false) return [];
  const targetX = subject?.faceX ?? 0.5;
  const targetY = subject?.faceY ?? 0.35;
  const nearest = candidates.reduce((best, candidate) => {
    const points = candidate.filter((point) => point != null);
    if (points.length === 0) return best;
    const centerX = points.reduce((sum, point) => sum + point.x, 0) / points.length;
    const centerY = points.reduce((sum, point) => sum + point.y, 0) / points.length;
    const distance = Math.hypot(centerX - targetX, centerY - targetY);
    if (!best || distance < best.distance) return {points, distance};
    return best;
  }, null);
  return nearest && nearest.distance <= SUBJECT_FACE_MATCH_DISTANCE
    ? nearest.points
    : [];
}

function handBelongsToSubject(hand, subject) {
  // Do not emit hands before the pose lock exists. Otherwise another person's
  // hands could enter the stream during the few frames before pose detection.
  if (!subject || subject.visible === false || !hand?.landmarks?.[0]) return false;
  const wrist = hand.landmarks[0];
  const poseWristIndex = hand.handedness === 'left' ? 15 : 16;
  const poseWrist = subject.landmarks?.[poseWristIndex];
  if ((poseWrist?.visibility ?? 0) >= 0.35) {
    // MediaPipe pose wrists are the strongest available association between
    // a detected hand and the locked person's body. Allow signing movement,
    // but do not use the old very-wide box that admitted nearby people.
    const wristDistance = Math.hypot(
      wrist.x - poseWrist.x,
      wrist.y - poseWrist.y,
    );
    const subjectWidth = Math.max(0.12, subject.maxX - subject.minX);
    return wristDistance <= Math.max(0.2, subjectWidth * 0.75);
  }

  const subjectWidth = Math.max(0.12, subject.maxX - subject.minX);
  const subjectHeight = Math.max(0.2, subject.maxY - subject.minY);
  const marginX = Math.max(0.1, subjectWidth * 0.25);
  const marginY = Math.max(0.12, subjectHeight * 0.15);
  return (
    wrist.x >= subject.minX - marginX &&
    wrist.x <= subject.maxX + marginX &&
    wrist.y >= subject.minY - marginY &&
    wrist.y <= subject.maxY + marginY
  );
}

function motionDirection(dx, dy) {
  if (Math.abs(dx) < 0.01 && Math.abs(dy) < 0.01) return 'still';
  if (Math.abs(dx) > Math.abs(dy)) return dx > 0 ? 'right' : 'left';
  return dy > 0 ? 'down' : 'up';
}

function mostCommon(values) {
  if (values.length === 0) return 'still';
  const counts = {};
  for (const value of values) counts[value] = (counts[value] ?? 0) + 1;
  return Object.entries(counts).reduce((best, current) =>
    current[1] > best[1] ? current : best,
  )[0];
}

function calculateMotion(hands, timestampMs) {
  const elapsedSeconds = previousMotionTimestamp
    ? Math.max(0.016, (timestampMs - previousMotionTimestamp) / 1000)
    : 0.016;
  previousMotionTimestamp = timestampMs;
  const speeds = [];
  const accelerations = [];
  const directions = [];
  const perHand = {};
  const seen = new Set();

  for (const side of ['left', 'right']) {
    const hand = hands.find((candidate) => candidate.handedness === side);
    const wrist = hand?.landmarks?.[0];
    if (!wrist) {
      previousHandMotion[side] = null;
      continue;
    }
    seen.add(side);
    const previous = previousHandMotion[side];
    let velocity = 0;
    let acceleration = 0;
    let direction = 'still';
    if (previous) {
      const dx = wrist.x - previous.x;
      const dy = wrist.y - previous.y;
      const dz = (wrist.z ?? 0) - previous.z;
      velocity = Math.sqrt(dx * dx + dy * dy + dz * dz) / elapsedSeconds;
      acceleration = Math.abs(velocity - previous.velocity) / elapsedSeconds;
      direction = motionDirection(dx, dy);
      directions.push(direction);
    }
    speeds.push(velocity);
    accelerations.push(acceleration);
    perHand[side] = {velocity, acceleration, direction};
    previousHandMotion[side] = {
      x: wrist.x,
      y: wrist.y,
      z: wrist.z ?? 0,
      velocity,
    };
  }

  return {
    average_speed: speeds.length
      ? speeds.reduce((sum, value) => sum + value, 0) / speeds.length
      : 0,
    average_velocity: speeds.length
      ? speeds.reduce((sum, value) => sum + value, 0) / speeds.length
      : 0,
    peak_velocity: speeds.length ? Math.max(...speeds) : 0,
    average_acceleration: accelerations.length
      ? accelerations.reduce((sum, value) => sum + value, 0) / accelerations.length
      : 0,
    peak_acceleration: accelerations.length ? Math.max(...accelerations) : 0,
    direction: mostCommon(directions),
    per_hand: perHand,
    tracked_hands: seen.size,
  };
}

function wireFrameFromFrame(frame) {
  return {
    timestamp: new Date(frame.timestamp_ms).toISOString(),
    tracking_confidence: frame.processing_confidence,
    hands: frame.hands,
    face_expression: frame.face
      ? {
          label: frame.face.label,
          confidence: frame.face.confidence,
          emotion_scores: frame.face.emotion_scores,
        }
      : null,
    left_shoulder: frame.left_shoulder,
    right_shoulder: frame.right_shoulder,
    landmark_worlds: frame.landmark_worlds,
    hand_motion: frame.hand_motion,
    subject_tracking: frame.subject_tracking,
  };
}

function summarizeChunk(frames) {
  const motions = frames
    .map((frame) => frame.hand_motion)
    .filter((motion) => motion != null);
  const average = (values) =>
    values.length
      ? values.reduce((sum, value) => sum + Number(value || 0), 0) / values.length
      : 0;
  const speeds = motions.map((motion) => motion.average_velocity ?? motion.average_speed ?? 0);
  const accelerations = motions.map((motion) => motion.average_acceleration ?? 0);
  const directions = motions.map((motion) => motion.direction ?? 'still');
  const perHand = {};
  for (const side of ['left', 'right']) {
    const values = motions
      .map((motion) => motion.per_hand?.[side])
      .filter((motion) => motion != null);
    const sideSpeeds = values.map((motion) => motion.velocity ?? 0);
    const sideAccelerations = values.map((motion) => motion.acceleration ?? 0);
    perHand[side] = {
      average_velocity: average(sideSpeeds),
      peak_velocity: sideSpeeds.length ? Math.max(...sideSpeeds) : 0,
      average_acceleration: average(sideAccelerations),
      peak_acceleration: sideAccelerations.length
        ? Math.max(...sideAccelerations)
        : 0,
    };
  }
  return {
    frame_count: frames.length,
    average_velocity: average(speeds),
    peak_velocity: speeds.length ? Math.max(...speeds) : 0,
    average_acceleration: average(accelerations),
    peak_acceleration: accelerations.length ? Math.max(...accelerations) : 0,
    direction: mostCommon(directions),
    per_hand: perHand,
  };
}

function beginUtterance() {
  trackingUtteranceId = `utterance-${Date.now()}`;
  trackingChunkSequence = 0;
  trackingChunkFrames = [];
  trackingChunkStartedAt = 0;
  previousHandMotion = {left: null, right: null};
  previousMotionTimestamp = null;
}

function sendUtteranceStart() {
  if (!trackingSocket || trackingSocket.readyState !== WebSocket.OPEN) return;
  trackingSocket.send(
    JSON.stringify({
      type: 'utterance_start',
      session_id: trackingSocketSessionId,
      utterance_id: trackingUtteranceId,
    }),
  );
}

function sendTrackingChunk(force = false) {
  if (
    !trackingSocket ||
    trackingSocket.readyState !== WebSocket.OPEN ||
    trackingChunkFrames.length === 0 ||
    trackingSocket.bufferedAmount > TRACKING_MAX_SOCKET_BUFFER_BYTES
  ) {
    return false;
  }
  const entries = trackingChunkFrames.slice(
    0,
    TRACKING_MAX_FRAMES_PER_CHUNK,
  );
  const latestQueued = trackingChunkFrames[trackingChunkFrames.length - 1];
  if (
    !force &&
    latestQueued.timestamp_ms - trackingChunkFrames[0].timestamp_ms <
      TRACKING_CHUNK_INTERVAL_MS
  ) {
    return false;
  }
  const latest = entries[entries.length - 1];
  const frames = entries.map((entry) => entry.wire);
  const startedAt = new Date(entries[0].timestamp_ms).toISOString();
  const endedAt = new Date(latest.timestamp_ms).toISOString();
  const chunk = {
    type: 'chunk',
    session_id: trackingSocketSessionId,
    utterance_id: trackingUtteranceId,
    chunk_id: `${trackingUtteranceId}-chunk-${++trackingChunkSequence}`,
    started_at: startedAt,
    ended_at: endedAt,
    frame_count: frames.length,
    frames,
    features: summarizeChunk(entries.map((entry) => entry.frame)),
  };
  try {
    trackingSocket.send(JSON.stringify(chunk));
    trackingSocketFrameCount += frames.length;
    trackingSocketChunkCount += 1;
    trackingChunkFrames.splice(0, entries.length);
    trackingChunkStartedAt = trackingChunkFrames.length
      ? trackingChunkFrames[0].timestamp_ms
      : 0;
    return true;
  } catch (error) {
    console.warn('Unable to send tracking chunk over WebSocket.', error);
    return false;
  }
}

function flushTrackingChunks() {
  // The pending queue is bounded, so flushing it cannot grow memory without
  // limit after a reconnect or a short backend outage.
  let attempts = 0;
  while (
    trackingChunkFrames.length > 0 &&
    attempts < 10 &&
    sendTrackingChunk(true)
  ) {
    attempts += 1;
  }
}

function queueTrackingFrame(frame) {
  if (!BACKEND_ENABLED) return;
  if (!trackingChunkStartedAt) trackingChunkStartedAt = frame.timestamp_ms;
  trackingChunkFrames.push({
    timestamp_ms: frame.timestamp_ms,
    frame,
    wire: wireFrameFromFrame(frame),
  });
  if (trackingChunkFrames.length > TRACKING_MAX_BUFFERED_FRAMES) {
    const dropped =
      trackingChunkFrames.length - TRACKING_MAX_BUFFERED_FRAMES;
    trackingChunkFrames.splice(0, dropped);
    trackingChunkStartedAt = trackingChunkFrames[0]?.timestamp_ms ?? 0;
    if (!trackingSocketWarningShown) {
      console.warn(
        'Tracking WebSocket is behind; dropping old unsent frames to keep capture continuous.',
      );
      trackingSocketWarningShown = true;
    }
  }
  // Chunks, rather than individual frames, are the transport unit for live
  // utterance analysis. Flutter still receives every browser event locally so
  // the overlay remains smooth.
  sendTrackingChunk(false);
}

function subjectFaceCrop(faceLandmarks, subject, sourceWidth, sourceHeight) {
  const points = (faceLandmarks ?? []).filter((point) => point != null);
  let faceMinX;
  let faceMaxX;
  let faceMinY;
  let faceMaxY;
  if (points.length >= 4) {
    const xs = points.map((point) => point.x);
    const ys = points.map((point) => point.y);
    faceMinX = Math.max(0, Math.min(...xs));
    faceMaxX = Math.min(1, Math.max(...xs));
    faceMinY = Math.max(0, Math.min(...ys));
    faceMaxY = Math.min(1, Math.max(...ys));
  } else if (subject?.faceX != null && subject?.faceY != null) {
    // If the optional Face Landmarker is unavailable, use the locked pose's
    // nose as a subject-only crop rather than sending the whole camera frame.
    const estimatedWidth = Math.max(
      0.12,
      Math.min(0.5, (subject.maxX - subject.minX) * 0.45),
    );
    const estimatedHeight = estimatedWidth * 1.25;
    faceMinX = subject.faceX - estimatedWidth / 2;
    faceMaxX = subject.faceX + estimatedWidth / 2;
    faceMinY = subject.faceY - estimatedHeight * 0.42;
    faceMaxY = subject.faceY + estimatedHeight * 0.58;
  } else {
    return null;
  }
  const faceWidth = Math.max(0.02, faceMaxX - faceMinX);
  const faceHeight = Math.max(0.02, faceMaxY - faceMinY);
  const paddingX = Math.max(0.06, faceWidth * 0.45);
  const paddingY = Math.max(0.08, faceHeight * 0.65);
  const minX = Math.max(0, faceMinX - paddingX);
  const maxX = Math.min(1, faceMaxX + paddingX);
  const minY = Math.max(0, faceMinY - paddingY);
  const maxY = Math.min(1, faceMaxY + paddingY);
  return {
    x: minX * sourceWidth,
    y: minY * sourceHeight,
    width: Math.max(1, (maxX - minX) * sourceWidth),
    height: Math.max(1, (maxY - minY) * sourceHeight),
  };
}

async function requestDeepFaceEmotion(subject, faceLandmarks) {
  if (
    !DEEPFACE_API_URL ||
    !video ||
    video.readyState < 2 ||
    !subject ||
    subject.visible === false ||
    deepFaceRequestInFlight
  ) {
    return;
  }

  const now = performance.now();
  if (now - lastDeepFaceRequestAt < DEEPFACE_INTERVAL_MS) return;
  lastDeepFaceRequestAt = now;
  deepFaceRequestInFlight = true;
  const subjectGeneration = deepFaceSubjectGeneration;

  try {
    if (!emotionCanvas) {
      emotionCanvas = document.createElement('canvas');
      emotionContext = emotionCanvas.getContext('2d');
    }
    const sourceWidth = video.videoWidth || 640;
    const sourceHeight = video.videoHeight || 480;
    const crop = subjectFaceCrop(
      faceLandmarks,
      subject,
      sourceWidth,
      sourceHeight,
    );
    if (!crop) return;
    const scale = Math.min(1, 480 / crop.width);
    emotionCanvas.width = Math.max(1, Math.round(crop.width * scale));
    emotionCanvas.height = Math.max(1, Math.round(crop.height * scale));
    emotionContext.drawImage(
      video,
      crop.x,
      crop.y,
      crop.width,
      crop.height,
      0,
      0,
      emotionCanvas.width,
      emotionCanvas.height,
    );
    const blob = await new Promise((resolve) =>
      emotionCanvas.toBlob(resolve, 'image/jpeg', 0.68),
    );
    if (!blob) return;

    const controller = new AbortController();
    const requestTimeout = setTimeout(() => controller.abort(), 5000);
    let response;
    try {
      response = await fetch(DEEPFACE_API_URL, {
        method: 'POST',
        headers: {'Content-Type': 'image/jpeg'},
        body: blob,
        signal: controller.signal,
      });
    } finally {
      clearTimeout(requestTimeout);
    }
    if (!response.ok) {
      throw new Error(`DeepFace API returned ${response.status}`);
    }
    const payload = await response.json();
    if (subjectGeneration === deepFaceSubjectGeneration) {
      deepFaceEmotion = payload.status === 'ok' ? payload : null;
    }
  } catch (error) {
    // Hand and shoulder tracking remain available if the optional local
    // The local face-analysis service is not running or its dependencies are missing.
    if (!deepFaceWarningShown) {
      console.warn(
        'Face emotion API unavailable; face emotion will remain unavailable.',
        error,
      );
      deepFaceWarningShown = true;
    }
  } finally {
    deepFaceRequestInFlight = false;
  }
}

function deepFaceToJson(result) {
  if (!result || result.status !== 'ok') return null;
  const emotions = Object.fromEntries(
    Object.entries(result.emotions ?? {}).map(([label, score]) => [
      label.toLowerCase(),
      Number(score),
    ]),
  );
  return {
    source: result.source ?? 'face-model',
    confidence: Number(result.confidence ?? 0),
    label: result.dominant_emotion ?? 'not detected',
    landmarks: [],
    emotion_scores: emotions,
  };
}

function connectTrackingSocket() {
  if (
    !TRACKING_WEBSOCKET_URL ||
    typeof WebSocket === 'undefined' ||
    !started ||
    (trackingSocket &&
      (trackingSocket.readyState === WebSocket.CONNECTING ||
        trackingSocket.readyState === WebSocket.OPEN))
  ) {
    return;
  }

  trackingSocket = new WebSocket(TRACKING_WEBSOCKET_URL);
  trackingSocket.addEventListener('open', () => {
    trackingSocket.send(
      JSON.stringify({
        type: 'start',
        session_id: trackingSocketSessionId,
      }),
    );
    sendUtteranceStart();
    flushTrackingChunks();
    console.info('SignBridge utterance WebSocket connected.');
  });
  trackingSocket.addEventListener('message', (event) => {
    try {
      const message = JSON.parse(event.data);
      if (message.type === 'frame_ack' || message.type === 'chunk_ack') {
        trackingSocketFrameCount = message.frames_received ?? trackingSocketFrameCount;
        trackingSocketChunkCount = message.chunks_received ?? trackingSocketChunkCount;
      }
    } catch (_) {
      // Ignore non-JSON diagnostic messages from a compatible server.
    }
  });
  trackingSocket.addEventListener('error', (error) => {
    if (!trackingSocketWarningShown) {
      console.warn('Coordinate WebSocket unavailable.', error);
      trackingSocketWarningShown = true;
    }
  });
  trackingSocket.addEventListener('close', () => {
    trackingSocket = null;
    if (started) {
      clearTimeout(trackingSocketReconnectTimer);
      trackingSocketReconnectTimer = setTimeout(connectTrackingSocket, 2000);
    }
  });
}

function dispatchFrame(result, poseResult, faceResult, timestampMs) {
  const handednesses = result.handednesses ?? result.handedness ?? [];
  const allHands = (result.landmarks ?? []).map((landmarks, index) => {
    const category = handednesses[index]?.[0];
    const world = result.worldLandmarks?.[index] ?? [];
    return {
      handedness: category?.categoryName?.toLowerCase() ?? 'unknown',
      confidence: category?.score ?? 0,
      landmarks: landmarks.map((landmark, landmarkIndex) => ({
        x: landmark.x,
        y: landmark.y,
        z: landmark.z ?? 0,
        world_x: world[landmarkIndex]?.x,
        world_y: world[landmarkIndex]?.y,
        world_z: world[landmarkIndex]?.z,
        visibility: 1,
      })),
    };
  });
  const subject = selectSubjectPose(poseResult);
  const hands = allHands.filter((hand) => handBelongsToSubject(hand, subject));
  const leftHand = hands.find((hand) => hand.handedness === 'left');
  const rightHand = hands.find((hand) => hand.handedness === 'right');
  const pose = subject?.visible === false ? [] : subject?.landmarks ?? [];
  const poseLandmarks = curatedLandmarks(
    pose,
    POSE_LANDMARKS,
    posePointToJson,
  );
  const leftShoulder = posePointToJson(pose[11], 11, 'left_shoulder');
  const rightShoulder = posePointToJson(pose[12], 12, 'right_shoulder');
  const faceLandmarks = selectSubjectFace(faceResult, subject);
  const faceUpper = curatedLandmarks(
    faceLandmarks,
    FACE_UPPER_LANDMARKS,
    facePointToJson,
  );
  const faceMouth = curatedLandmarks(
    faceLandmarks,
    FACE_MOUTH_LANDMARKS,
    facePointToJson,
  );
  const hasShoulders =
    leftShoulder?.visibility >= 0.45 && rightShoulder?.visibility >= 0.45;
  if (subject?.visible !== true) {
    deepFaceSubjectGeneration += 1;
    deepFaceEmotion = null;
  }
  const face = deepFaceToJson(deepFaceEmotion);
  const handMotion = calculateMotion(hands, timestampMs);
  const subjectTracking = subject
    ? {
        locked: subject.locked === true,
        visible: subject.visible !== false,
        center_x: subject.visible === false ? null : subject.centerX,
        center_y: subject.visible === false ? null : subject.centerY,
        area: subject.visible === false ? 0 : subject.area,
        missing_frames: subject.missingFrames,
      }
    : {
        locked: false,
        center_x: null,
        center_y: null,
        area: 0,
        missing_frames: 0,
      };
  const landmarkWorlds = {
    left_hand: {
      handedness: 'left',
      confidence: leftHand?.confidence ?? 0,
      landmarks: (leftHand?.landmarks ?? []).map((landmark, index) => ({
        index,
        x: landmark.x,
        y: landmark.y,
        z: landmark.z ?? 0,
        world_x: landmark.world_x,
        world_y: landmark.world_y,
        world_z: landmark.world_z,
        visibility: landmark.visibility ?? 1,
      })),
    },
    right_hand: {
      handedness: 'right',
      confidence: rightHand?.confidence ?? 0,
      landmarks: (rightHand?.landmarks ?? []).map((landmark, index) => ({
        index,
        x: landmark.x,
        y: landmark.y,
        z: landmark.z ?? 0,
        world_x: landmark.world_x,
        world_y: landmark.world_y,
        world_z: landmark.world_z,
        visibility: landmark.visibility ?? 1,
      })),
    },
    pose: {
      landmarks: poseLandmarks,
    },
    face: {
      upper: faceUpper,
      mouth: faceMouth,
      emotion: face,
    },
  };

  const frame = {
    timestamp_ms: timestampMs,
    processing_confidence: hands.length > 0
      ? 0.95
      : hasShoulders
        ? 0.8
        : faceUpper.length > 0 || faceMouth.length > 0
          ? 0.7
          : 0,
    hands,
    face,
    left_shoulder: leftShoulder,
    right_shoulder: rightShoulder,
    landmark_worlds: landmarkWorlds,
    hand_motion: handMotion,
    subject_tracking: subjectTracking,
  };
  window.dispatchEvent(
    new CustomEvent('signbridge-hand-frame', {
      detail: JSON.stringify(frame),
    }),
  );
  queueTrackingFrame(frame);
  void requestDeepFaceEmotion(subject, faceLandmarks);
}

function processFrame() {
  if (!started) return;
  syncVisibleCameraElement();
  if (
    video?.readyState >= 2 &&
    handLandmarker &&
    poseLandmarker &&
    !detectionInProgress
  ) {
    const now = performance.now();
    if (now - lastProcessedAt >= DETECTION_INTERVAL_MS) {
      lastProcessedAt = now;
      detectionInProgress = true;
      try {
        const result = handLandmarker.detectForVideo(video, now);
        const poseResult = poseLandmarker.detectForVideo(video, now);
        let faceResult = lastFaceResult;
        if (
          faceLandmarker &&
          now - lastFaceProcessedAt >= FACE_DETECTION_INTERVAL_MS
        ) {
          try {
            faceResult = faceLandmarker.detectForVideo(video, now);
            lastFaceResult = faceResult;
            lastFaceProcessedAt = now;
          } catch (error) {
            // Face is supplementary. Keep hand and pose tracking alive if one
            // face inference fails.
            lastFaceProcessedAt = now;
            if (!trackingFrameErrorShown) {
              console.warn('A face frame failed; continuing hand/pose capture.', error);
              trackingFrameErrorShown = true;
            }
          }
        }
        dispatchFrame(result, poseResult, faceResult, Date.now());
        trackingLoopFrameCount += 1;
        if (now - trackingLoopLastLogAt >= 10_000) {
          const elapsedSeconds =
            (now - trackingLoopStartedAt) / 1000;
          console.info(
            `SignBridge tracking loop alive: ${trackingLoopFrameCount} frames over ${elapsedSeconds.toFixed(1)}s at ~${TRACKING_FPS} FPS.`,
          );
          trackingLoopLastLogAt = now;
        }
      } catch (error) {
        // A malformed frame or temporary detector failure must not terminate
        // requestAnimationFrame. The next video frame can recover.
        if (!trackingFrameErrorShown) {
          console.warn('A tracking frame failed; continuing capture.', error);
          trackingFrameErrorShown = true;
        }
      } finally {
        detectionInProgress = false;
      }
    }
  }
  animationFrame = requestAnimationFrame(processFrame);
}

async function createLandmarker(delegate) {
  const vision = await FilesetResolver.forVisionTasks(WASM_ROOT);
  const hand = await HandLandmarker.createFromOptions(vision, {
    baseOptions: {
      modelAssetPath: MODEL_URL,
      delegate,
    },
    runningMode: 'VIDEO',
    numHands: 2,
    minHandDetectionConfidence: 0.55,
    minHandPresenceConfidence: 0.55,
    minTrackingConfidence: 0.55,
  });
  const pose = await PoseLandmarker.createFromOptions(vision, {
    baseOptions: {
      modelAssetPath: POSE_MODEL_URL,
      delegate,
    },
    runningMode: 'VIDEO',
    numPoses: 2,
    minPoseDetectionConfidence: 0.55,
    minPosePresenceConfidence: 0.55,
    minTrackingConfidence: 0.55,
  });
  let face = null;
  try {
    face = await FaceLandmarker.createFromOptions(vision, {
      baseOptions: {
        modelAssetPath: FACE_MODEL_URL,
        delegate,
      },
      runningMode: 'VIDEO',
      numFaces: 2,
      outputFaceBlendshapes: false,
      outputFacialTransformationMatrixes: false,
      minFaceDetectionConfidence: 0.55,
      minFacePresenceConfidence: 0.55,
      minTrackingConfidence: 0.55,
    });
  } catch (error) {
    // Face landmarks are useful but optional. DeepFace emotion and the hand /
    // pose worlds should continue working if this extra model cannot load.
    console.warn('MediaPipe face landmarks unavailable.', error);
  }
  return { hand, pose, face };
}

function waitForCameraElement(timeoutMs = 3000) {
  const startedAt = performance.now();
  return new Promise((resolve, reject) => {
    const findElement = () => {
      const element = visibleCameraElement();
      if (element) {
        resolve(element);
        return;
      }
      if (performance.now() - startedAt >= timeoutMs) {
        reject(new Error('SignBridge camera view was not mounted in time.'));
        return;
      }
      requestAnimationFrame(findElement);
    };
    findElement();
  });
}

function endUtterance() {
  if (!started) return Promise.resolve();
  const endedUtteranceId = trackingUtteranceId;
  flushTrackingChunks();
  if (trackingSocket && trackingSocket.readyState === WebSocket.OPEN) {
    trackingSocket.send(
      JSON.stringify({
        type: 'utterance_end',
        session_id: trackingSocketSessionId,
        utterance_id: endedUtteranceId,
      }),
    );
  }
  beginUtterance();
  sendUtteranceStart();
  return Promise.resolve();
}

async function start() {
  if (started) return;
  // A hot restart or an interrupted startup can leave an old stream or
  // detector alive. Release those resources before requesting the camera
  // again so the next page/start cycle always gets a clean session.
  await stop();
  try {
    // Flutter marks the camera as ready and mounts HtmlElementView on the next
    // frame. Wait for that element before requesting permission or attaching
    // the stream, otherwise the first click can fail even though permission
    // exists.
    video = await waitForCameraElement();

    stream = await navigator.mediaDevices.getUserMedia({
      audio: false,
      video: {
        facingMode: 'user',
        width: { ideal: 1280 },
        height: { ideal: 720 },
      },
    });
    video.srcObject = stream;
    video.muted = true;
    video.playsInline = true;
    await video.play();

    try {
      const detectors = await createLandmarker('GPU');
      handLandmarker = detectors.hand;
      poseLandmarker = detectors.pose;
      faceLandmarker = detectors.face;
    } catch (error) {
      console.warn('MediaPipe GPU delegate unavailable; using CPU.', error);
      const detectors = await createLandmarker('CPU');
      handLandmarker = detectors.hand;
      poseLandmarker = detectors.pose;
      faceLandmarker = detectors.face;
    }
  } catch (error) {
    await stop();
    throw error;
  }

  started = true;
  trackingSocketSessionId = `session-${Date.now()}`;
  trackingSocketFrameCount = 0;
  trackingSocketChunkCount = 0;
  trackingSocketWarningShown = false;
  trackingFrameErrorShown = false;
  lastProcessedAt = 0;
  lastFaceResult = undefined;
  lastFaceProcessedAt = 0;
  detectionInProgress = false;
  trackingLoopFrameCount = 0;
  trackingLoopStartedAt = performance.now();
  trackingLoopLastLogAt = trackingLoopStartedAt;
  subjectTrack = null;
  subjectAcquire = null;
  beginUtterance();
  connectTrackingSocket();
  processFrame();
}

async function stop() {
  const wasStarted = started;
  if (wasStarted) {
    flushTrackingChunks();
    if (trackingSocket && trackingSocket.readyState === WebSocket.OPEN) {
      trackingSocket.send(
        JSON.stringify({
          type: 'utterance_end',
          session_id: trackingSocketSessionId,
          utterance_id: trackingUtteranceId,
        }),
      );
    }
  }
  started = false;
  clearTimeout(trackingSocketReconnectTimer);
  if (trackingSocket) {
    if (trackingSocket.readyState === WebSocket.OPEN) {
      trackingSocket.send(
        JSON.stringify({
          type: 'end',
          session_id: trackingSocketSessionId,
        }),
      );
    }
    if (
      trackingSocket.readyState === WebSocket.OPEN ||
      trackingSocket.readyState === WebSocket.CONNECTING
    ) {
      trackingSocket.close();
    }
  }
  trackingSocket = null;
  if (animationFrame) cancelAnimationFrame(animationFrame);
  stream?.getTracks().forEach((track) => track.stop());
  stream = null;
  if (video) video.srcObject = null;
  deepFaceEmotion = null;
  deepFaceRequestInFlight = false;
  lastDeepFaceRequestAt = 0;
  deepFaceSubjectGeneration += 1;
  handLandmarker?.close();
  poseLandmarker?.close();
  faceLandmarker?.close();
  handLandmarker = null;
  poseLandmarker = null;
  faceLandmarker = null;
  trackingUtteranceId = null;
  trackingChunkFrames = [];
  trackingChunkStartedAt = 0;
  previousHandMotion = {left: null, right: null};
  previousMotionTimestamp = null;
  lastProcessedAt = 0;
  lastFaceResult = undefined;
  lastFaceProcessedAt = 0;
  detectionInProgress = false;
  trackingLoopFrameCount = 0;
  trackingLoopStartedAt = 0;
  trackingLoopLastLogAt = 0;
  subjectTrack = null;
  subjectAcquire = null;
}

globalThis.addEventListener('pagehide', () => {
  void stop();
});

window.signBridgeHandTracker = { start, stop, endUtterance };
