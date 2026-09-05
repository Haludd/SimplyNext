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

let handLandmarker;
let poseLandmarker;
let faceLandmarker;
let video;
let stream;
let animationFrame;
let started = false;

function posePointToJson(point) {
  if (!point) return null;
  return {
    x: point.x,
    y: point.y,
    z: point.z ?? 0,
    visibility: point.visibility ?? point.presence ?? 0,
  };
}

function averageBlendshape(blendshapes, names) {
  const values = names
    .map((name) => blendshapes[name] ?? 0)
    .filter((value) => value > 0);
  return values.length === 0
    ? 0
    : values.reduce((sum, value) => sum + value, 0) / values.length;
}

function faceToJson(faceResult) {
  const sourceLandmarks = faceResult?.faceLandmarks?.[0] ?? [];
  if (sourceLandmarks.length === 0) return null;

  const landmarkIndices = [1, 10, 13, 14, 33, 61, 70, 263, 291, 300];
  const landmarks = landmarkIndices.map((index) => ({
    index,
    ...posePointToJson(sourceLandmarks[index]),
  }));
  const categories = faceResult?.faceBlendshapes?.[0]?.categories ?? [];
  const blendshapes = Object.fromEntries(
    categories.map((category) => [
      category.categoryName,
      category.score ?? 0,
    ]),
  );
  const smile = averageBlendshape(blendshapes, [
    'mouthSmileLeft',
    'mouthSmileRight',
  ]);
  const frown = averageBlendshape(blendshapes, [
    'mouthFrownLeft',
    'mouthFrownRight',
  ]);
  const browRaise = averageBlendshape(blendshapes, [
    'browInnerUp',
    'browOuterUpLeft',
    'browOuterUpRight',
  ]);
  const browFurrow = averageBlendshape(blendshapes, [
    'browDownLeft',
    'browDownRight',
  ]);
  const eyeWide = averageBlendshape(blendshapes, [
    'eyeWideLeft',
    'eyeWideRight',
  ]);
  const jawOpen = blendshapes.jawOpen ?? 0;
  const mouthPucker = blendshapes.mouthPucker ?? 0;
  const candidates = [
    ['smile', smile],
    ['frown', frown],
    ['brow raised', browRaise],
    ['brow furrowed', browFurrow],
    ['eyes wide', eyeWide],
    ['mouth open', jawOpen],
    ['pursed lips', mouthPucker],
  ].sort((left, right) => right[1] - left[1]);
  const label = candidates[0][1] >= 0.35 ? candidates[0][0] : 'neutral';

  return {
    confidence: 0.9,
    label,
    smile,
    frown,
    brow_raise: browRaise,
    brow_furrow: browFurrow,
    eye_wide: eyeWide,
    jaw_open: jawOpen,
    mouth_pucker: mouthPucker,
    landmarks,
    blendshapes,
  };
}

function dispatchFrame(result, poseResult, faceResult) {
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
  const face = faceToJson(faceResult);

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
}

function processFrame() {
  if (!started) return;
  if (
    video?.readyState >= 2 &&
    handLandmarker &&
    poseLandmarker &&
    faceLandmarker
  ) {
    const result = handLandmarker.detectForVideo(video, performance.now());
    const poseResult = poseLandmarker.detectForVideo(video, performance.now());
    const faceResult = faceLandmarker.detectForVideo(video, performance.now());
    dispatchFrame(result, poseResult, faceResult);
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
  const face = await FaceLandmarker.createFromOptions(vision, {
    baseOptions: {
      modelAssetPath: FACE_MODEL_URL,
      delegate,
    },
    runningMode: 'VIDEO',
    numFaces: 1,
    minFaceDetectionConfidence: 0.55,
    minFacePresenceConfidence: 0.55,
    minTrackingConfidence: 0.55,
    outputFaceBlendshapes: true,
  });
  return { hand, pose, face };
}

function waitForCameraElement(timeoutMs = 3000) {
  const startedAt = performance.now();
  return new Promise((resolve, reject) => {
    const findElement = () => {
      const element = document.getElementById('signbridge-web-camera');
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
    faceLandmarker = detectors.face;
  } catch (error) {
    console.warn('MediaPipe GPU delegate unavailable; using CPU.', error);
    const detectors = await createLandmarker('CPU');
    handLandmarker = detectors.hand;
    poseLandmarker = detectors.pose;
    faceLandmarker = detectors.face;
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
  handLandmarker?.close();
  poseLandmarker?.close();
  faceLandmarker?.close();
  handLandmarker = null;
  poseLandmarker = null;
  faceLandmarker = null;
}

window.signBridgeHandTracker = { start, stop };
