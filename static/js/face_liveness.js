const video = document.getElementById("video");
const stepLabel = document.getElementById("livenessStep");
const submitBtn = document.getElementById("submitBtn");
const livenessPassed = document.getElementById("livenessPassed");
const debugLabel = document.getElementById("livenessDebug");
const snapshotInput = document.getElementById("snapshotInput");
const captureCanvas = document.getElementById("captureCanvas");
const snapshotPreview = document.getElementById("snapshotPreview");

const REQUIRED_BLINKS = 2;
const REQUIRED_TURNS = 1;

let blinkCount = 0;
let turnCount = 0;
let earClosed = false;
let modelsLoaded = false;
let calibrated = false;
let earOpenBaseline = 0;
let earCloseThreshold = 0;
let earOpenThreshold = 0;
let calibrationSamples = [];

const LIVENESS = {
  INIT: "Initializing…",
  BLINK: "Please blink 2 times",
  TURN: "Turn your head left or right",
  DONE: "Liveness passed",
  CALIBRATE: "Calibrating… look at the camera",
};

const computeEAR = (landmarks) => {
  const left = landmarks.getLeftEye();
  const right = landmarks.getRightEye();
  const ear = (eye) => {
    const p1 = eye[1];
    const p2 = eye[5];
    const p3 = eye[2];
    const p4 = eye[4];
    const p5 = eye[0];
    const p6 = eye[3];
    const dist = (a, b) => Math.hypot(a.x - b.x, a.y - b.y);
    return (dist(p1, p2) + dist(p3, p4)) / (2 * dist(p5, p6));
  };
  return (ear(left) + ear(right)) / 2;
};

const startCamera = async () => {
  const stream = await navigator.mediaDevices.getUserMedia({ video: true });
  video.srcObject = stream;
  return new Promise((resolve) => {
    video.onloadedmetadata = () => resolve();
  });
};

const loadModels = async () => {
  const base = "/static/models";
  await faceapi.nets.tinyFaceDetector.loadFromUri(base);
  await faceapi.nets.faceLandmark68Net.loadFromUri(base);
  modelsLoaded = true;
};

const updateStep = () => {
  if (blinkCount < REQUIRED_BLINKS) {
    stepLabel.textContent = LIVENESS.BLINK;
    return;
  }
  if (turnCount < REQUIRED_TURNS) {
    stepLabel.textContent = LIVENESS.TURN;
    return;
  }
  stepLabel.textContent = LIVENESS.DONE;
  submitBtn.disabled = false;
  livenessPassed.value = "1";
  if (!snapshotInput.value) {
    captureSnapshot();
  }
};

const captureSnapshot = () => {
  if (!captureCanvas || !snapshotInput) return;
  const width = video.videoWidth || 640;
  const height = video.videoHeight || 480;
  captureCanvas.width = width;
  captureCanvas.height = height;
  const ctx = captureCanvas.getContext("2d");
  ctx.drawImage(video, 0, 0, width, height);
  const dataUrl = captureCanvas.toDataURL("image/jpeg", 0.85);
  snapshotInput.value = dataUrl;
  if (snapshotPreview) {
    snapshotPreview.src = dataUrl;
    snapshotPreview.classList.remove("d-none");
  }
};

const detectLoop = async () => {
  if (!modelsLoaded) return;

  const detection = await faceapi
    .detectSingleFace(video, new faceapi.TinyFaceDetectorOptions())
    .withFaceLandmarks();

  if (detection && detection.landmarks) {
    const ear = computeEAR(detection.landmarks);
    if (debugLabel) {
      debugLabel.textContent = `EAR: ${ear.toFixed(3)}`;
    }

    if (!calibrated) {
      calibrationSamples.push(ear);
      if (calibrationSamples.length >= 20) {
        earOpenBaseline =
          calibrationSamples.reduce((a, b) => a + b, 0) / calibrationSamples.length;
        // Use more lenient thresholds for cameras with minimal EAR drop.
        earCloseThreshold = earOpenBaseline * 0.9;
        earOpenThreshold = earOpenBaseline * 0.97;
        calibrated = true;
      }
    } else if (ear < earCloseThreshold && !earClosed) {
      earClosed = true;
    }
    if (calibrated && ear > earOpenThreshold && earClosed) {
      earClosed = false;
      blinkCount += 1;
    }

    const nose = detection.landmarks.getNose()[3];
    const left = detection.landmarks.getLeftEye()[0];
    const right = detection.landmarks.getRightEye()[3];
    const faceWidth = Math.hypot(right.x - left.x, right.y - left.y);
    const offset = (nose.x - left.x) / faceWidth;
    if (offset < 0.35 || offset > 0.65) {
      if (turnCount < REQUIRED_TURNS) {
        turnCount += 1;
      }
    }
  }

  if (!calibrated) {
    stepLabel.textContent = LIVENESS.CALIBRATE;
  } else {
    updateStep();
  }
  requestAnimationFrame(detectLoop);
};

const init = async () => {
  stepLabel.textContent = LIVENESS.INIT;
  await loadModels();
  await startCamera();
  updateStep();
  detectLoop();
};

const bindSnapshotOnSubmit = () => {
  const form = document.getElementById("verifyForm");
  if (!form) return;
  form.addEventListener("submit", () => {
    if (livenessPassed.value !== "1") return;
    if (snapshotInput && snapshotInput.value) return;
    captureSnapshot();
  });
};

bindSnapshotOnSubmit();
init().catch(() => {
  stepLabel.textContent = "Camera access required.";
});
