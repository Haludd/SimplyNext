import {
  FilesetResolver,
  HandLandmarker,
  PoseLandmarker,
} from 'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.35/vision_bundle.mjs';

const WASM_ROOT =
  'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.35/wasm';
const MODEL_URL =
  'https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task';
const POSE_MODEL_URL =
  'https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task';
const configuredDeepFaceUrl = globalThis.signBridgeDeepFaceUrl;
const queryDeepFaceUrl = new URLSearchParams(globalThis.location.search).get(
  'deepface_api',
);
const DEEPFACE_API_URL =
  configuredDeepFaceUrl ||
  queryDeepFaceUrl ||
  'http://127.0.0.1:8000/v1/emotions/analyze';
const DEEPFACE_INTERVAL_MS = 1200;

let handLandmarker;
let poseLandmarker;
let video;
let stream;
let animationFrame;
let started = false;
let deepFaceEmotion;
let deepFaceRequestInFlight = false;
let lastDeepFaceRequestAt = 0;
let deepFaceWarningShown = false;
let emotionCanvas;
let emotionContext;

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

function posePointToJson(point) {
  if (!point) return null;
  return {
    x: point.x,
    y: point.y,
    z: point.z ?? 0,
    visibility: point.visibility ?? point.presence ?? 0,
  };
}

async function requestDeepFaceEmotion() {
  if (
    !DEEPFACE_API_URL ||
    !video ||
    video.readyState < 2 ||
    deepFaceRequestInFlight
  ) {
    return;
  }

  const now = performance.now();
  if (now - lastDeepFaceRequestAt < DEEPFACE_INTERVAL_MS) return;
  lastDeepFaceRequestAt = now;
  deepFaceRequestInFlight = true;

  try {
    if (!emotionCanvas) {
      emotionCanvas = document.createElement('canvas');
      emotionContext = emotionCanvas.getContext('2d');
    }
    const sourceWidth = video.videoWidth || 640;
    const sourceHeight = video.videoHeight || 480;
    const scale = Math.min(1, 480 / sourceWidth);
    emotionCanvas.width = Math.max(1, Math.round(sourceWidth * scale));
    emotionCanvas.height = Math.max(1, Math.round(sourceHeight * scale));
    emotionContext.drawImage(
      video,
      0,
      0,
      emotionCanvas.width,
      emotionCanvas.height,
    );
    const blob = await new Promise((resolve) =>
      emotionCanvas.toBlob(resolve, 'image/jpeg', 0.68),
    );
    if (!blob) return;

    const response = await fetch(DEEPFACE_API_URL, {
      method: 'POST',
      headers: {'Content-Type': 'image/jpeg'},
      body: blob,
    });
    if (!response.ok) {
      throw new Error(`DeepFace API returned ${response.status}`);
    }
    const payload = await response.json();
    deepFaceEmotion = payload.status === 'ok' ? payload : null;
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

function dispatchFrame(result, poseResult) {
  const handednesses = result.handednesses ?? result.handedness ?? [];
  const hands = (result.landmarks ?? []).map((landmarks, index) => {
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
  const pose = poseResult?.landmarks?.[0] ?? [];
  const leftShoulder = posePointToJson(pose[11]);
  const rightShoulder = posePointToJson(pose[12]);
  const hasShoulders =
    leftShoulder?.visibility >= 0.45 && rightShoulder?.visibility >= 0.45;
  const face = deepFaceToJson(deepFaceEmotion);

  window.dispatchEvent(
    new CustomEvent('signbridge-hand-frame', {
      detail: JSON.stringify({
        timestamp_ms: Date.now(),
        processing_confidence: hands.length > 0
          ? 0.95
          : hasShoulders
            ? 0.8
            : 0,
        hands,
        face,
        left_shoulder: leftShoulder,
        right_shoulder: rightShoulder,
      }),
    }),
  );
  void requestDeepFaceEmotion();
}

function processFrame() {
  if (!started) return;
  syncVisibleCameraElement();
  if (
    video?.readyState >= 2 &&
    handLandmarker &&
    poseLandmarker
  ) {
    const result = handLandmarker.detectForVideo(video, performance.now());
    const poseResult = poseLandmarker.detectForVideo(video, performance.now());
    dispatchFrame(result, poseResult);
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
    numPoses: 1,
    minPoseDetectionConfidence: 0.55,
    minPosePresenceConfidence: 0.55,
    minTrackingConfidence: 0.55,
  });
  return { hand, pose };
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

async function start() {
  if (started) return;
  // Flutter marks the camera as ready and mounts HtmlElementView on the next
  // frame. Wait for that element before requesting permission or attaching the
  // stream, otherwise the first click can fail even though permission exists.
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
  } catch (error) {
    console.warn('MediaPipe GPU delegate unavailable; using CPU.', error);
    const detectors = await createLandmarker('CPU');
    handLandmarker = detectors.hand;
    poseLandmarker = detectors.pose;
  }

  started = true;
  processFrame();
}

async function stop() {
  started = false;
  if (animationFrame) cancelAnimationFrame(animationFrame);
  stream?.getTracks().forEach((track) => track.stop());
  stream = null;
  if (video) video.srcObject = null;
  deepFaceEmotion = null;
  deepFaceRequestInFlight = false;
  lastDeepFaceRequestAt = 0;
  handLandmarker?.close();
  poseLandmarker?.close();
  handLandmarker = null;
  poseLandmarker = null;
}

window.signBridgeHandTracker = { start, stop };
