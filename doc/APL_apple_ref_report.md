**APPLE REFERENCE REPOSITORY — FULL TECHNICAL REPORT**





# METADATA
<details>
<summary>Document code, status, review date, and usage instructions.</summary>

| Field                   | Value                                             |
| :---------------------- | :------------------------------------------------ |
| **Code**                | `APL`                                             |
| **Status**              | Live                                              |
| **Last reviewed**       | 2026-08-28                                        |
| **Source of truth for** | Analysis of the Apple reference repository        |
| **Parent**              | [`RIX_S2.1`](../ref_index.md#21-live-documents)   |
| **Short version**       | [`SYN`](../ref_repo/apple/SYN_apple_synthesis.md) |
| **Subject**             | `ref_repo/apple/` at commit `ec30ff6`             |

**For the team.** What `ref_repo/apple/` is, how it is built, what philosophy it encodes, and which
parts transfer to SimplyNext. [`APL_S10`](#10-relevance-to-simplynext) holds the twelve lessons and the Swift → Python
port table.

**For the assistant.** The sample targets **iOS, not Apple Vision Pro** —
[`APL_S1.1`](#11-what-this-repository-is). Line numbers refer to the files at the commit named above; re-verify them
before citing. Nothing in `ref_repo/apple/` may be edited except
[`SYN`](../ref_repo/apple/SYN_apple_synthesis.md).

</details>

---





# 1. EXECUTIVE SUMMARY
## 1.1. What This Repository Is
`ref_repo/apple/` is Apple's official sample project **"Detecting Hand Poses with Vision"**
(target name `HandPose`). It is a ~450-line iOS application that turns the camera into a
finger-painting surface: pinching thumb and index finger together draws, and pulling them apart
ends the stroke. It ships as the companion code to WWDC20 session 10653,
*Detect Body and Hand Pose with Vision* `[S1]`.

> **Correction to a shared assumption.** The repository is often described in project notes as an
> "Apple Vision Pro" project. It is not. It targets **iOS 14 on iPhone and iPad** using Apple's
> **Vision** framework — a computer-vision library that has existed since iOS 11 and whose name
> long predates the Apple Vision Pro headset. The hand-pose API it uses *is* also available on
> visionOS 1.0+ `[S2]`, so the correction changes nothing about the repository's usefulness here;
> it changes how it must be described in a submission, where calling it a Vision Pro project would
> be a factual error a judge could catch.




## 1.2. Why It Matters to SimplyNext
Apple's app is, structurally, **steps 1 to 3 of the MVP** ([`SCR`](../plan/scribbles.md), *Current MVP*)
implemented to production quality, and then it stops — deliberately — right before step 4.

1. **1. Isolate the subject from environment noise**
   *Apple's app:* `maximumHandCount = 1`; Vision returns hands ordered by size, so the largest hand
   wins
   *Verdict:* Solved, crudely but effectively
2. **2. Track many points on hands and face**
   *Apple's app:* Vision detects 21 hand joints; the app **uses 2**
   *Verdict:* Capability present, deliberately under-used
3. **3. Turn the points into a skeleton**
   *Apple's app:* 2D normalised points, three coordinate spaces, confidence-gated
   *Verdict:* Solved for 2D; no 3D
4. **4. Turn skeleton motion into conversational text**
   *Apple's app:* **Not attempted.** A hand-written 5-state machine over one scalar distance
   *Verdict:* The project's entire contribution

The repository's real value is therefore **not the drawing feature**. It is the
*plumbing*: how to get from a camera buffer to trustworthy, temporally-stable landmark data
without the output flickering, stuttering, or lying. That plumbing is where naive sign-language
prototypes fail, and Apple solved it in about 80 lines. Sections [`APL_S6`](#6-working-philosophy) and
[`APL_S10`](#10-relevance-to-simplynext) extract those lines.




## 1.3. Summary
A serial dispatch queue receives camera frames and drops any it cannot keep up with. Each frame
is handed synchronously to a single `VNDetectHumanHandPoseRequest`. Points below 30% confidence
are discarded rather than smoothed. Surviving points are converted through three coordinate
systems and pushed to a small state machine that refuses to change its mind until it has seen
the same evidence three frames running — while buffering the frames it is unsure about, so that
committing later costs no data. Two seconds of silence resets the machine. Rendering happens on
`CAShapeLayer`s with implicit animation switched off. Every failure is surfaced to the user and
stops the session rather than degrading quietly.

---





# 2. PROVENANCE, LICENCE AND BUILD REQUIREMENTS
## 2.1. Provenance
1. **Publisher**
   Apple Inc.
2. **Sample name**
   Detecting Hand Poses with Vision
3. **Xcode target**
   `HandPose`
4. **Associated session**
   WWDC20 session 10653, *Detect Body and Hand Pose with Vision* `[S1]`
5. **Git history in `ref_repo/apple/`**
   4 commits: `Initial release for WWDC20` → `Minor updates.` ×2 → `Republish sample code project.`
6. **Language**
   Swift 5.0, UIKit + storyboards

The four-commit history matters: this is a **frozen teaching artefact**, not a maintained
library. It will not gain features. Anything missing is missing on purpose.




## 2.2. Licence
`LICENSE.txt` is Apple's standard sample-code licence. Read it before copying code verbatim into
a submission. Practically, for a hackathon the safe posture is: **copy the architecture and the
ideas, re-implement the code in Python, and credit the source.** The port from Swift to Python
happens regardless ([`APL_S10.2`](#102-swift--python-port-table)), so this costs nothing.




## 2.3. Build Configuration
Extracted from `HandPose.xcodeproj/project.pbxproj`, `HandPose/Info.plist` and
`Configuration/SampleCode.xcconfig`:

1. **`IPHONEOS_DEPLOYMENT_TARGET`**
   *Value:* `14.0`
   *Consequence:* Hand pose is an iOS 14 API; the floor is not arbitrary
2. **`SWIFT_VERSION`**
   *Value:* `5.0`
   *Consequence:* —
3. **`TARGETED_DEVICE_FAMILY`**
   *Value:* `1,2`
   *Consequence:* iPhone and iPad
4. **`UISupportedInterfaceOrientations`**
   *Value:* Portrait only
   *Consequence:* Simplifies the coordinate maths; see
   [`APL_S5.2`](#52-coordinate-spaces--three-of-them)
5. **`UIRequiresFullScreen`**
   *Value:* `true`
   *Consequence:* No iPad split-view — the preview layer's geometry stays predictable
6. **`NSCameraUsageDescription`**
   *Value:* *"This application uses the camera to demonstrate new Vision technology."*
   *Consequence:* Mandatory; without it the app is killed on first camera access
7. **`SAMPLE_CODE_DISAMBIGUATOR`**
   *Value:* `${DEVELOPMENT_TEAM}`
   *Consequence:* Makes the bundle ID unique per developer. Apple explicitly says **do not** copy
   this pattern into real projects

`HandPose/HandPose.entitlements` requests `app-sandbox`, `device.camera` and `network.client`.

> **Note:** the `network.client` entitlement is **never exercised**. There is not a single
> network call in the codebase. It is boilerplate. This is worth naming out loud because it is
> the strongest single piece of evidence for [`APL_S6.1`](#61-on-device-by-default): the entire pipeline is
> on-device.

---





# 3. REPOSITORY MAP
## 3.1. File Inventory
```text
ref_repo/apple/
├── README.md                                  6 lines  — points at the WWDC session
├── LICENSE.txt                                         — Apple sample-code licence
├── Configuration/SampleCode.xcconfig                   — bundle-ID disambiguator
├── HandPose.xcodeproj/                                 — project definition
└── HandPose/
    ├── AppDelegate.swift                     59 lines  — app entry + AppError enum
    ├── SceneDelegate.swift                   15 lines  — empty; holds the UIWindow
    ├── CameraView.swift                      58 lines  — preview layer + point overlay
    ├── CameraViewController.swift           243 lines  — THE FILE. Capture, Vision, drawing
    ├── HandGestureProcessor.swift            79 lines  — pinch/apart state machine
    ├── Base.lproj/Main.storyboard                      — one VC whose view class is CameraView
    ├── Base.lproj/LaunchScreen.storyboard
    ├── Assets.xcassets/
    ├── Info.plist
    └── HandPose.entitlements
```

Roughly **454 lines of Swift in five files**. Two of them (`SceneDelegate`, and half of
`AppDelegate`) are framework boilerplate. The substance is three files and about 380 lines.




## 3.2. Responsibility Split
1. **`CameraViewController.swift`**
   *Single responsibility:* Orchestration: own the capture session, run Vision, convert coordinates,
   drive the drawing
   *Knows about:* Everything
2. **`HandGestureProcessor.swift`**
   *Single responsibility:* Decide *pinched* vs *apart* from a stream of two points, stably
   *Knows about:* Nothing but `CGPoint`
3. **`CameraView.swift`**
   *Single responsibility:* Show the camera feed and paint fingertip dots
   *Knows about:* `UIKit`, `AVFoundation`
4. **`AppDelegate.swift`**
   *Single responsibility:* App lifecycle + a typed error vocabulary
   *Knows about:* `UIKit`, `Vision`
5. **`SceneDelegate.swift`**
   *Single responsibility:* Hold the window
   *Knows about:* `UIKit`

`HandGestureProcessor` importing **only `CoreGraphics`** is the most important line in the
repository's design. The semantic layer has no dependency on cameras, on Vision, or on UIKit. It
is a pure function of a point stream — which means it is unit-testable, portable, and replaceable.
The sign-segmentation logic must have the same property. See [`APL_S10.3`](#103-the-architectural-boundary-to-preserve).

---





# 4. ARCHITECTURE
## 4.1. The Pipeline
```text
                    ┌──────────────────────────────────────────────┐
                    │  AVCaptureSession                            │
                    │  front wide-angle camera · preset .high      │
                    └───────────────┬──────────────────────────────┘
                                    │ CMSampleBuffer, 1 per frame
                                    │ alwaysDiscardsLateVideoFrames = true
                                    ▼
    ┌───────────────────────────────────────────────────────────────────────┐
    │  QUEUE: "CameraFeedDataOutput"  (serial, qos .userInteractive)        │
    │                                                                       │
    │   VNImageRequestHandler(cmSampleBuffer:, orientation: .up)            │
    │            │                                                          │
    │            ▼                                                          │
    │   VNDetectHumanHandPoseRequest   maximumHandCount = 1                 │
    │            │                                                          │
    │            ▼  [VNHumanHandPoseObservation]                            │
    │   results.first  →  recognizedPoints(.thumb) / (.indexFinger)         │
    │            │                                                          │
    │            ▼  GATE 1: point exists?                                   │
    │            ▼  GATE 2: confidence > 0.3?                               │
    │            │                                                          │
    │            ▼  Vision space → AVFoundation space   (y := 1 − y)        │
    └────────────┼──────────────────────────────────────────────────────────┘
                 │ DispatchQueue.main.sync   ← deliberate back-pressure
                 ▼
    ┌───────────────────────────────────────────────────────────────────────┐
    │  MAIN THREAD                                                          │
    │                                                                       │
    │   AVFoundation space → UIKit layer space                              │
    │     previewLayer.layerPointConverted(fromCaptureDevicePoint:)         │
    │            │                                                          │
    │            ▼                                                          │
    │   HandGestureProcessor.processPointsPair((thumbTip, indexTip))        │
    │            │  distance = hypot(...)                                   │
    │            ▼  evidence counters, 3-frame trigger                      │
    │      ┌─────┴───────────────────────────────────────┐                  │
    │      │ .possiblePinch / .possibleApart → BUFFER    │  orange dots     │
    │      │ .pinched   → replay buffer, then draw       │  green dots      │
    │      │ .apart     → discard buffer, close stroke   │  red dots        │
    │      └─────┬───────────────────────────────────────┘                  │
    │            ▼                                                          │
    │   UIBezierPath (quad-curve smoothing) → CAShapeLayer                  │
    │   CATransaction.setDisableActions(true)                               │
    └───────────────────────────────────────────────────────────────────────┘
```




## 4.2. Layers
1. **Capture**
   *Where:* `setupAVSession()`, `CameraViewController.swift:70–102`
   *Concern:* Get frames, drop late ones
   *Stateless?:* yes
2. **Perception**
   *Where:* `captureOutput(_:didOutput:from:)`, `:202–243`
   *Concern:* Frame → landmarks + confidence
   *Stateless?:* **yes — one frame at a time**
3. **Filtering**
   *Where:* `:225–231`
   *Concern:* Reject missing and low-confidence points
   *Stateless?:* yes
4. **Coordinate transform**
   *Where:* `:233–234` and `:116–118`
   *Concern:* Three spaces, two conversions
   *Stateless?:* yes
5. **Temporal / semantic**
   *Where:* `HandGestureProcessor.swift`
   *Concern:* Stabilise a noisy signal into discrete states
   *Stateless?:* **no — this is the only stateful layer**
6. **Presentation**
   *Where:* `handleGestureStateChange`, `updatePath`, `CameraView.swift`
   *Concern:* Draw dots and ink
   *Stateless?:* no

The design rule this expresses: **the machine-learning layer is stateless and the state lives in
plain, testable application code.** Vision knows nothing about the previous frame. All memory —
evidence counters, the buffer, the last draw point, the staleness timestamp — is ordinary Swift
that a human wrote and can reason about.

That rule is the single most transferable idea in the repository, and [`ARC`](../plan/ARC_architecture.md)
adopts it wholesale.




## 4.3. Threading Model
1. **`CameraFeedDataOutput` (serial, `.userInteractive`)**
   *Work:* Camera delivery + all Vision inference
   *Why:* Serial guarantees frames are processed in order; a private queue keeps inference off the
   UI
2. **Main**
   *Work:* Coordinate conversion into layer space, the state machine, all drawing
   *Why:* `previewLayer.layerPointConverted` and `CAShapeLayer` are main-thread-only

The hop is `DispatchQueue.main.sync` inside a `defer` block (`CameraViewController.swift:206–210`).

> **Warning — read this before copying.** `main.sync` **blocks the capture queue** until the main
> thread finishes. That is a feature *here*: it guarantees the app can never build an unbounded
> backlog of frames, because frame N+1 cannot start until frame N has been fully drawn. It
> couples inference rate to render rate.
>
> It is also a deadlock waiting to happen if any main-thread work ever synchronously waits on the
> capture queue, and it is the wrong pattern the moment inference gets slower than one frame
> interval — which it will here, once a temporal model runs on top. The port keeps the *intent*
> (bounded backlog) and changes the *mechanism* to a bounded queue with a drop-oldest policy. See [`RSK_S6`](../plan/RSK_risk_register.md#6-system-and-platform) for the latency risks
> this touches.

---





# 5. FILE-BY-FILE DEEP DIVE
## 5.1. `CameraViewController.swift` — Capture and Orchestration
**`viewDidLoad()` (`:29–49`)** builds the ink overlay, sets `handPoseRequest.maximumHandCount = 1`,
wires the state-machine callback, and registers a double-tap recogniser that clears the canvas.

The comment on line 38 is worth quoting: *"This sample app detects one hand only."* The API's
default is 2 `[S3]`. Apple **narrowed** the capability on purpose, to keep the sample about one
idea. The port widens it back.

**`setupAVSession()` (`:70–102`)** is the configuration to reproduce almost verbatim in spirit:

1. **`:72`**
   *Choice:* `.builtInWideAngleCamera`, `position: .front`
   *Reasoning:* Selfie camera — the user must see their own hands
2. **`:82`**
   *Choice:* `sessionPreset = .high`
   *Reasoning:* Enough resolution for joint detection; not 4K, which would waste the pixels
3. **`:94`**
   *Choice:* `alwaysDiscardsLateVideoFrames = true`
   *Reasoning:* **Drop frames, never queue them.** Latency stays bounded; throughput degrades
   gracefully
4. **`:95`**
   *Choice:* `kCVPixelFormatType_420YpCbCr8BiPlanarFullRange`
   *Reasoning:* Native camera format — no colour conversion cost before Vision
5. **`:96`**
   *Choice:* Delegate on a private serial queue
   *Reasoning:* Inference never touches the UI thread

**`captureOutput(_:didOutput:from:)` (`:202–243`)** — the perception step. Note the ordering: a
`defer` block at the *top* (`:206–210`) guarantees `processPoints` runs on every single frame,
including the early-`return` paths where no hand was found. That is how the "no observation for
2 seconds" reset ever gets a chance to fire. Restructuring this into a straight-line function
would silently break the staleness timer.

Two hard gates before any point is trusted:

```swift
guard let thumbTipPoint = thumbPoints[.thumbTip],
      let indexTipPoint = indexFingerPoints[.indexTip] else { return }   // exists?
guard thumbTipPoint.confidence > 0.3 && indexTipPoint.confidence > 0.3 else { return }  // trusted?
```

`0.3` is a magic number with no comment. Empirically it is permissive — it admits fairly poor
detections. For sign language, where a wrong handshape is a wrong *word*, this threshold must be a
tuned, measured parameter, per joint group, not a constant. See
[`RSK_S3`](../plan/RSK_risk_register.md#3-linguistic).

**`processPoints(thumbTip:indexTip:)` (`:104–122`)** handles the empty case first: if either point
is missing and more than 2 seconds have passed since the last observation, reset the state
machine and clear the dots. Staleness is treated as a state, not as an absence of events.

**`updatePath(with:isLastPointsPair:)` (`:154–189`)** is the drawing smoother. It never draws
straight to the raw fingertip midpoint; it draws a quadratic Bézier *to the midpoint between the
last point and the new point*, using the last point as the control point. This is the standard
freehand-smoothing trick, and it is doing the same job as a low-pass filter on a jittery signal.
The landmark stream needs the analogous treatment — see [`APL_S10.1`](#101-lessons-to-carry-across), lesson L6.




## 5.2. Coordinate Spaces — Three of Them
This is the highest-density source of bugs in any camera + ML pipeline, and Apple's handling is
exemplary. Three distinct spaces are in play:

1. **Vision normalised** · *Range:* `0…1` × `0…1`
   *Origin:* bottom-left
   *Produced by:* `VNRecognizedPoint.location`
2. **AVFoundation capture-device** · *Range:* `0…1` × `0…1`
   *Origin:* **top-left**
   *Produced by:* the `1 − y` flip at `:233–234`
3. **UIKit layer points** · *Range:* pixels
   *Origin:* top-left of the preview layer
   *Produced by:* `previewLayer.layerPointConverted(fromCaptureDevicePoint:)` at `:117–118`

```swift
// 1 → 2   (CameraViewController.swift:233)
thumbTip = CGPoint(x: thumbTipPoint.location.x, y: 1 - thumbTipPoint.location.y)

// 2 → 3   (CameraViewController.swift:117)
let thumbPointConverted = previewLayer.layerPointConverted(fromCaptureDevicePoint: thumbPoint)
```

Two properties of this design are worth reproducing:

1. **Conversion happens at layer boundaries, exactly once, and nowhere else.** No function is
   ambiguous about which space its arguments are in.
2. **The geometry-dependent conversion (2 → 3) is delegated to the framework**, which knows about
   `videoGravity = .resizeAspectFill`, the device orientation, and the preview layer's bounds.
   Hand-rolling that arithmetic is how aspect-ratio bugs are born.

The app locks to portrait and passes `orientation: .up` to the request handler, which sidesteps
the rotation problem entirely rather than solving it. That shortcut is not available for a
multi-device product — see [`RSK_S2.2`](../plan/RSK_risk_register.md#22-geometric).




## 5.3. `HandGestureProcessor.swift` — the State Machine
Seventy-nine lines, no dependencies beyond `CoreGraphics`, and the most instructive file in the
repository.

**States (`:15–21`)** — five, not two:

```text
        .unknown  ──────────────────────────────────┐
            │                                       │
   d < 40pt │                            d ≥ 40pt   │
            ▼                                       ▼
    .possiblePinch  ──── 3 frames ────►  .pinched   │
            ▲                                │      │
            │                                │      │
            └──────────  d ≥ 40pt  ──────────┘      │
                              │                     │
                              ▼                     │
                     .possibleApart ── 3 frames ──► .apart
```

The two `possible*` states are the entire point. A naive implementation has two states and
thresholds on every frame; it flickers on the boundary and produces broken strokes.

**Evidence counters (`:49–65`)** — the mechanism:

```swift
if distance < pinchMaxDistance {
    pinchEvidenceCounter += 1
    apartEvidenceCounter  = 0                                     // note: hard reset
    state = (pinchEvidenceCounter >= evidenceCounterStateTrigger) ? .pinched : .possiblePinch
} else {
    apartEvidenceCounter += 1
    pinchEvidenceCounter  = 0
    state = (apartEvidenceCounter >= evidenceCounterStateTrigger) ? .apart : .possibleApart
}
```

Two tunables, both injected via the initialiser with defaults (`:38`):
`pinchMaxDistance = 40` points and `evidenceCounterStateTrigger = 3` frames. Contradicting
evidence **zeroes** the opposing counter rather than decrementing it — so three consecutive
frames are required, not three out of five. That is a deliberately conservative choice: it
prefers a late decision to a wrong one.

**The buffer-and-replay pattern** lives across the boundary, in
`CameraViewController.handleGestureStateChange` (`:124–152`):

1. **`.possiblePinch` / `.possibleApart`** · *Dot colour:* orange
   *Action:* Append the point pair to `evidenceBuffer`. Draw nothing yet
2. **`.pinched`** · *Dot colour:* green
   *Action:* **Replay every buffered pair into the path**, clear the buffer, then draw the current
   pair
3. **`.apart` / `.unknown`** · *Dot colour:* red
   *Action:* Discard the buffer, close the stroke

Debouncing normally costs the first *N* frames of every gesture — for a 3-frame trigger at 30 fps,
100 ms is lost off the front of every stroke. The buffer means the delay costs **latency but not
data**: when the machine finally commits, it
retroactively includes everything it was unsure about. The `unknown` and `possible` states even
get their own on-screen colour, so the user can *see* the machine hesitating.

This is the template for sign-boundary detection here: hold frames while unsure, commit
retroactively, and never discard the run-up to a sign. See [`APL_S10.1`](#101-lessons-to-carry-across), lesson L4.




## 5.4. `CameraView.swift` — Rendering
A `UIView` subclass with one clever line (`:21–23`):

```swift
override class var layerClass: AnyClass { return AVCaptureVideoPreviewLayer.self }
```

The view's *backing layer* **is** the preview layer. No sublayer to size, no frame to keep in
sync, no chance of drift between the video and the overlay. `layoutSublayers(of:)` (`:35–40`)
then keeps the overlay's frame pinned to the preview layer's bounds.

`showPoints(_:color:)` (`:46–57`) rebuilds a `UIBezierPath` of small arcs every frame and wraps
the assignment in:

```swift
CATransaction.begin()
CATransaction.setDisableActions(true)
overlayLayer.path = pointsPath.cgPath
CATransaction.commit()
```

Without `setDisableActions(true)`, Core Animation animates each path change over its default
0.25 s. At 30 fps that produces visible smearing and lag on data that is already correct. This is
a class of bug that looks like a tracking problem and is not — worth knowing before debugging the
project's own overlay.




## 5.5. `AppDelegate.swift` — the Error Vocabulary
Beyond the four-line scene hook, this file defines the app's failure language (`:25–58`):

```swift
enum AppError: Error {
    case captureSessionSetup(reason: String)
    case visionError(error: Error)
    case otherError(error: Error)
}
```

Three cases, each with a user-facing title and message, and a `display(_:inViewController:)`
helper that wraps any unknown `Error` into `.otherError`. Every throw site in
`setupAVSession()` supplies a specific, human-readable `reason` — *"Could not find a front facing
camera."*, *"Could not create video device input."*, and so on.

And when Vision itself throws mid-stream (`CameraViewController.swift:235–241`), the app
**stops the capture session** and shows an alert. It does not swallow the error and keep running
on stale data.

That is worth naming as a deliberate policy: *degrading silently is worse than stopping.* For an
assistive communication tool, where a silent degradation means putting words in a deaf person's
mouth, this policy is not merely good practice — it is an ethical requirement. See
[`RSK_S8`](../plan/RSK_risk_register.md#8-human-ethical-and-legal).




## 5.6. `SceneDelegate.swift` and the Storyboards
`SceneDelegate` is a `var window: UIWindow?` and nothing else. `Main.storyboard` contains one
view controller whose view's custom class is `CameraView`. `LaunchScreen.storyboard` is empty.
There is no UI to speak of — no buttons, no settings, no menu. The only input gesture in the
entire app is a double-tap to clear.

That minimalism is itself the lesson: a demo that shows **one capability with zero chrome** is
easier to understand, easier to film, and harder to break on stage. Directly relevant to the
5-minute demo video ([`JCR_S7`](../plan/JCR_judging_criteria.md#7-the-5-minute-demo-video)).

---





# 6. WORKING PHILOSOPHY
Ten principles the code encodes. Each is stated as the rule, then the evidence for it.




## 6.1. On-device by Default
*Evidence:* zero network calls; the `network.client` entitlement is declared and never used.

Latency, privacy and offline capability all follow from this. For a product whose input is
continuous video of a person's face and hands in what may be a medical or legal conversation,
processing location is a **product requirement**, not an optimisation.




## 6.2. The Model Is Stateless; the Application Owns All Memory
*Evidence:* `VNDetectHumanHandPoseRequest` is re-run per frame with no history. Every temporal
concept — evidence counters, the buffer, `lastDrawPoint`, `lastObservationTimestamp` — is plain
Swift in application code.




## 6.3. Confidence Is a Gate, Not a Weight
*Evidence:* `guard ... confidence > 0.3 else { return }`.

A low-confidence point is **dropped**, not down-weighted, not interpolated, not smoothed into the
stream. Uncertain input produces no output rather than uncertain output. Compare
[`RSK_S7.1`](../plan/RSK_risk_register.md#71-fabrication), where the opposite behaviour in an LLM is the
single largest risk to this product.




## 6.4. Accumulate Evidence Before Changing State
*Evidence:* `evidenceCounterStateTrigger = 3`, with contradicting evidence zeroing the counter.

Any instantaneous threshold on a noisy signal flickers. Hysteresis is not optional.




## 6.5. Buffer While Uncertain; Commit Retroactively
*Evidence:* `evidenceBuffer` replay in `handleGestureStateChange`.

Debouncing should cost latency, never data.




## 6.6. Convert Coordinates Exactly Once, at the Boundary
*Evidence:* the 1→2 flip and the 2→3 framework call, each appearing exactly once.




## 6.7. Drop Frames; Never Queue Them
*Evidence:* `alwaysDiscardsLateVideoFrames = true`, plus `main.sync` as a back-pressure valve.

Under load, a real-time system must lose data and stay current. Falling behind is worse than
skipping.




## 6.8. Staleness Is a State
*Evidence:* the 2-second `lastObservationTimestamp` reset.

The absence of a signal carries information. A system that only reacts to events will hold a
stale state forever.




## 6.9. Use Cheap Arithmetic for the Semantic Layer
*Evidence:* the whole gesture layer is `hypot()` and a comparison. No second model.

Apple had every incentive to demonstrate more ML here and chose not to. If geometry answers the
question, geometry is faster, deterministic, debuggable, and free.




## 6.10. Fail Loudly and Stop
*Evidence:* typed `AppError`, human-readable reasons at every throw site, and
`cameraFeedSession?.stopRunning()` on a Vision failure.

---





# 7. EXTERNAL TECHNOLOGIES
## 7.1. Frameworks Used
1. **Vision**
   *Used for:* `VNDetectHumanHandPoseRequest`, `VNImageRequestHandler`, `VNHumanHandPoseObservation`
   *Where:* `CameraViewController`, `AppDelegate`
2. **AVFoundation**
   *Used for:* `AVCaptureSession`, `AVCaptureDevice`, `AVCaptureVideoDataOutput`,
   `AVCaptureVideoPreviewLayer`
   *Where:* `CameraViewController`, `CameraView`
3. **UIKit**
   *Used for:* View controllers, `UIBezierPath`, `UIColor`, `UIAlertController`, gesture recognisers
   *Where:* throughout
4. **Core Animation**
   *Used for:* `CAShapeLayer`, `CATransaction`
   *Where:* `CameraView`, `CameraViewController`
5. **Core Graphics**
   *Used for:* `CGPoint`, `CGFloat`, `hypot`
   *Where:* `HandGestureProcessor`

**No third-party dependencies. No package manager. No model file in the bundle.** The hand-pose
model ships inside the OS.

That last point is a genuine strategic advantage of the Apple platform and a genuine constraint:
the model is free, fast and well-tuned, and it cannot be changed, fine-tuned or inspected.




## 7.2. The Vision Hand-pose API in Detail
Verified against Apple's official documentation `[S2] [S3] [S4] [S5]`.



### 7.2.1. `VNDetectHumanHandPoseRequest`
1. **Availability**
   iOS 14.0+, iPadOS 14.0+, Mac Catalyst 14.0+, macOS 11.0+, tvOS 14.0+, **visionOS 1.0+** `[S2]`
2. **Results**
   `[VNHumanHandPoseObservation]`
3. **`maximumHandCount`**
   Default **2**. *"The request orders detected hands by relative size, with only the largest ones
   having key points determined."* `[S3]`
4. **Revisions**
   `VNDetectHumanHandPoseRequestRevision1`

The ordering-by-size behaviour is worth dwelling on: it means **"pick the biggest hand" is free**,
which is a usable first answer to MVP step 1 (isolate the subject). The signer's hands are
nearest the camera, therefore largest.



### 7.2.2. The 21 joints
`VNHumanHandPoseObservation.JointName` `[S5]` — four per finger plus the wrist:

| Group (`JointsGroupName`) | Joints, root → tip                                    |
| :------------------------ | :---------------------------------------------------- |
| `.thumb`                  | `thumbCMC` · `thumbMP` · `thumbIP` · `thumbTip`       |
| `.indexFinger`            | `indexMCP` · `indexPIP` · `indexDIP` · `indexTip`     |
| `.middleFinger`           | `middleMCP` · `middlePIP` · `middleDIP` · `middleTip` |
| `.ringFinger`             | `ringMCP` · `ringPIP` · `ringDIP` · `ringTip`         |
| `.littleFinger`           | `littleMCP` · `littlePIP` · `littleDIP` · `littleTip` |
| —                         | `wrist`                                               |

**The sample uses 2 of these 21.** The remaining 19 are exactly the signal a handshape classifier
needs, and they are available at zero additional cost — the model computes them whether or not
they are read.



### 7.2.3. Chirality
`VNHumanHandPoseObservation.chirality` returns a `VNChirality` (`.left` / `.right` / `.unknown`)
and is available **iOS 15.0+ / visionOS 1.0+** `[S4]` — one release *later* than the request
itself, which is why this 2020 sample does not use it.

For sign language this is not a nicety. Dominant and non-dominant hand carry different
grammatical roles in every sign language, so a system that cannot tell them apart is missing a
feature, not a label.



### 7.2.4. Adjacent Vision requests relevant to the MVP
1. **`VNDetectHumanBodyPoseRequest`**
   *Availability:* iOS 14.0+ `[S6]`
   *Relevance to [`SCR`](../plan/scribbles.md) MVP:* Step 2 — torso, shoulders, arms; signing space
   is defined relative to the body
2. **`VNDetectHumanBodyPose3DRequest`**
   *Availability:* iOS 17.0+ `[S7]` — *"detects points on human bodies in 3D space, relative to the
   camera"*, and *"if the system allows it, the request uses depth information to improve the
   accuracy"*
   *Relevance to [`SCR`](../plan/scribbles.md) MVP:* Step 3 — the closest first-party answer to "3D
   skeleton"
3. **`VNGeneratePersonInstanceMaskRequest`**
   *Availability:* iOS 17.0+ `[S8]` — *"produces a mask of individual people it finds in the input
   image"*
   *Relevance to [`SCR`](../plan/scribbles.md) MVP:* Step 1 — per-person masks, i.e. genuinely
   isolating one signer from bystanders

> **Note:** all three of these post-date the sample. The repository shows Apple's 2020 answer;
> Apple's 2023 platform answers two more of the four MVP steps out of the box. That matters for
> [`ARC_S6`](../plan/ARC_architecture.md#6-the-recommended-architecture), where an iOS-native track is one of the options.

---





# 8. WHAT THE REPOSITORY DOES NOT DO
The gap between this sample and the product.

1.  **Second hand**
    `maximumHandCount = 1`. Two-handed signs are a large fraction of any sign language's lexicon
2.  **19 of 21 joints**
    Only the two fingertips are read. No handshape information at all
3.  **Chirality**
    Not used (API postdates the sample). Dominant/non-dominant roles are lost
4.  **Face and body**
    No `VNDetectHumanBodyPoseRequest`, no face landmarks. Non-manual grammar is invisible — see
    [`RSK_S3.1`](../plan/RSK_risk_register.md#31-non-manual-grammar)
5.  **Any temporal model**
    The 3-frame counter is the entire memory. No sequence model, no RNN, no transformer
6.  **Vocabulary**
    The output alphabet is `{pinched, apart}`. Two symbols
7.  **Multi-person**
    Nothing distinguishes the intended subject from a bystander beyond hand size
8.  **Depth / true 3D**
    2D normalised points only
9.  **Text or speech output**
    The output is ink on a layer
10. **Recording, export, persistence**
    Nothing survives a double-tap, let alone app termination
11. **Orientation handling**
    Portrait-locked; `orientation: .up` is hard-coded
12. **Rear camera**
    Front-facing only
13. **Any evaluation harness**
    No tests, no metrics, no ground truth
14. **Portability**
    Swift, UIKit, Apple-only. The judges expect Python `[D3_p42]`

Items 1–8 are the technical distance between the sample and a sign-language system. Item 14 is
the reason this is a **reference**, not a starting codebase.

---





# 9. RUNNING IT
Optional, but seeing the hysteresis behave on a live camera is worth twenty minutes.

1. **Hardware**
   A Mac, plus a **physical** iPhone or iPad on iOS 14+. The Simulator has no camera
2. **Software**
   Xcode 12 or later
3. **Signing**
   Open the project, select the `HandPose` target → *Signing & Capabilities* → set the Development
   Team. `SAMPLE_CODE_DISAMBIGUATOR` derives a unique bundle ID from it
4. **Run**
   Build to the device, grant camera permission, hold one hand up in portrait, pinch thumb and index
   together to draw. Double-tap to clear

**What to watch for:** the fingertip dots turn **orange** exactly while the state machine is
undecided, **green** while committed to drawing, **red** when committed to not drawing. Waving a
hand out of frame and back shows the 2-second reset. That orange interval is the buffer-and-replay
window of [`APL_S5.3`](#53-handgestureprocessorswift--the-state-machine) made visible.

---





# 10. RELEVANCE TO SIMPLYNEXT
## 10.1. Lessons to Carry Across
1.  **L1**
    *Lesson:* Keep the ML layer stateless; own all temporal state in plain code
    *Source:* [`APL_S6.2`](#62-the-model-is-stateless-the-application-owns-all-memory)
    *Application:* Landmark extractor returns per-frame features only. Segmentation, smoothing and
    history live in a project module
2.  **L2**
    *Lesson:* Gate on confidence; drop rather than guess
    *Source:* [`APL_S6.3`](#63-confidence-is-a-gate-not-a-weight)
    *Application:* Per-joint-group thresholds, tuned and measured — not one magic `0.3`
3.  **L3**
    *Lesson:* Hysteresis before any state change
    *Source:* [`APL_S6.4`](#64-accumulate-evidence-before-changing-state)
    *Application:* *N*-consecutive-frame trigger for sign-boundary detection, with contradicting
    evidence zeroing the counter
4.  **L4**
    *Lesson:* Buffer while uncertain, commit retroactively
    *Source:* [`APL_S5.3`](#53-handgestureprocessorswift--the-state-machine)
    *Application:* Ring buffer of landmark frames; when a sign boundary commits, the whole run-up is
    already captured
5.  **L5**
    *Lesson:* Show the machine hesitating
    *Source:* [`APL_S5.3`](#53-handgestureprocessorswift--the-state-machine)
    *Application:* Three-state UI: *listening* / *unsure* / *committed*. Directly serviceable as an
    honesty mechanism — see [`RSK_S7.4`](../plan/RSK_risk_register.md#74-confidence-and-honesty)
6.  **L6**
    *Lesson:* Smooth the output, not the decision
    *Source:* [`APL_S5.1`](#51-cameraviewcontrollerswift--capture-and-orchestration)
    *Application:* Low-pass the rendered landmark trail for the UI; feed the model the raw, gated
    stream
7.  **L7**
    *Lesson:* Drop frames under load
    *Source:* [`APL_S6.7`](#67-drop-frames-never-queue-them)
    *Application:* Bounded queue, drop-oldest. Never let the buffer grow
8.  **L8**
    *Lesson:* Staleness is a state
    *Source:* [`APL_S6.8`](#68-staleness-is-a-state)
    *Application:* An "N seconds without hands" timeout closes the utterance and flushes it to
    output
9.  **L9**
    *Lesson:* Convert coordinates once, at boundaries
    *Source:* [`APL_S6.6`](#66-convert-coordinates-exactly-once-at-the-boundary)
    *Application:* One normalisation step from pixel space into body-relative signing space; every
    downstream module sees only the latter
10. **L10**
    *Lesson:* Fail loudly and stop
    *Source:* [`APL_S6.10`](#610-fail-loudly-and-stop)
    *Application:* Never emit a "best guess" sentence when the pipeline is broken. Say so
11. **L11**
    *Lesson:* Zero-chrome demo
    *Source:* [`APL_S5.6`](#56-scenedelegateswift-and-the-storyboards)
    *Application:* One screen, one capability, no settings, for the 5-minute video
12. **L12**
    *Lesson:* Cheap arithmetic where it suffices
    *Source:* [`APL_S6.9`](#69-use-cheap-arithmetic-for-the-semantic-layer)
    *Application:* Motion energy, hand-in-signing-space tests, and velocity thresholds are geometry
    — do not spend a model on them




## 10.2. Swift → Python Port Table
The project stack is Python `[D3_p42]`. This maps every Apple concept to its likely equivalent.

1.  **`AVCaptureSession` + `AVCaptureVideoDataOutput`**
    *Purpose:* Frame source
    *Python equivalent:* `cv2.VideoCapture`, or a WebRTC/browser track for a web demo
2.  **`alwaysDiscardsLateVideoFrames = true`**
    *Purpose:* Bounded latency
    *Python equivalent:* An explicit `queue.Queue(maxsize=1)` with drop-oldest in the capture thread
3.  **`VNImageRequestHandler`**
    *Purpose:* Per-frame inference entry
    *Python equivalent:* `HandLandmarker.detect_for_video(mp_image, timestamp_ms)`
4.  **`VNDetectHumanHandPoseRequest`**
    *Purpose:* 21 hand joints
    *Python equivalent:* MediaPipe **Hand Landmarker** — 21 landmarks, plus handedness `[S9]`
5.  **`VNDetectHumanBodyPoseRequest` + face**
    *Purpose:* Body + face landmarks
    *Python equivalent:* MediaPipe **Holistic Landmarker** — 543 landmarks: 33 pose + 468 face +
    21×2 hands `[S10]`
6.  **`VNHumanHandPoseObservation.chirality`**
    *Purpose:* Left/right hand
    *Python equivalent:* MediaPipe `handedness` field `[S9]`
7.  **`VNRecognizedPoint.confidence`**
    *Purpose:* Trust score
    *Python equivalent:* Landmark `visibility` / `presence`, and the task's
    `min_hand_detection_confidence` / `min_tracking_confidence`
8.  **`location` (normalised, bottom-left)**
    *Purpose:* 2D position
    *Python equivalent:* MediaPipe normalised landmarks, **top-left origin** — ⚠ the y-flip is *not*
    needed; porting it blindly inverts the image
9.  **— (no equivalent in the sample)**
    *Purpose:* Metric 3D
    *Python equivalent:* MediaPipe **world landmarks**: x, y, z in metres, origin at the hand's
    geometric centre `[S9]`
10. **`VNGeneratePersonInstanceMaskRequest`**
    *Purpose:* Per-person mask
    *Python equivalent:* MediaPipe Image Segmenter, or a person-detector crop
11. **`HandGestureProcessor`**
    *Purpose:* Temporal semantics
    *Python equivalent:* A project module — pure functions over landmark frames, no camera or model
    imports
12. **`CAShapeLayer` + `CATransaction`**
    *Purpose:* Overlay rendering
    *Python equivalent:* `cv2` overlay, or a canvas in the web UI
13. **`AppError` enum**
    *Purpose:* Typed failures
    *Python equivalent:* A small exception hierarchy surfaced in the UI, not logged and swallowed

> **Warning — the y-flip trap.** Vision's normalised space has its origin at the **bottom-left**;
> MediaPipe's at the **top-left**. Apple's `y := 1 - y` line exists to reconcile Vision with
> AVFoundation. Copying that line into a MediaPipe pipeline flips the image upside down. It is
> the single most likely bug to arise from reading this repository, so it is called out here and
> again in [`SYN`](../ref_repo/apple/SYN_apple_synthesis.md).




## 10.3. The Architectural Boundary to Preserve
The one structural property to carry over verbatim: `HandGestureProcessor` imports **only**
`CoreGraphics`. It has no knowledge of cameras, of Vision, or of the UI. Its input is a stream of
point pairs; its output is a state.

The equivalent module — the **utterance segmenter** — must obey the same rule: it takes a stream
of landmark frames and emits sign-boundary events, and it imports neither the camera layer, nor the
landmark model, nor the LLM client. That makes it testable against recorded
fixtures, tunable without a camera, and swappable without touching anything else. In a four-day
build with a live demo at the end, that boundary is what keeps the system debuggable.




## 10.4. Questions This Repository Does Not Answer
The Apple sample is silent on every hard problem in this product:

- how to segment continuous signing into discrete units;
- how to represent non-manual grammar;
- how to map a sequence of recognised units onto fluent spoken-language text;
- how to attribute utterances when two people sign at once;
- how to know when the system is wrong.

Those are the subject of [`ARC`](../plan/ARC_architecture.md) and
[`RSK`](../plan/RSK_risk_register.md). The Apple repository provides a solid floor and nothing
above the knee.

---





# 11. SOURCES
1.  **`[S1]`** · *Reliability:* Official
    *Source:* Apple, *Detect Body and Hand Pose with Vision*, WWDC20 session 10653 —
    https://developer.apple.com/videos/play/wwdc2020/10653/ (cited by `ref_repo/apple/README.md`)
2.  **`[S2]`** · *Reliability:* Official
    *Source:* Apple Developer Documentation, `VNDetectHumanHandPoseRequest` —
    https://developer.apple.com/documentation/vision/vndetecthumanhandposerequest
3.  **`[S3]`** · *Reliability:* Official
    *Source:* Apple Developer Documentation, `maximumHandCount` —
    https://developer.apple.com/documentation/vision/vndetecthumanhandposerequest/maximumhandcount
4.  **`[S4]`** · *Reliability:* Official
    *Source:* Apple Developer Documentation, `VNHumanHandPoseObservation.chirality` —
    https://developer.apple.com/documentation/vision/vnhumanhandposeobservation/chirality
5.  **`[S5]`** · *Reliability:* Official
    *Source:* Apple Developer Documentation, `VNHumanHandPoseObservation.JointName` —
    https://developer.apple.com/documentation/vision/vnhumanhandposeobservation/jointname
6.  **`[S6]`** · *Reliability:* Official
    *Source:* Apple Developer Documentation, `VNDetectHumanBodyPoseRequest` —
    https://developer.apple.com/documentation/vision/vndetecthumanbodyposerequest
7.  **`[S7]`** · *Reliability:* Official
    *Source:* Apple Developer Documentation, `VNDetectHumanBodyPose3DRequest` —
    https://developer.apple.com/documentation/vision/vndetecthumanbodypose3drequest
8.  **`[S8]`** · *Reliability:* Official
    *Source:* Apple Developer Documentation, `VNGeneratePersonInstanceMaskRequest` —
    https://developer.apple.com/documentation/vision/vngeneratepersoninstancemaskrequest
9.  **`[S9]`** · *Reliability:* Official
    *Source:* Google AI Edge, *Hand landmarks detection guide* —
    https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker
10. **`[S10]`** · *Reliability:* Official
    *Source:* Google AI Edge, *Holistic landmarks detection task guide* —
    https://ai.google.dev/edge/mediapipe/solutions/vision/holistic_landmarker
11. **`[S11]`** · *Reliability:* Primary
    *Source:* The repository itself: `ref_repo/apple/` at commit `ec30ff6`, *Republish sample code
    project.*

All line numbers in this document refer to the files as they stand at `[S11]`.

---





# 12. CHANGE LOG
1. **2026-08-28** · *Author:* Claude (Opus 5)
   *Change:* Created from a full read of all five Swift files, the project configuration, and
   Apple's official API documentation.
2. **2026-08-28** · *Author:* Claude (Opus 5)
   *Change:* Reformatted to the revised conventions in
   [`RIX_S4`](../ref_index.md#4-markdown-formatting-rules): bold title, collapsible `# METADATA`,
   `#`-level numbered sections, HTML anchors removed, padded tables, third-person voice,
   placeholders for unfinished content.
3. **2026-08-28** · *Author:* Claude (Opus 5)
   *Change:* Applied the revised [`RIX_S4.4`](../#44-vertical-spacing) heading spacing and the
   [`RIX_S4.5`](../#45-tables-and-numbered-lists) table-versus-numbered-list rule: tables whose rows exceeded 100
   characters became numbered lists.
