**ARCHITECTURE — CONFIRMATION, SOURCES AND ALTERNATIVES**





# METADATA
<details>
<summary>Document code, status, review date, and usage instructions.</summary>

| Field                      | Value                            |
| :------------------------- | :------------------------------- |
| **Code**                   | `ARC`                            |
| **Status**                 | Live                             |
| **Last reviewed**          | 2026-09-04                       |
| **Source of truth for**    | Technical direction              |
| **Parent**                 | [`SCR`](scribbles.md)            |
| **Scored against**         | [`JCR`](JCR_judging_criteria.md) |
| **Problems catalogued in** | [`RSK`](RSK_risk_register.md)    |
| **Evidence base**          | Ten repository syntheses in `doc/` |

**For the team.** This document tests the MVP in [`SCR`](scribbles.md) step by step against
published evidence, states the architecture to build, and ranks the alternatives by cost, hardware
and risk. [`ARC_S7.2`](#72-the-four-reference-repositories-compared) compares the four reference
repositories head-to-head and names the one the perception layer is built on; its evidence base is
the four repository syntheses [`APS`](../doc/APS_apple_synthesis.md),
[`MPS`](../doc/MPS_mediapipe_synthesis.md), [`DHS`](../doc/DHS_depthai_synthesis.md) and
[`OPS`](../doc/OPS_openpose_synthesis.md). [`ARC_S7.7`](#77-the-six-translation-repositories-compared)
does the same for the six translation repositories, and
[`ARC_S5.6`](#56-the-four-routes-from-skeleton-to-text) ranks the routes from pose to text. The
twenty-four decisions in [`ARC_S9`](#9-decisions) are **Proposed** and await team sign-off; the
master plan `PLN` is blocked on them.

**For the assistant.** Every external claim carries a source tag resolving to
[`ARC_S10`](#10-sources). Preprint-derived figures are marked `⚠` and must not be restated without
that mark. Decision status in [`ARC_S9`](#9-decisions) changes only on explicit team instruction.

</details>

---





# 1. SCOPE
## 1.1. The Claim Under Test
From [`SCR`](scribbles.md), *Current MVP (concept)*:

1. Recognise the focus and isolate the person(s) from environment noise.
2. Track multiple points (as many as possible) on the hands and face.
3. Translate the points' motion into a 3D skeleton.
4. Use the skeleton's movements to translate them into coherent conversational text / audio.

Plus, from *ISSUES*: **(a)** training an LLM (methodology), **(b)** AI memory loss during training,
or hallucination.




## 1.2. Verdict Summary
1. **1. Isolate the subject**
   *Verdict:* ✅ **Confirmed, simplify it**
   *One-line reason:* Free from the detector's own ordering; full segmentation is a UX feature, not
   a recognition requirement
2. **2. Track many points**
   *Verdict:* ⚠️ **Confirmed, but reframe**
   *One-line reason:* "As many as possible" is the wrong target. *Which* points — the face — is what
   the evidence says matters
3. **3. Build a 3D skeleton**
   *Verdict:* ⚠️ **Partially confirmed**
   *One-line reason:* Pose is the right representation. Metric 3D from one RGB camera is not
   reliable; use body-relative normalised coordinates
4. **4. Skeleton → conversational text**
   *Verdict:* ⚠️ **Confirmed as the goal, wrong as a single step**
   *One-line reason:* This is three problems (segment, recognise, translate), and published
   gloss-free translation quality is low
5. **(a) Training an LLM**
   *Verdict:* ❌ **Rejected**
   *One-line reason:* No LLM is trained. The project trains a small sequence classifier and
   *prompts* an LLM
6. **(b) Memory loss in training**
   *Verdict:* ❌ **Category error**
   *One-line reason:* The runtime risk is context rot and hallucination, not catastrophic forgetting

Each verdict is argued in [`ARC_S2`](#2-step-1--isolating-the-subject) through
[`ARC_S5`](#5-step-4--skeleton-to-conversational-text).

---





# 2. STEP 1 — ISOLATING THE SUBJECT
## 2.1. Verdict: Confirmed, at Lower Cost Than Assumed
The scribble proposes background separation in the manner of *"Google Meet & Zoom blur
background"*. That analogy is misleading in one important way: **Meet and Zoom blur the background
for the benefit of the human viewer, not the recognition model.** A landmark model does not see a
background; it sees a person and emits joint coordinates. Blurring first adds cost and adds a
failure mode (a segmentation error can erase a hand) without improving the signal.

The genuinely necessary function is narrower: **decide which person in frame is the signer, and
follow that person.** Two facts make this cheap:

- Apple's Vision hand-pose request *"orders detected hands by relative size, with only the largest
  ones having key points determined"* `[S1]`. The signer is nearest the camera, therefore largest.
  Subject selection is a by-product of detection.
- MediaPipe exposes the same handle through the number of hands requested and the per-detection
  confidence scores `[S2]`.




## 2.2. Recommended Build
1. **Primary** · *Cost:* free
   *Purpose:* Largest / most central detected person, held with hysteresis (see
   [`APR_S6.4`](../ref_repo/tracking/apple/APR_apple_report.md)) so the subject does not flip between
   people mid-sentence
2. **Optional, later** · *Cost:* moderate
   *Purpose:* Explicit per-person masks — `VNGeneratePersonInstanceMaskRequest` on iOS 17+ `[S3]`,
   or MediaPipe Image Segmenter
3. **Presentation only** · *Cost:* cheap, cosmetic
   *Purpose:* Background blur in the preview, purely so the user can see who the system is listening
   to

> **Decision:** subject selection is a **tracking** problem, not a segmentation problem. Build the
> hysteresis-held largest-person tracker; do not build segmentation for the hackathon.

Residual issues are catalogued at
[`RSK_S2.3`](RSK_risk_register.md#23-subject-selection-and-framing) and
[`RSK_S5`](RSK_risk_register.md#5-multi-person-and-conversation).

---





# 3. STEP 2 — WHICH POINTS TO TRACK
## 3.1. Verdict: Confirmed, with a Corrected Objective
More landmarks are not better; the **right** landmarks are. The evidence is unusually clear here,
and it points somewhere the scribble treats as an afterthought — the face.

Michael Erard's widely-cited critique of sign-language gloves makes the linguistic point plainly:
such devices *"misconstrue the nature of ASL (and other sign languages) by focusing on what the
hands do"*, when key parts of ASL grammar include *"raised or lowered eyebrows, a shift in the
orientation of the signer's torso, or a movement of the mouth"* `[S4]`. The same argument is made
in the peer-reviewed literature `[S5]`.

Quantitatively — ⚠ these figures come from a **preprint**, so treat them as indicative rather than
settled: facial expressions, head movement, eye gaze and body posture are reported to carry *up to
30% of sign meaning*, and adding facial features is reported to cut confusion between visually
similar signs *from 37% to 11%* `[S6]`.

There is a second, harder finding in the same literature: facial expression in sign language is
**doubly loaded**, encoding both grammatical structure and affect, so the same movement can be
syntax or emotion `[S7]`. Upper-face markers carry syntactic and prosodic structure; the mouth
carries lexical and morphological information `[S7]`.




## 3.2. The Landmark Budget
1. **Hands**
   *Landmarks:* 21 per hand, ×2 = **42**
   *Why it is in the budget:* Handshape, orientation, location, movement — the manual channel
2. **Handedness / chirality**
   *Landmarks:* 1 label per hand
   *Why it is in the budget:* Dominant vs non-dominant hand carry different grammatical roles.
   Available in MediaPipe `[S2]`; in Vision from iOS 15 `[S8]`
3. **Upper body / pose**
   *Landmarks:* ~11 of 33 (shoulders, elbows, wrists, hips)
   *Why it is in the budget:* Signing space is defined **relative to the body**. Without the torso,
   hand positions are meaningless
4. **Face — upper (brows, eyes)**
   *Landmarks:* small subset
   *Why it is in the budget:* Syntactic and prosodic markers `[S7]`
5. **Face — mouth**
   *Landmarks:* small subset
   *Why it is in the budget:* Lexical and morphological markers, including mouthing `[S7]`
6. **Face — the other ~400**
   *Landmarks:* **excluded**
   *Why it is in the budget:* Cheek and jaw mesh detail is cost without signal

MediaPipe's Holistic Landmarker emits 543 landmarks — 33 pose, 468 face, 21 per hand `[S9]`. The
pipeline should **consume all of them and feed a curated subset to the model.** Passing 543 × 3
floats per frame into a classifier is a reliable way to overfit a small dataset.

**Two published systems set this budget, and both are far below 543.** Added 2026-09-04.

| System                 | Venue      | Body |     Hands | Face                   |  Total |
| :--------------------- | :--------- | ---: | --------: | :--------------------- | -----: |
| `RSA` SAM-SLR          | CVPR 21 W  |    7 | 10 × 2    | **none**               | **27** |
| `RSL` SLRT, minimal    | CVPR 23    |   11 | 21 × 2    | 10 (mouth)             | **63** |
| `RSL` SLRT, maximal    | NeurIPS 22 |   11 | 21 × 2    | 10 mouth + 16 other    | **79** |

Four facts follow, each confirmed independently by both systems `[S25] [S26]`:

1. **No published system uses the full face mesh.** The largest face budget observed is 26 points
   of 68 available; nineteen of SLRT's thirty-nine configurations use ten
2. **The mouth is the face group that never disappears** in SLRT — consistent with items 4 and 5
   above, and with the linguistic claim that the mouth carries lexical content `[S7]`
3. **Neither system decimates the hands below ten points each**, and SLRT keeps all 42 despite
   having the machinery to reduce them
4. **`RSA`'s ten hand indices are directly reusable**, because COCO-WholeBody and MediaPipe share
   the 21-point hand topology and index order: `0` (wrist), `4`, `8`, `12`, `16`, `20` (the five
   fingertips) and `5`, `9`, `13`, `17` (the base knuckles). **The wrist, every fingertip, and each
   non-thumb finger's anchoring knuckle** — [`SAS_S4`](../doc/SAS_sam_slr_synthesis.md#4-twenty-seven-points)

> **Decision:** start from `RSA`'s 27 points plus a mouth subset — roughly **37** — and measure
> whether adding the remaining hand joints or brow points earns its place. This is a **narrower**
> budget than this section originally proposed, and it is narrower on evidence. Recorded as
> decision 17.

> **Decision:** track hands + handedness + upper-body pose + a curated face subset. Explicitly
> reject the full 468-point face mesh as a model input. Record the exclusion: a measured
> demonstration that the obvious choice performed worse is exactly the evidence
> [`JCR_S2.3`](JCR_judging_criteria.md#23-c3--effectiveness-of-the-solution-20) rewards.

---





# 4. STEP 3 — THE "3D SKELETON"
## 4.1. Verdict: Right Instinct, Over-Specified
Pose as an intermediate representation is well supported. The trade-off is real and measurable.

**Dimensionality.** A 512×512 RGB frame carries over 786,000 pixel-level features; a pose vector
is typically fewer than 150 numbers `[S10]`. That is a ~5,000× reduction — which is why pose-based
models train fast on small datasets, and why they are robust to background, lighting and clothing
`[S10]`. For a four-day hackathon with no large dataset, that is close to decisive.

**But pose is not free.** Reported accuracies on isolated sign recognition — ⚠ from a preprint's
survey table `[S10]`:

| Dataset   | RGB-based          | Skeleton/pose-based |
| :-------- | :----------------- | :------------------ |
| WLASL-100 | 65.89 – 80.72%     | 55.43 – **81.47%**  |
| AUTSL     | 93.53 – **96.55%** | 93.13 – 96.47%      |

Read honestly: **the ranges overlap and neither wins outright.** The best pose model beats the
best RGB model on WLASL-100 and loses narrowly on AUTSL. Pose is *competitive*, not superior. What
it reliably buys is cheapness, speed, and privacy — pose-based representations are explicitly
named as a **privacy-preserving** design choice in the low-resource sign-language literature
`[S11]`, which matters when the input is continuous video of someone's face.

**A better citation than the preprint, added 2026-09-04.** `RSA` — the CVPR 2021 challenge winner —
reports a controlled modality ablation with one system on one benchmark `[S26]`. On WLASL-2000,
the **keypoint** modality alone scores **51.50%** top-1 against **RGB frames' 47.51%** and optical
flow's 40.46%. On AUTSL validation:

| Ensemble                | Top-1     | Top-5     |
| :---------------------- | --------: | --------: |
| Skeleton only           | **96.11** |     99.43 |
| RGB + optical flow      |     95.77 |     99.52 |
| Everything, incl. RGB-D | **97.10** | **99.73** |

> **Skeleton alone reaches 96.11%; a six-modality RGB-D ensemble reaches 97.10%.** The difference
> is **0.99 points**, bought with two extra deep video models, two optical-flow computations and a
> depth sensor. The authors' own late-fusion weights put the skeleton highest of all six streams.
>
> This does two things for this document. It replaces a preprint survey table with a single
> system's controlled comparison, and it **prices the depth camera** that
> [`ARC_S7.5`](#75-p4p5--depth-and-glasses-as-roadmap-items) rejects on scalability grounds. The
> rejection now has a number.

⚠ Two variables move between AUTSL (98.42% test) and WLASL-2000 (58.73%) for the same system —
vocabulary size and recording conditions — so neither is isolated. See
[`ARC_S5.2`](#52-state-of-the-art).




## 4.2. Available Depth Information
1. MediaPipe **hand world landmarks**
   *Output:* x, y, z in metres, origin at the hand's geometric centre `[S2]`
   *Reality:* Real 3D **within the hand**. Does not locate the hand in the room
2. **MediaPipe normalised landmarks**
   *Output:* x, y in image space, z as relative depth
   *Reality:* z is a weak, relative signal — not metric. Confirmed in the source: the `z` scale
   factor is `0.4` × the **crop** width, not the image width `[S21]`
3. **MediaPipe Holistic pose world landmarks**
   *Output:* x, y, z in metres, origin at the **hip centre**, with hand world landmarks
   *"translated so that wrist from hand matches wrist from pose in pose coordinates system"*
   `[S21]`
   *Reality:* Not metric depth from the camera, but a **body-centred metric frame** — which is what
   [`ARC_S4.3`](#43-recommended-representation) actually needs. See
   [`MPS_S7`](../doc/MPS_mediapipe_synthesis.md#7-what-it-does-not-do)
4. **Apple `VNDetectHumanBodyPose3DRequest`**
   *Output:* *"points on human bodies in 3D space, relative to the camera"*, and *"if the system
   allows it, the request uses depth information to improve the accuracy"* `[S12]`
   *Reality:* Genuine 3D — but iOS 17+, and the accuracy caveat is Apple's own
5. **A depth sensor (LiDAR, stereo, TrueDepth)**
   *Output:* Metric depth
   *Reality:* Accurate, and it kills the "any device with a camera" promise. `RDH` demonstrates
   exactly this trade with the OAK-D's `-xyz` mode —
   [`DHS_S2`](../doc/DHS_depthai_synthesis.md#2-relevance). See
   [`ARC_S6.4`](#64-latency-budget)




## 4.3. Recommended Representation
Not a metric 3D skeleton. A **body-normalised pose representation**:

1. Take 2D normalised landmarks plus MediaPipe world landmarks for each hand.
2. Re-express hand positions **relative to the signer's own body** — origin at mid-shoulder,
   scale by shoulder width. This makes the representation invariant to distance from camera, to
   the signer's size, and to where they stand in frame.
3. Keep per-hand world landmarks as a separate, already-metric handshape descriptor.
4. Add velocity and acceleration as explicit derived features rather than hoping the model infers
   them from a short window.

This is the same discipline as
[`APR_S6.6`](../ref_repo/tracking/apple/APR_apple_report.md): convert once, at the boundary, and let every
downstream module see only signing-space coordinates.

> **Note — step 2 is already written, in a library.** Added 2026-09-04. `RSP`'s `Pose.normalize()`
> translates every point so the **shoulder midpoint is the origin** and scales so the **mean
> inter-shoulder distance is 1**, selecting the shoulder points automatically for six pose formats
> `[S27]`. It is MIT-licensed and installs with three dependencies —
> [`SPS_S3.1`](../doc/SPS_sign_pose_synthesis.md#31-normalize--already-written). Two details
> matter: the centre and scale are computed **over the whole sequence**, so the transform is rigid
> and relative motion between frames is preserved — per-frame normalisation would destroy exactly
> the signal the classifier needs; and ⚠ it is a **batch** operation, so the live path must
> normalise per buffered utterance window or hold a running shoulder estimate. That is a decision,
> not an inheritance.

> **Note — two additions to the four steps above.** Both come from `RSP` `[S27]`:
> **(a) Correct the wrists first.** MediaPipe Holistic emits each wrist twice — once from the pose
> model, once from the hand model. When the hand model fails, its wrist has zero confidence while
> the pose model's is valid. Since the hand wrist is the **origin of the handshape descriptor**, a
> collapsed wrist silently corrupts every hand landmark expressed relative to it.
> `correct_wrists()` substitutes the pose wrist, per frame, per hand.
> **(b) Canonicalise hand rotation.** `normalize_hands_3d()` rotates each hand into a frame defined
> by the `WRIST`, `PINKY_MCP` and `INDEX_FINGER_MCP` plane, making handshape independent of hand
> orientation. Step 3 above keeps per-hand world landmarks but does not canonicalise their
> rotation; it should.

> **Note — a third normalisation scheme worth an ablation.** The literature records per-*object*
> standardisation — separate mean and standard deviation for body, face and each hand — as an
> alternative to body-relative scaling `[S28]`. `RSP` implements it as
> `normalize_distribution(axis=...)`. It is a cheap comparison.

> **Note — step 2 is partly already built.** The reading of the MediaPipe source recorded in
> [`MPR_S7.1`](../ref_repo/tracking/google-mediapipe/MPR_mediapipe_report.md#71-holistic-landmarker) shows
> that `HolisticLandmarker` emits hand world landmarks **already translated into the pose
> coordinate system**, and pose world landmarks with the origin at the hip centre `[S21]`. What
> remains for the project is the **scale** normalisation (by shoulder width) and the derived
> velocity and acceleration features. The origin translation does not need to be written.
> This is a reduction in scope, not a change of d irection.

> **Decision:** ship body-normalised 2D + per-hand world landmarks. Treat true metric 3D as a
> roadmap item tied to hardware ([`ARC_S6.4`](#64-latency-budget)), not an MVP requirement.

---





# 5. STEP 4 — SKELETON TO CONVERSATIONAL TEXT
This is the whole product, and the scribble compresses three distinct problems into one line.




## 5.1. Three Problems Inside Step 4
1. **Segmentation** — where does one sign end and the next begin?
   Continuous signing has no spaces. Signs bleed into each other (coarticulation)
2. **Recognition** — which sign was that?
   A closed-vocabulary classification problem over a temporal window
3. **Translation** — what sentence does that sequence mean?
   Sign languages are not word-ordered spoken language. Grammar, spatial reference and non-manual
   marking all have to be resolved

Systems that skip straight from video to sentences are called **gloss-free sign language
translation**, and their published quality is the single most important number in this document.




## 5.2. State of the Art
⚠ The figures below come from **preprints and search summaries of preprints**, not from
peer-reviewed venues. They are directionally reliable and precisely unreliable; do not put an
exact number on a slide without opening the paper.

- Recent gloss-free translation reports a **BLEU-4 around 10.75** on the relevant benchmark,
  described as a new state of the art, beating the previous best by **+0.64 BLEU-4** `[S13]`.
- Training on How2Sign alone yields **13.7 BLEU-4**, versus **22.1 BLEU-4** with large-scale
  YouTube-ASL pre-training `[S14]`.

For calibration: a BLEU-4 in the 10–22 range is *far* below usable machine translation between
written languages. **Free-form, open-vocabulary sign-to-sentence translation is not a solved
problem, and it will not be solved in four days.**

There is a second warning. A February 2026 study by Mercanoglu Sincan, Low, Asasi and Bowden
re-implemented recent gloss-free models in a unified framework and found that *"many of the
performance gains reported in the literature often diminish when models are evaluated under
consistent conditions"* `[S15]`. So even those low numbers are optimistic.

> **Warning:** any submission implying open-domain sign-language translation will be judged
> against this literature by anyone who knows it. That is a direct route to **0 on
> [`JCR_S2.2`](JCR_judging_criteria.md#22-c2--original--innovative-idea-20) (originality —
> "existing solutions address it effectively")** *and* a credibility loss on C3 and C5.

**The other end of the range, added 2026-09-04.** The figures above are *gloss-free*. With **gloss
supervision**, on a closed domain, the same field does far better. `RSL`'s TwoStream network
reports, from peer-reviewed work `[S25]`:

| System              | Dataset       | ROUGE |    BLEU-4 |
| :------------------ | :------------ | ----: | --------: |
| TwoStream-SLT       | Phoenix-2014T | 53.48 | **28.95** |
| TwoStream-SLT       | CSL-Daily     | 55.72 | **25.79** |
| SingleStream-SLT    | Phoenix-2014T | 53.08 |     28.57 |

Recognition-only word error rates on the same corpora are **18.8**, **19.3** and **25.3** `[S25]`.

> **Three conditions must travel with 28.95 BLEU-4, or quoting it is dishonest.**
> **(a)** Phoenix-2014T is **German Sign Language weather forecasts** — 1,231 glosses, one topic,
> **nine signers**.
> **(b)** It uses **gloss supervision**: human sign-by-sign annotation of the training set.
> **(c)** The field's own methodological guidance is to *"Focus on datasets beyond
> RWTH-PHOENIX-Weather-2014T"* and to *"Openly discuss the limited size and linguistic domain of
> this dataset"* `[S28]`.

**What this changes.** The conclusion above stands: open-vocabulary translation is unsolved. What
these figures add is the shape of the trade — **the gap between BLEU-4 ≈ 10 and ≈ 29 is almost
entirely the cost of annotation and the narrowness of the domain.** That is precisely the trade
this project makes by closing the vocabulary, and stating it that way is stronger than stating the
low number alone.

**And the number that actually sets the vocabulary.** One system, one method, one CVPR 2023 paper,
evaluated at four vocabulary sizes `[S25]` — per-instance top-1 accuracy for isolated recognition:

| Vocabulary  |     WLASL |     MSASL |
| :---------- | --------: | --------: |
| 100 signs   | **92.64** | **91.02** |
| 300 signs   |     86.98 |       --- |
| 1,000 signs |     75.64 |     73.80 |
| 2,000 signs | **61.26** |       --- |

> **Accuracy falls from 92.6% to 61.3% as the vocabulary grows from 100 to 2,000 signs.** The curve
> is monotonic and steep. Three consequences:
>
> 1. **Closing the vocabulary is where the field's accuracy lives**, not a schedule compromise.
>    Decision 4 now rests on a measurement.
> 2. **A demonstration vocabulary in the low hundreds is the honest target.** This project's
>    smaller model on its own recorded data will sit below 92.6%, and the deck must say so.
> 3. **Top-5 stays high while top-1 collapses** — 91.77% at WLASL-2000, and above 99% on `RSA`'s
>    226-class benchmark `[S26]`. The right sign is usually *in the candidate set*. This is the
>    evidence for the top-k lattice at stage ⑤ and the *"offer top-k"* repair at stage ⑨ of
>    [`ARC_S6.1`](#61-pipeline).




## 5.3. Recommended Approach
Invert the problem. Do not attempt open-domain translation. Build a **closed-vocabulary
recognition system with an agentic assembly layer**, and be explicit that the vocabulary is
closed.

```text
P1  segmentation   → geometry + hysteresis, no model
                     motion energy, hands-in-signing-space, pause detection
                     buffer-and-replay (APR_S5.3) so the run-up is never lost

P2  recognition    → a SMALL temporal classifier over the curated landmark features
                     closed vocabulary, per-class confidence, top-k output
                     the only trained component, and it is not an LLM

P3  assembly       → an agentic layer that turns a noisy, confidence-scored
                     hypothesis lattice into a sentence — and, crucially, decides
                     what to do when it cannot
```




## 5.4. Corrections to `SCR` → ISSUES
**"Training LLM (methodology)."** No LLM is trained. The only trained component is a small
sequence classifier over ~150-dimensional landmark vectors — hours on a laptop, not a cluster.
The LLM is used **at inference time via prompting and tool use** on Bedrock, exactly as taught in
`D1`/`D2`. Removing this from the plan removes the largest single cost and schedule risk in it.

**"AI memory loss (during training) or hallucination."** Two different things, one of which does
not apply:

- *Catastrophic forgetting* is a **training-time** phenomenon. Since no LLM is trained, it is out
  of scope.
- *Context rot* is the real runtime analogue, and `D3_p22` names it precisely: *"Everything the
  model can see shares one window. Well before the limit, accuracy and consistency degrade while
  cost and latency rise on every turn of the loop."*
- *Hallucination* is real, and for this product it is the **single most dangerous failure mode**,
  because a fluent LLM handed a low-confidence gloss sequence will produce a fluent, plausible,
  **wrong sentence** and attribute it to a deaf person. See
  [`RSK_S7.1`](RSK_risk_register.md#71-fabrication).




## 5.5. Positioning Against Existing Solutions
Required for [`JCR_S2.2`](JCR_judging_criteria.md#22-c2--original--innovative-idea-20) and for
`D3_p7`'s *"Look for what the existing tools still leave undone."*

1. **Google SignGemma** — announced at Google I/O, May 2025; an open model for translating sign
   language into spoken-language text, *"best at American Sign Language to English"* `[S16]`
   *What it does:* Strong ASL→English translation
   *What it leaves undone:* **ASL, not SgSL.** Model-only — no conversation flow, no
   bidirectionality, no handling of its own uncertainty. ⚠ Availability at time of writing is
   unconfirmed `[S16]`
2. **Live captioning (YouTube, Meet, Zoom)**
   *What it does:* Speech → text
   *What it leaves undone:* Handles the **hearing** side only. Does nothing for a signer
3. **Sign-language gloves and wearables**
   *What it does:* Hand tracking
   *What it leaves undone:* Require the deaf person to wear the device; miss non-manual grammar;
   produce one-way communication. Rejected by the deaf community and by researchers `[S4] [S17]`
4. **Human interpreters**
   *What it does:* Everything, correctly
   *What it leaves undone:* Scarce and must be booked. In Singapore, SADeaf lists **2 Deaf and more
   than 6 hearing staff interpreters**, supported by **55 community interpreters on an ad-hoc
   basis** `[S18]`

**The credible gap:** none of the above is a *Singapore-context, uncertainty-honest, turn-aware
conversational agent*. Specifically:

1. **SgSL, not ASL.** Singapore Sign Language is its own language — SADeaf describes it as a
   combination of Shanghainese Sign Language, ASL, Signing Exact English and locally developed
   signs `[S19]`. An ASL model is the wrong model here, and that is a defensible, verifiable
   differentiator.
2. **Honesty about uncertainty.** Every incumbent outputs a sentence. This system refuses to, and
   states why, when it is not confident.
3. **The conversation, not the clip.** Turn-taking, repair, and the hearing person's reply are
   part of the product, not out of scope.




## 5.6. The Four Routes from Skeleton to Text
Added 2026-09-04, from the six translation repositories. [`ARC_S5.3`](#53-recommended-approach)
names the recommendation; this section states the alternatives it was chosen over, and why, so the
choice is on the record rather than assumed. **Priority-ordered.**



### 5.6.1. R1 — Isolated classifier + agentic assembly *(recommended)*
Segment, classify each segment against a closed vocabulary, and hand a confidence-scored gloss
lattice to an LLM that assembles a sentence or refuses. This is
[`ARC_S5.3`](#53-recommended-approach), and it is what stages ④–⑦ of
[`ARC_S6.1`](#61-pipeline) already describe.

1. **Evidence** · At 100 signs, isolated recognition reaches **92.64%** top-1 and **96.90%** top-5
   `[S25]`; on a 226-class studio benchmark, skeleton-only reaches **96.11%** `[S26]`
2. **Cost** · One small temporal model, hours on a laptop. No LLM training
3. **Why it wins** · It is the only route where **the system can decline**. Every alternative below
   emits its best hypothesis by construction, which is disqualifying under
   [`CLD_S5.2`](../CLAUDE.md#52-honesty-about-the-product) and decision 8
4. **Its weakness** · It depends on segmentation, and segmentation is contested —
   [`ARC_S9.1`](#91-open-questions-for-the-team) question 5



### 5.6.2. R2 — Sliding-window classifier with a blank class
Do not segment at all. Slide a fixed window over the landmark stream, classify **every** window,
and recover the gloss sequence by beam search over the per-frame distribution, with a **blank**
class absorbing the gaps. This is `RSL`'s `Online` framework, EMNLP 2024 `[S25]`.

1. **Parameters, as published** · 16-frame window (~640 ms at 25 fps), **stride 1**, beam width 10
2. **Cost** · One forward pass **per frame**, affordable only because the classifier is small.
   Training additionally needs a dictionary of isolated clips, which `RSL` bootstraps by cutting
   continuous video with an already-trained model — a step this project cannot perform
3. **Why it is second, not first** · It removes the segmentation assumption that R1 depends on,
   which is a real advantage given
   [`ARC_S9.1`](#91-open-questions-for-the-team) question 5. But a per-frame argmax has no natural
   place to attach a refusal, and the beam search commits to a path
4. **Standing** · A **measurement**, not an argument. Both R1's segmenter and R2's window are
   cheap; build them behind one interface and compare — decision 20



### 5.6.3. R3 — Frame-sampled VLM, no training
Sample k keyframes from an utterance window, send them with a landmark summary to a multimodal
model, and ask for the sign. This is [`ARC_S7.4`](#74-p2--rationale-for-building-it-regardless)'s
P2, and it stays exactly where that section puts it: **a fallback and a measured baseline**, built
in an afternoon, not the primary route.

Its ceiling is set by what the literature reports for gloss-free translation —
[`ARC_S5.2`](#52-state-of-the-art) — and by the fact that Bedrock's Claude models accept images,
not video, so fast movement is sampled rather than seen.



### 5.6.4. R4 — Retrieval instead of classification
Embed the utterance window and retrieve the nearest entries from a vocabulary of embedded reference
clips, rather than classifying into a fixed softmax. `RSL`'s `CiCo` (CVPR 2023) formulates sign
understanding as retrieval and reports R@1 of 69.5 on Phoenix-2014T and 56.6 on How2Sign `[S25]`.

1. **Its one real advantage** · A retrieval system **cannot return a sign that is not in the
   index**. `RSS` relies on exactly this property in the reverse direction —
   [`ARC_S5.7`](#57-the-reverse-direction) — and it is the architectural form of the
   anti-fabrication invariant rather than a threshold on top of a model
2. **Its costs** · The published numbers are for *sentence* retrieval against a corpus, not sign
   recognition, so they do not transfer directly; and a new sign requires re-embedding, not
   retraining, which is an operational advantage but not an accuracy one
3. **Standing** · ⚠ **Not evaluated for this task by anything in `ref_repo/`.** Recorded as a
   research direction, not a plan — [`ARC_S9.1`](#91-open-questions-for-the-team) question 7



### 5.6.5. Routes explicitly rejected
1. **End-to-end video → text, trained here** · *Rejected:* Weeks of multi-GPU training —
   [`ARC_S7.1`](#71-comparison-table) P7
2. **Reproducing a published translation model** · *Rejected:* `RSL` is the only complete
   implementation available and it has **no licence file**, pins a 2021 CUDA toolchain, and needs
   eight GPUs — [`SLS_S2`](../doc/SLS_slrt_synthesis.md#2-why-it-cannot-be-used)
3. **Wait-k streaming translation** · *Rejected for the MVP:* `RSL`'s `Online/SLT` emits text after
   `wait_k: 2` glosses rather than at the utterance boundary `[S25]`. It multiplies model calls
   against the `D6` cap, and **partial output later revised is exactly the fluent-confident-wrong
   failure** decision 8 exists to prevent. It is the named roadmap answer to sub-utterance latency,
   and belongs on slide 9
4. **Any OpenPose, SLRT or SAM-SLR code** · *Rejected:* Licence — decisions 16, 21 and 22




## 5.7. The Reverse Direction
[`SCR`](scribbles.md) promises a conversation, which means the hearing person's reply must reach
the signer. Added 2026-09-04, because the pipeline in [`ARC_S6.1`](#61-pipeline) previously
described only one direction.

**This half is a dependency, not a build.** `RSS` — ZurichNLP's `spoken-to-signed-translation`, MIT,
`pip install`, CPU-only, published at AT4SSL 2023 and deployed behind `sign.mt` — implements it
`[S29]`:

```text
spoken text ──► ① GLOSSER ──► ② LEXICON LOOKUP ──► ③ POSE STITCH ──► skeleton
                LLM or            lexicon             trim, cap,
                lemmatiser        ↓ language backup   seam-match,
                                  ↓ fingerspelling    filter, hide
                                  ↓ unmatched         idle hands
```

Four properties make it the right choice over `RSL`'s `Spoken2Sign`, which shares the architecture
but requires SMPL-X, Blender, a GPU, and has no licence
([`SLS_S7`](../doc/SLS_slrt_synthesis.md#7-spoken2sign-and-why-rss-wins)):

1. **It cannot fabricate a sign.** Every output is a retrieved `.pose` clip or a spelled letter.
   There is no generative step. This is decision 8's invariant enforced by **architecture** rather
   than by threshold
2. **It records how every token was resolved.** A four-state ladder — `LEXICON`,
   `LANGUAGE_BACKUP`, `FINGERSPELLING_BACKUP`, `UNMATCHED` — with per-token provenance exposed via
   `--coverage-info` and `--coverage-stats` `[S29]`
3. **Fingerspelling is the default fallback**, not an error path
4. **It shares `RSP`'s `.pose` format** with the forward direction, so one representation serves
   both

> **Decision:** the reverse direction is `RSS`, with the project's own lexicon. Recorded as
> decision 18.

> **The coverage ladder should be adopted in the forward direction too.** It is a better-engineered
> form of decision 8 than this document currently describes. The forward analogue: every gloss
> reaching the assembler carries **how it was obtained** — *classifier, high confidence* /
> *top-k, signer-confirmed* / *fingerspelled* / *unresolved* — and the output shows it. That is a
> richer trace than one sentence-level confidence, it is the *"show the gloss trace"* requirement
> in [`ARC_S7.3`](#73-p1--the-recommendation-in-detail) item 8, and it makes **refusal precision
> measurable per token** rather than per utterance —
> [`ARC_S8.4`](#84-proposed-metric-set) metric 4. Recorded as decision 19.

> **Warning — one gap `RSS` does not close.** A lexicon is indexed by written word, and a written
> word may have two senses with two different signs. `RST` names this explicitly —
> `"spring" -> ["spring(water-spring)", "spring(metal-coil)"]` `[S30]`. `RSS` handles the *missing*
> word by fingerspelling it, but not the *ambiguous* one. **The project's answer is cheap and
> already in the architecture: the agent disambiguates**, because it holds the conversation
> context. Lexicon keys become `word + sense`, and the glosser is asked for the sense.

> **Warning — no Singapore Sign Language fingerspelling alphabet exists.** `RSS` ships alphabets
> for twenty sign languages; `sls` is not among them, and neither is any other Southeast Asian sign
> language `[S29]`. If SgSL is chosen, 26 handshapes must be recorded — which is the **cheapest
> data-collection task in the entire plan** and an achievable deliverable in its own right.

> **Note — output as a skeleton, not an avatar.** `RSS`'s video renderer is an optional extra
> requiring a pix2pix model. The project does not need it: `RSP`'s `PoseVisualizer` renders a pose
> skeleton, and **an avatar that looks almost-human is a worse product than a skeleton that
> obviously is not.** Recorded as decision 23.

---





# 6. THE RECOMMENDED ARCHITECTURE
## 6.1. Pipeline
```text
┌─ EDGE / LOCAL ──────────────────────────────────────────────────────────────┐
│                                                                             │
│  camera ──► bounded queue (drop-oldest, size 1)      [APR lesson L7]        │
│                │                                                            │
│                ▼                                                            │
│  ① SUBJECT TRACKER      largest/central person, hysteresis-held             │
│                │                                                            │
│                ▼                                                            │
│  ② LANDMARK EXTRACTOR   MediaPipe Holistic → 543 landmarks                  │
│                │        curated subset: hands 42 + handedness + upper pose  │
│                │        + brows + mouth                    [ARC_S3.2]       │
│                ▼                                                            │
│  ③ NORMALISER           body-relative signing space, + velocity/accel       │
│                │        confidence GATE — drop, never guess  [APR L2]       │
│                ▼                                                            │
│  ④ SEGMENTER            geometry + hysteresis + buffer-and-replay [APR L3/L4]│
│                │        emits: candidate sign windows, utterance boundaries │
│                ▼                                                            │
│  ⑤ CLASSIFIER           small temporal model, closed vocabulary             │
│                │        emits: top-k glosses with calibrated confidence     │
│                │                                                            │
│                ▼   compact JSON — NOT raw landmarks    [D2: payloads small] │
└────────────────┼────────────────────────────────────────────────────────────┘
                 │
┌─ AGENT (AWS Bedrock) ───────────────────────────────────────────────────────┐
│                                                                             │
│  LangGraph state machine, bounded loops, typed state       [D2, D3_p22]     │
│                                                                             │
│  ⑥ ASSEMBLER agent      hypothesis lattice → candidate sentence             │
│       tools: sgsl_lexicon_lookup() · conversation_memory() · context_hint() │
│                │                                                            │
│                ▼                                                            │
│  ⑦ CRITIC agent         reflection pattern (D3 case study 2)                │
│       "is this supported by the glosses, or was it invented?"                │
│       hard iteration cap held in state                     [D3_p22]         │
│                │                                                            │
│         ┌──────┴─────────────────────────────┐                              │
│         ▼                                    ▼                              │
│  ⑧ CONFIDENT                          ⑨ NOT CONFIDENT                       │
│     emit text + TTS                      DO NOT GUESS.                      │
│     show the gloss trace                 Plan a repair action:              │
│                                            · ask for a repeat               │
│                                            · request fingerspelling         │
│                                            · offer top-k for the signer     │
│                                              to pick                        │
│                                            · escalate to a human interpreter│
│                                                                             │
│  ⑩ ADAPTER              per-signer episodic memory: corrections, preferred  │
│                         variants, personal signs                            │
└─────────────────────────────────────────────────────────────────────────────┘

┌─ REVERSE DIRECTION — the hearing person's reply           [ARC_S5.7]        ┐
│                                                                             │
│  speech ──► ASR ──► ⑪ GLOSSER      the assembler agent, prompted            │
│                          │          with the closed vocabulary + word sense │
│                          ▼                                                  │
│                     ⑫ LEXICON LOOKUP        RSS coverage ladder:            │
│                          │                    lexicon → language backup     │
│                          │                    → fingerspelling → unmatched  │
│                          ▼                    per-token provenance recorded │
│                     ⑬ POSE STITCH           trim · cap · seam-match ·       │
│                          │                  filter (NOT the face) · hide    │
│                          ▼                  idle hands                      │
│                     ⑭ RENDER                pose skeleton, not an avatar    │
│                                                                             │
│  ⑪–⑭ are RSS + RSP, MIT, on CPU. Nothing here is trained.  [decision 18]    │
└─────────────────────────────────────────────────────────────────────────────┘
```

Stages ①–⑩ are the **sign → spoken** direction and are the project's own build. Stages ⑪–⑭ are the
**spoken → sign** direction and are a dependency — [`ARC_S5.7`](#57-the-reverse-direction). Both
share one landmark representation, `RSP`'s `.pose`, which is why the two halves compose rather than
merely coexist.




## 6.2. Where Agentic AI Earns Its Place
`D3_p10` sets the test: *"would this be possible without agentic AI?"* and asks for an explanation
of *"what a fixed workflow would miss."*

Stages ①–⑤ are **not agentic**, and the submission should say so. They are perception, and a fixed
pipeline performs them perfectly well.

The agency is at ⑥–⑩, and it is genuine:

1. **Plans** · *Where:* ⑨
   *What a fixed workflow would miss:* A fixed pipeline emits its best guess every time. This system
   decides *between* actions — ask again, request fingerspelling, offer choices, escalate — based on
   the shape of its own uncertainty
2. **Acts** · *Where:* ⑥, ⑨
   *What a fixed workflow would miss:* Calls tools: the SgSL lexicon, conversation memory, TTS,
   escalation. A classifier calls nothing
3. **Adapts** · *Where:* ⑩
   *What a fixed workflow would miss:* Learns this signer's corrections and personal variants across
   the conversation, and across sessions. The literature explicitly identifies the shift *"from
   signer-independent to signer-adaptive systems"* as a needed paradigm shift `[S11]`
4. **Reflects** · *Where:* ⑦
   *What a fixed workflow would miss:* A critic that can veto the assembler's sentence. This is
   `D3`'s own reflection pattern, from case study 2
5. **Keeps a human in the loop** · *Where:* ⑨
   *What a fixed workflow would miss:* Both physical-AI case studies in `D3` (slides 33, 34) make
   human confirmation a design constraint from day one. This design does the same, for the same
   reason

> **Note — agent class.** `D3_p17` is explicit that *"Perception belongs here [physical] when the
> reading feeds a decision that changes physical state. Analysing recorded media for a report sits
> with Extraction Agents on the digital side."* The perception stage here changes no physical
> state. **This is a digital-track project**, spanning `D3`'s **Extraction** (parse and transform),
> **Personalized** (adapt and learn) and **Embedded** (live where people work) classes. Stating
> this on the technical-architecture slide demonstrates that the taxonomy was read.




## 6.3. Design Rules Inherited from the Training Decks
Each of these is a direct application of taught material, which is worth making visible at code
level per [`JCR_S3.2`](JCR_judging_criteria.md#32-project-files).

1. **Heavy payloads live in graph State; prompts carry only metadata or references** · *Source:*
   `D2`
   *Application:* Landmark tensors and video frames **never** enter a prompt. The agent sees compact
   JSON: glosses, confidences, timestamps
2. **Bound every loop with a counter held in state** · *Source:* `D3_p22`
   *Application:* The assembler↔critic loop has a hard iteration cap that ignores the model's
   judgement
3. **Descriptions are the interface** · *Source:* `D3_p22`
   *Application:* `sgsl_lexicon_lookup`'s docstring is prompt text, and is written as such
4. **Keep payloads small** · *Source:* `D3_p22`
   *Application:* Tools return small typed results, not page dumps
5. **Short, single-purpose agents that do one job and exit** · *Source:* `D3_p22`
   *Application:* Assembler and critic are separate agents with separate prompts
6. **Typed state with reducers** · *Source:* `D3` stack slide
   *Application:* Pydantic / TypedDict schema for the graph state
7. **Read model IDs from a constant, never build them** · *Source:* `D3` stack slide
   *Application:* One `MODEL_ID` constant
8. **`allowed_tools` is an allow-list and a security boundary** · *Source:* `D3` stack slide
   *Application:* The agent cannot call anything not on the list




## 6.4. Latency Budget
Live captioning sets the user's expectation, and the standard is *sub-second, continuously
updating*. Target budget per utterance:

1. **①–③ landmark extraction**
   *Target:* ≤ 33 ms/frame
   *Notes:* MediaPipe on CPU comfortably reaches this; drop frames rather than fall behind
2. **④ segmentation commit**
   *Target:* 100–200 ms
   *Notes:* The hysteresis window. Costs latency, not data, because of buffer-and-replay
3. **⑤ classification**
   *Target:* ≤ 50 ms
   *Notes:* Small model, short window
4. **⑥–⑦ agent round trip**
   *Target:* 0.5–2 s
   *Notes:* The dominant term. Network + Bedrock. Only runs at utterance boundaries, not per frame
5. **Perceived**
   *Target:* **~1–2 s behind the signer**
   *Notes:* Comparable to live captioning; acceptable

> **Decision:** the agent is invoked **once per utterance**, never per frame. This is what keeps
> both latency and cost tractable — see [`ARC_S8`](#8-cost-model-against-the-aws-cap).




## 6.5. Perception Engineering Rules
Rules 1–12 added 2026-08-30 from the four tracking repositories; rules 13–18 added 2026-09-04 from
the translation repositories. Each is a concrete instruction for stages ①–⑤ that the earlier
drafting of this document did not know it needed. Sources:
[`MPS`](../doc/MPS_mediapipe_synthesis.md), [`DHS`](../doc/DHS_depthai_synthesis.md),
[`APS`](../doc/APS_apple_synthesis.md), [`SPS`](../doc/SPS_sign_pose_synthesis.md),
[`SSS`](../doc/SSS_spoken_to_signed_synthesis.md), [`STS`](../doc/STS_sign_translator_synthesis.md),
[`LTS`](../doc/LTS_signlang_literature_synthesis.md).

1.  **Use the Tasks API, never the legacy Solutions API** · *Stage:* ②
    *Rule:* Import from `mediapipe.tasks.python.vision`. `mp.solutions.hands` is excluded from the
    1.0-line wheel by `setup.py`, and almost every tutorial online uses it `[S21]`
2.  **Pin the MediaPipe version in `requirements.txt`** · *Stage:* ②
    *Rule:* An exact version, chosen against the live index and recorded with the date it was
    checked. The upstream repository has 5,617 commits and has already removed a public API
3.  **Run the landmarker in `VIDEO` or `LIVE_STREAM` mode** · *Stage:* ②
    *Rule:* `IMAGE` mode silently disables the tracking loop and runs the palm detector on every
    call. `LIVE_STREAM` additionally drops frames under load, which is
    [`APR`](../ref_repo/tracking/apple/APR_apple_report.md) lesson L7 implemented inside the library
4.  **Rate-limit the second-hand search** · *Stage:* ②
    *Rule:* With `num_hands = 2` and one hand visible, the palm detector runs on **every frame**.
    Port `RDH`'s tolerance counter — [`DHS_S3.1`](../doc/DHS_depthai_synthesis.md).
    Signers drop to one hand constantly, so this is the common case, not an edge case
5.  **Average handedness over a hand's tracked lifetime** · *Stage:* ③
    *Rule:* Per-frame handedness flips. Because dominant and non-dominant hands carry different
    grammatical roles ([`ARC_S3.2`](#32-the-landmark-budget)), a flip is a **grammatical** error.
    ~10 lines — [`DHS_S3.2`](../doc/DHS_depthai_synthesis.md#32-handedness-averaging)
6.  **Maintain hand identity across frames** · *Stage:* ③
    *Rule:* MediaPipe orders hands per frame and guarantees nothing between frames. Rule 5 depends
    on this, so the two are built together
7.  **Keep both hands and mark handedness uncertain** · *Stage:* ③
    *Rule:* When two hands classify with the same handedness, do **not** drop one, as `RDH` does. A
    two-handed sign seen with one hand is unrecognisable — a worse failure than a mislabel. Report
    the uncertainty, per decision 8
8.  **Never index a landmark result without checking for absence** · *Stage:* ②–③
    *Rule:* Empty result lists are the **normal** output when nothing clears the presence gate
9.  **Do not treat normalised `z` as depth** · *Stage:* ③
    *Rule:* It is scaled by 0.4 × the *crop* width and is a within-hand ordering only. It must not
    reach the classifier as though it were a distance
10. **Signing space is a gate, and hands at rest are not signing** · *Stage:* ④
    *Rule:* `RDH`'s `hands_up_only` is field evidence that a wrist-above-elbow test suppresses
    false positives cheaply. Generalise it to hands-in-signing-space
11. **Instrument perception from the first commit** · *Stage:* ①–⑤
    *Rule:* Count frames with no hand, frames on which detection ran, landmark inferences split by
    detection versus tracking, and failed inferences — the shape of `RDH`'s exit statistics. The
    detection-rate percentage is the one number that exposes rule 4's pathology. Feeds
    [`ARC_S8.4`](#84-proposed-metric-set)
12. **Nothing in `src/` imports from `ref_repo/`** · *Stage:* all
    *Rule:* The directory is git-ignored, so a judge cloning the submission would get an
    `ImportError`. Anything kept is re-implemented with attribution
13. **Never temporally smooth the face** · *Stage:* ③
    *Rule:* Landmark jitter invites a uniform smoothing filter. Applying one to the face
    **dampens mouthing and the fast brow movements** that carry lexical and syntactic content —
    the reason [`ARC_S3.2`](#32-the-landmark-budget) items 4 and 5 exist at all. `RSS` excludes the
    face block from its filter with exactly this stated reason `[S29]`. **Smooth the hands and
    body; leave the face alone.** Where the hands are filtered, `RSS` uses a zero-phase 4th-order
    Butterworth low-pass at **6 Hz** — ⚠ one system's parameter, not a measured property of sign
    language, but a usable default and a sanity check on velocity features
14. **Gate signing space by torso-normalised wrist height, with hysteresis** · *Stage:* ④
    *Rule:* Rule 10's wrist-above-elbow test is the crude form. `RSS` normalises wrist height by
    the signer's own **hip-to-shoulder distance** — 0 at the hip, 1 at the shoulder — with a
    threshold of **0.15**, a **0.2 s** minimum duration, and a **median** over the sequence for the
    torso length so one bad frame cannot move the threshold `[S29]`. It is scale-invariant, which
    the raw elbow test is not. About twenty lines, and it supersedes rule 10
15. **Substitute the body wrist when the hand wrist is absent** · *Stage:* ③
    *Rule:* MediaPipe Holistic emits each wrist twice. The hand wrist is the origin of the
    handshape descriptor, so when it collapses to zero confidence every hand landmark relative to
    it is silently wrong. `RSP`'s `correct_wrists()` is ten lines —
    [`ARC_S4.3`](#43-recommended-representation)
16. **Interpolate missing hand keypoints; do not pass zeros** · *Stage:* ③
    *Rule:* The literature reports **bilinear interpolation of undetected hand keypoints** and
    **palm-anchor normalisation** as the two preprocessing steps that took a pose-based model to
    the best reported WLASL-100 accuracy of its time `[S28]`. Both operate on MediaPipe output
    specifically. ⚠ Reported by a survey; the paper was not read
17. **Weight any pose-to-pose distance by the product of the two confidences** · *Stage:* ③–⑤
    *Rule:* Comparing two poses with missing keypoints — template matching, dynamic time warping
    against reference signs, nearest-neighbour — must not let undetected points, whose coordinates
    are arbitrary, decide the answer. Weight each keypoint by the **product** of its confidence in
    both frames and normalise by the summed weight `[S29]`. The evaluation literature reaches the
    same conclusion independently, in `nDTW-MJE` `[S28]`. Also **exclude the face** from any
    whole-body distance: it is most of the points and it barely moves
18. **Configure MediaPipe Tasks as `RST` does** · *Stage:* ②
    *Rule:* `mediapipe.tasks.vision.PoseLandmarker` and `HandLandmarker`, `RunningMode.VIDEO`,
    `.task` assets by path, `output_segmentation_masks=False`, both landmarkers created and closed
    in one `with` block `[S30]`. It is the only correct example in `ref_repo/`, it is Apache 2.0,
    and it may be adapted with attribution. ⚠ It defaults to `pose_landmarker_heavy.task` — measure
    `lite` and `full` before inheriting `heavy` — and it has **no** tolerance counter, so rule 4
    still applies on top of it

> **Warning — the y-flip.** MediaPipe's normalised origin is the **top-left**; Apple's Vision
> origin is the **bottom-left**. Copying `y = 1 - y` out of
> [`APR_S5.2`](../ref_repo/tracking/apple/APR_apple_report.md#52-coordinate-spaces--three-of-them) into a
> MediaPipe pipeline flips the image. Already standing policy in
> [`CLD_S5.4`](../CLAUDE.md#54-working-with-the-reference-repositories); repeated here because this
> section is where the code will be written from.

---





# 7. ALTERNATIVES, PRIORITY-ORDERED
Ordered by expected value for this hackathon: financial investment, hardware requirement,
schedule risk, and effect on the judging criteria.




## 7.1. Comparison Table
1. **P1 — Pose + small classifier + Bedrock agent** *(recommended)*
   *Hardware:* Any laptop with a webcam — **$0**
   *Money:* ~$1–3 of the $20 cap · *Training:* hours, on a laptop · *Schedule risk:* **low**
   *Effect on `JCR`:* C1 ✅ scalable · C4 ✅ runs anywhere
2. **P2 — Frame-sampled VLM, no training**
   *Hardware:* Any webcam — **$0**
   *Money:* Higher token cost; still within cap if utterance-triggered · *Training:* **none** ·
   *Schedule risk:* **very low**
   *Effect on `JCR`:* Excellent **fallback** and a free ablation baseline for C3
3. **P3 — Adapt an open sign model (e.g. SignGemma)**
   *Hardware:* GPU for fine-tuning — cloud hours or a gaming laptop
   *Money:* Moderate · *Training:* days · *Schedule risk:* **high** — ⚠ availability unconfirmed
   `[S16]`
   *Effect on `JCR`:* C2 ⚠ ties originality to a third-party model
4. **P4 — Depth camera / stereo / LiDAR**
   *Hardware:* RealSense ~US$150–400, or an iPhone Pro
   *Money:* High · *Training:* same as P1 · *Schedule risk:* medium — procurement inside 4 days
   *Effect on `JCR`:* C1 ❌ **breaks "scalable or easily adopted"**
5. **P5 — Smart glasses / AR headset**
   *Hardware:* US$300–3,500
   *Money:* Very high · *Training:* same as P1 · *Schedule risk:* high
   *Effect on `JCR`:* C1 ❌ same problem, worse
6. **P6 — Gloves / EMG wearables**
   *Hardware:* US$50–500
   *Money:* High · *Training:* new data collection · *Schedule risk:* high
   *Effect on `JCR`:* ❌ **Contradicts [`SCR`](scribbles.md)'s own premise and is rejected by the
   deaf community** `[S4] [S17]`
7. **P7 — End-to-end video→text trained from scratch**
   *Hardware:* Multi-GPU
   *Money:* Very high · *Training:* weeks · *Schedule risk:* **fatal**
   *Effect on `JCR`:* Not achievable in the window




## 7.2. The Four Reference Repositories Compared
[`ARC_S7.1`](#71-comparison-table) chooses the *approach*. This section chooses the **perception
library**, against the four repositories in `ref_repo/`. Added 2026-08-30; it did not exist when
the pipeline in [`ARC_S6.1`](#61-pipeline) was first drafted.



### 7.2.1. Summary table
| Repository      | Licence            | Runs on a laptop CPU | Language | Verdict           |
| :-------------- | :----------------- | :------------------- | :------- | :---------------- |
| `RMP` MediaPipe | Apache 2.0         | **Yes**, video rate  | Python   | **Build on this** |
| `RAP` HandPose  | Apple sample       | iOS device only      | Swift    | Architecture only |
| `RDH` DepthAI   | MIT                | Algorithms only      | Python   | Port the logic    |
| `ROP` OpenPose  | **Non-commercial** | ~0.1 FPS             | C++      | **Rejected**      |



### 7.2.2. The four, in one paragraph each
1. **`RMP` — Google MediaPipe** · *Verdict:* **The dependency**
   *Reason:* Apache 2.0, `pip install`, no GPU, 21 hand landmarks plus handedness at video rate on
   a CPU, and a `HolisticLandmarker` that additionally supplies pose-aligned hand world landmarks
   `[S21]`. Nothing else in `ref_repo/` satisfies the *"any device with a camera"* promise. The
   costs are real and are listed in [`MPS_S6`](../doc/MPS_mediapipe_synthesis.md): a moving API, a
   dropped legacy interface, a misnamed option and a detector pathology
2. **`RAP` — Apple `HandPose`** · *Verdict:* **Architecture, not code**
   *Reason:* iOS and Swift, so nothing ships. What transfers is the twelve lessons in
   [`APS_S5`](../doc/APS_apple_synthesis.md#5-the-twelve-lessons), above all buffer-and-replay
   segmentation (L4) and confidence-as-a-gate (L2). The segmenter at stage ④ is a port of
   [`APR_S5.3`](../ref_repo/tracking/apple/APR_apple_report.md)
3. **`RDH` — DepthAI hand tracker** · *Verdict:* **Port the tracking logic; reject the hardware**
   *Reason:* Requiring an OAK camera fails C1 exactly as any depth sensor does
   ([`ARC_S7.5`](#75-p4p5--depth-and-glasses-as-roadmap-items)). But it is the only place where
   MediaPipe's tracking state machine exists in readable Python, and it supplies four fixes
   MediaPipe does not: the detector tolerance counter, handedness averaging, duplicate-hand
   suppression and a hands-at-rest prior — [`ARC_S6.5`](#65-perception-engineering-rules)
4. **`ROP` — CMU OpenPose** · *Verdict:* **Rejected, on two independent grounds**
   *Reason:* Its licence is *"ACADEMIC OR NON-PROFIT ORGANIZATION NONCOMMERCIAL RESEARCH USE
   ONLY"*, and assigns ownership of derivatives to CMU `[S22]`; and its own documentation reports
   *"about 0.1 FPS (i.e., about 15 sec / frame)"* on CPU for the default body model, before hands
   are enabled `[S23]`. Either alone settles it. It remains the best **citation** available —
   TPAMI 2019 and CVPR 2017 — and the honest comparison
   [`JCR_S2.2`](JCR_judging_criteria.md#22-c2--original--innovative-idea-20) rewards



### 7.2.3. Consequences for the pipeline
1. **Stage ② is MediaPipe Tasks, pinned** — [`ARC_S6.5`](#65-perception-engineering-rules) rules 1
   and 2
2. **Stage ② gains a detector rate-limiter** — rule 4, ported from `RDH`
3. **Stage ③ gains handedness averaging and hand identity** — rules 5 and 6, ported from `RDH`
4. **Stage ③ loses part of the normaliser** — `HolisticLandmarker` already translates hand world
   landmarks into the pose frame ([`ARC_S4.3`](#43-recommended-representation))
5. **Stage ④ is unchanged** — still the Apple state machine, ported to Python
6. **No OpenPose code, model or derivative enters `src/`** — decision 16

> **Open question — Holistic Landmarker or Hand + Pose + Face separately?** `HolisticLandmarker`
> gives the body-relative frame for free and derives handedness from the pose skeleton, which is
> more reliable than classifying it from a hand crop. It is also hard-limited to **one person**
> `[S21]`, which collides with [`RSK_S5`](RSK_risk_register.md#5-multi-person-and-conversation) and
> with the two-way-conversation ambition. Running `HandLandmarker` and `PoseLandmarker` separately
> keeps multi-person open but means writing the normaliser and paying for two model loads. This is
> a measurement, not an argument: build both behind one interface and time them. Recorded as
> decision 14.

> **Placeholder — the measurement that settles decision 14.**
> **Missing:** frames per second and landmark quality for (a) `HolisticLandmarker` and (b)
> `HandLandmarker` + `PoseLandmarker`, on the demo laptop, with one and two hands in frame.
> **Update trigger:** the first working capture loop.
> **Owner:** team. Record in `EVL`.




## 7.3. P1 — The Recommendation in Detail
1. **Capture**
   *Choice:* Browser `getUserMedia` or OpenCV
   *Why:* Runs on any device with a camera, which is the [`SCR`](scribbles.md) promise and the C1
   scalability argument
2. **Landmarks**
   *Choice:* MediaPipe **Tasks API**, at a **pinned** version — `HolisticLandmarker` (543 points)
   or `HandLandmarker` + `PoseLandmarker`, per decision 14 · `[S9] [S21]`
   *Why:* Free, on-device, CPU real-time, Apache 2.0, cross-platform, actively maintained. Never
   the legacy `mp.solutions` API, which is excluded from the 1.0-line wheel —
   [`ARC_S6.5`](#65-perception-engineering-rules) rules 1–3
3. **Tracking state**
   *Choice:* Detector rate-limiter, handedness averaging, hand identity, duplicate suppression
   *Why:* MediaPipe supplies none of these and the application needs all four. Ported from `RDH` —
   [`ARC_S6.5`](#65-perception-engineering-rules) rules 4–7
4. **Features**
   *Choice:* Curated subset, body-normalised — [`ARC_S3.2`](#32-the-landmark-budget),
   [`ARC_S4.3`](#43-recommended-representation)
   *Why:* Small enough to train on a small dataset
5. **Segmentation**
   *Choice:* Geometry + hysteresis + buffer-and-replay
   *Why:* Ported from
   [`APR_S5.3`](../ref_repo/tracking/apple/APR_apple_report.md).
   No model, no training data, deterministic. Gated additionally by a hands-in-signing-space test —
   [`ARC_S6.5`](#65-perception-engineering-rules) rule 10
6. **Classifier**
   *Choice:* Small temporal model over the feature sequence, closed vocabulary
   *Why:* The only trained component. Hours on a laptop. ⚠ MediaPipe Model Maker ships a frozen
   `gesture_embedder` that may serve as a landmark feature stage; its input format is unverified —
   [`MPR_S7.4`](../ref_repo/tracking/google-mediapipe/MPR_mediapipe_report.md#74-model-maker)
7. **Agent**
   *Choice:* LangGraph on Bedrock, Claude Haiku 4.5
   *Why:* Exactly the stack `D1`/`D2`/`D3` teach and the judges expect
8. **Output**
   *Choice:* Text + TTS, **with the gloss trace visible**
   *Why:* The trace is what makes the system auditable rather than oracular

**Vocabulary scoping.** Pick one high-value scenario and close the vocabulary around it — a
clinic reception, a service counter, a campus help desk. This is `D3_p7`'s *"Cut one slice we can
finish and demonstrate"*, and it is how the submission reaches a **2** rather than a **1** on
[`JCR_S2.3`](JCR_judging_criteria.md#23-c3--effectiveness-of-the-solution-20).




## 7.4. P2 — Rationale for Building It Regardless
Even though P1 is the recommendation, **build P2 as well**, in an afternoon. Sample k keyframes
from an utterance window, send them plus a landmark summary to a multimodal model, and ask for
the sign.

It is worth the afternoon for three reasons:

1. It is a **live fallback** if the classifier is not ready on demo day.
2. It is a **measured baseline**. A stated comparison — the zero-training approach scored X, the
   trained pipeline scored Y — is precisely the evidence
   [`JCR_S5`](JCR_judging_criteria.md#5-evaluation-and-metrics) asks for, and almost no hackathon
   team produces it.
3. It costs almost nothing to keep.

> **Note:** Claude models on Bedrock accept **images**, not video (`D1` demonstrates this with a
> photo in `05_multimodal.py`). P2 is therefore necessarily frame-sampling, which is exactly why
> it will struggle with fast movement — a limitation worth measuring rather than asserting.




## 7.5. P4/P5 — Depth and Glasses as Roadmap Items
Depth genuinely helps with occlusion and with the depth-perception problem [`SCR`](scribbles.md)
lists. Apple's `VNDetectHumanBodyPose3DRequest` even states it *"uses depth information to improve
the accuracy"* where available `[S12]`.

But requiring a depth camera converts the product from *"any device with a camera"* to *"any
device with a depth camera"*. That directly attacks the **"scalable or easily adopted"** clause
that separates a 2 from a 1 on
[`JCR_S2.1`](JCR_judging_criteria.md#21-c1--benefits-delivered-by-the-solution-20), and it costs
money and procurement time the schedule does not allow.

**Correct treatment:** slide 9, *Roadmap & future potential*. State that the pipeline was designed
so that depth is an optional accuracy upgrade rather than a dependency. That is a strength, stated
as one.




## 7.6. P6 — Gloves Rejected on the Record
[`SCR`](scribbles.md) already rules out gloves, and the reasoning deserves to be on a slide,
because it converts a constraint into a design principle:

- Gloves *"misconstrue the nature of ASL […] by focusing on what the hands do"* and cannot see
  facial grammar `[S4]`.
- They are *"rooted in the preoccupations of the hearing world, not the needs of Deaf signers"*,
  and produce a **one-sided conversation** — the hearing person cannot reply through them `[S4]`.
- The peer-reviewed framing of the same question — *Do deaf communities actually want sign
  language gloves?* `[S17]` — and the machine-translation literature both conclude that
  *"the inclusion of deaf and hearing end users […] in use case identification, data collection
  and evaluation is of the utmost importance"* `[S5]`.

> **Decision:** state this explicitly in the submission, and act on it: at least one Deaf or
> hard-of-hearing person sees the prototype before submission. It answers
> [`JCR_S4.4`](JCR_judging_criteria.md#44-five-pressure-test-questions) question 3 (*"Would that
> person recognise themselves?"*), and it is the single cheapest way to avoid `D3_p7`'s
> **"Comfortable Guess"**
> failure.




## 7.7. The Six Translation Repositories Compared
[`ARC_S7.2`](#72-the-four-reference-repositories-compared) chose the **perception library**. This
section chooses what the **translation layer** is built on and what it is only cited for. Added
2026-09-04; it did not exist when [`ARC_S5.3`](#53-recommended-approach) was first drafted.



### 7.7.1. Summary table
| Repository             | Licence           | Ships? | Runs on a laptop CPU | Verdict           |
| :--------------------- | :---------------- | :----- | :------------------- | :---------------- |
| `RSP` `pose-format`    | MIT               | Yes    | **Yes**              | **Dependency**    |
| `RSS` spoken-to-signed | MIT               | Yes    | **Yes**              | **Dependency**    |
| `RST` `slt`            | Apache 2.0        | Yes    | Yes                  | Template only     |
| `RLT` SLP survey       | CC BY 4.0         | n/a    | n/a                  | **Evidence base** |
| `RSL` SLRT             | **None**          | **No** | No — 8 GPUs          | **Cite only**     |
| `RSA` SAM-SLR          | **Contradictory** | **No** | No — 4 GPUs          | **Cite only**     |



### 7.7.2. The six, in one paragraph each
1. **`RSP` — `pose-format`** · *Verdict:* **Dependency, base install only**
   *Reason:* MIT, three runtime dependencies, actively maintained, and it already implements the
   body-relative normalisation [`ARC_S4.3`](#43-recommended-representation) specifies, plus wrist
   correction, 3D hand canonicalisation, augmentation and frame dropout `[S27]`. Its `.pose` format
   is what lets the forward and reverse directions share one representation. ⚠ **Its own pose
   estimator is on the legacy `mp.solutions` API and pins `mediapipe<0.10.30`** — never install the
   `mediapipe` extra — [`SPS_S4`](../doc/SPS_sign_pose_synthesis.md#4-the-one-thing-not-to-take)
2. **`RSS` — spoken-to-signed** · *Verdict:* **Dependency — the whole reverse direction**
   *Reason:* MIT, five dependencies, CPU-only, published at AT4SSL 2023 and deployed behind
   `sign.mt`. It is [`ARC_S5.7`](#57-the-reverse-direction) in a package, and its coverage ladder is
   a better-engineered form of decision 8 `[S29]`. Its geometry — the torso-normalised signing gate,
   the hysteresis, the no-face-smoothing rule, the confidence-weighted distance — transfers to the
   **forward** direction as [`ARC_S6.5`](#65-perception-engineering-rules) rules 13, 14 and 17
3. **`RST` — `sign-language-translator`** · *Verdict:* **Template, not a dependency**
   *Reason:* Apache 2.0, and the **only** clone in `ref_repo/` that configures MediaPipe's Tasks API
   correctly — `PoseLandmarker` + `HandLandmarker` in `VIDEO` mode `[S30]`. That settles the
   mechanics of decision 14 option (b). Its data-collection protocol is a written answer to
   [`ARC_S9.1`](#91-open-questions-for-the-team) question 4. ⚠ **Its sign-to-text direction is not
   implemented** — one empty file — and it has no commit since 2024-09, so it is read and adapted,
   not depended on
4. **`RLT` — the SLP literature survey** · *Verdict:* **The evidence base**
   *Reason:* CC BY 4.0, 1,346 lines of survey, 4,892 lines of BibTeX and a 49-dataset registry. It
   supplies the field's task vocabulary, its methodology, and the two facts in
   [`ARC_S7.7.4`](#774-what-the-data-registry-settles). ⚠ **A survey, not a primary source** —
   everything from it is one step removed and must be marked so
5. **`RSL` — FangyunWei SLRT** · *Verdict:* **Cite only, on three independent grounds**
   *Reason:* Six peer-reviewed papers and the best numbers available
   ([`ARC_S5.2`](#52-state-of-the-art)) — and **no licence file**, so no permission to copy exists;
   `torch==1.9.0+cu102`; and eight-GPU training recipes `[S25]`. Its `Online` sliding window is
   route R2 in [`ARC_S5.6`](#56-the-four-routes-from-skeleton-to-text), re-implementable from the
   description
6. **`RSA` — SAM-SLR** · *Verdict:* **Cite only, treated as non-commercial**
   *Reason:* The CVPR 2021 challenge winner, and the source of the depth-camera ablation and the
   27-point budget `[S26]`. ⚠ Its licence is **self-contradictory** — CC0 in the root file,
   non-commercial in the README, CC BY-NC 4.0 over the directory that matters — and the conservative
   reading is the only defensible one



### 7.7.3. Consequences for the pipeline
1. **Stage ③ gains four operations from `RSP`** — normalisation, wrist correction, hand-rotation
   canonicalisation and augmentation — none of which the project now writes
2. **Stage ③ loses uniform smoothing** — rule 13. The face is never filtered
3. **Stage ④'s signing gate is replaced** — rule 14 supersedes rule 10 with a scale-invariant
   version
4. **Stage ④ gains a measured alternative** — R2's sliding window, decision 20
5. **Stage ⑤'s landmark budget shrinks** — from "hands + pose + curated face" to a **27–37 point**
   starting budget, [`ARC_S3.2`](#32-the-landmark-budget), decision 17
6. **Stages ⑥ and ⑨ gain per-token provenance** — the coverage ladder, decision 19
7. **Stages ⑪–⑭ exist at all** — the reverse direction is now specified,
   [`ARC_S5.7`](#57-the-reverse-direction), decision 18
8. **No SLRT or SAM-SLR code enters `src/`** — decisions 21 and 22, alongside decision 16 for
   OpenPose



### 7.7.4. What the data registry settles
`RLT`'s registry catalogues **49 datasets across 23 languages** `[S28]`. Two findings bear directly
on [`ARC_S9.1`](#91-open-questions-for-the-team).

> **There is no Singapore Sign Language dataset.** None of the 23 languages is Singaporean, and no
> Southeast Asian sign language appears. A full-text search of the clone for *Singapore*, *SgSL* and
> the IANA subtag `sls` returns one hit — a conference venue in the bibliography. `RSS`'s twenty
> fingerspelling alphabets confirm it independently `[S29]`.
>
> **This changes the shape of question 2.** The choice is not *"SgSL or ASL, both of which have
> data"*. It is: **ASL has 2,000-sign public corpora with 100+ signers; SgSL has nothing public at
> all.** A SgSL system means recording every sign it will ever recognise — entirely feasible at the
> vocabulary size [`ARC_S5.2`](#52-state-of-the-art) recommends, and **the strongest available
> differentiator, because the gap is real and verifiable.**

> **The field's benchmark data is predominantly non-commercial.** Most registry entries record
> `CC BY-NC*`, *"Research purpose on request"* or *"Authorized Academics"*. **RWTH-PHOENIX-Weather-2014T
> — the benchmark the entire translation literature reports on — is CC BY-NC-SA 3.0**, and How2Sign
> is CC BY-NC 4.0. Permissive terms are the exception `[S28]`.
>
> This is the same class of problem as the `ROP`, `RSL` and `RSA` licences, one layer down, and it
> makes recording the project's own vocabulary not merely pragmatic but **licence-clean**: data the
> team records, with documented consent, carries terms the team sets. ⚠ The registry's licence field
> is a community summary, not a licence text; verify before relying on any entry.

> **Note the signer counts.** Phoenix-2014T has **nine** signers; How2Sign has **eleven**. Every
> translation figure in [`ARC_S5.2`](#52-state-of-the-art) rests on nine people. Read with the
> signer-overlap warning in [`ARC_S8.4`](#84-proposed-metric-set) metric 10, generalisation to an
> unseen signer is the field's structural weak point — and this project, recording a handful of
> people, sits at the same weak point.

---





# 8. COST MODEL AGAINST THE AWS CAP
## 8.1. The Hard Constraint
`D6` is unambiguous: one lease per group; **at US$20 access to the AWS account is revoked; at
US$30 the account is terminated** to eliminate run-away costs. Additional leases past the first
*"would not be granted"* barring exceptions.

> **Warning:** this is not a soft budget. Exceeding it does not produce a bill — it produces a
> dead account, potentially on submission day.




## 8.2. Why P1 Fits Within the Cap
Per `D1`, the workshop default is
`global.anthropic.claude-haiku-4-5-20251001-v1:0` at **$1 in / $5 out per million tokens**, with
the note that *"output is five times input, on all of them"* and that *"an agent loop calls the
model five to fifteen times for one task, so multiply everything below."* Access is granted per
model **and per region** — the workshop region is `ap-southeast-1`.

> **Note:** Bedrock is partner-operated and priced separately from Anthropic's first-party API.
> The authoritative figures are on the AWS Bedrock pricing page; the `$1 / $5` above is what the
> hackathon's own deck states for the model it prescribes. Verify before quoting on a slide.

The architecture keeps the bill small for structural reasons, not by luck:

1. All perception runs **locally**
   Zero Bedrock tokens for the 30 fps path — by far the biggest saving
2. Agent invoked **per utterance**, not per frame
   Cuts calls by roughly three orders of magnitude
3. **Compact JSON payloads, never landmarks or frames**
   Small input token counts per call
4. **Hard iteration cap on assembler↔critic**
   Bounds worst-case spend per utterance
5. **Prompt caching on the stable system prompt**
   `D1` notes cache reads billed *"at up to 90% less"*, worth it above ~1k tokens
6. **Haiku 4.5 as default, escalate only if measurably wrong**
   `D1`'s own guidance




## 8.3. Cost Discipline as a Deliverable
`D1` and `D3_p32` both require token accounting. Log `usage.inputTokens` and
`usage.outputTokens` on every call from the first commit, and report **token cost per run** as one
of the metrics. That is metric 4 of `D3_p32` directly, it demonstrates the cost awareness `D1`
spends four slides on, and it protects the lease.




## 8.4. Proposed Metric Set
Mapping `D3_p32` and `D3_p35` onto this system:

1. **Answer fidelity**
   *Project version:* Sign-level accuracy and sentence-level correctness against a reviewed
   ground-truth set
   *Why it is honest:* The core quality number
2. **Task completion rate**
   *Project version:* Utterances resolved end-to-end **without a repair request**
   *Why it is honest:* Measures the whole pipeline, not one stage
3. **Intervention rate**
   *Project version:* How often the system asked for a repeat or escalated
   *Why it is honest:* `D3_p35` calls this *"the honest measure of autonomy"*
4. **Refusal precision**
   *Project version:* When it declined to answer, was it right to?
   *Why it is honest:* The metric almost nobody reports, and the one that matters most for an
   assistive tool
5. **Schema validation pass rate**
   *Project version:* Share of agent outputs parsing on the first attempt
   *Why it is honest:* `D3_p32` metric 1
6. **Loop discipline**
   *Project version:* Assembler↔critic iterations vs the cap
   *Why it is honest:* `D3_p32` metric 5
7. **Token cost per run**
   *Project version:* Summed per utterance
   *Why it is honest:* `D3_p32` metric 4
8. **Robustness**
   *Project version:* Re-test under changed lighting, distance, clothing, background, signer
   *Why it is honest:* `D3_p35` metric 5
9. **Perception health**
   *Project version:* Frames with no hand; frames on which the palm detector ran; landmark
   inferences split by detection versus tracking; failed inferences — the shape of `RDH`'s exit
   statistics, [`DHS_S3.5`](../doc/DHS_depthai_synthesis.md#35-counting-everything)
   *Why it is honest:* Detection rate is the one number that exposes the `num_hands = 2`
   pathology, and it is measured rather than assumed —
   [`ARC_S6.5`](#65-perception-engineering-rules) rule 11

10. **Signer generalisation**
    *Project version:* Accuracy on **held-out signers**, reported separately from accuracy on seen
    signers
    *Why it is honest:* The field reports that performance drops for signers not present in
    training, and that random splits with signer overlap inflate the number `[S28]`. **A random
    train/test split of self-recorded data measures signer-dependent recognition** and will make
    the demo worse than the slide. Split by signer, and say so
11. **Per-token coverage**
    *Project version:* The distribution of resolution states — *classifier, high confidence* /
    *top-k, signer-confirmed* / *fingerspelled* / *unresolved* — across an utterance
    *Why it is honest:* It turns metric 4 from a per-utterance judgement into a per-token count,
    and it is the same instrument in both directions —
    [`ARC_S5.7`](#57-the-reverse-direction), decision 19
12. **Metric hygiene**
    *Project version:* If BLEU is reported at all, computed with **SacreBLEU**, with the metric
    signature published, and compared against nothing computed by an unknown procedure
    *Why it is honest:* It is the field's own stated requirement `[S28]`, and comparing against a
    number produced elsewhere by a different tokenisation is the most common way sign-language
    results are overstated

> **Note:** *refusal precision* is the differentiator expressed as a number. Every competing
> system optimises "how often is it right". This one also reports "when it was unsure, how often
> was it right to be unsure" — because for this product a confident wrong sentence is worse than no
> sentence. See [`RSK_S7`](RSK_risk_register.md#7-agent-and-llm).

---





# 9. DECISIONS
Ratify or amend these, then [`PLN`](../ref_index.md#22-planned-documents) can be written against
them.

1.  Subject selection is a **tracking** problem. Build hysteresis-held largest-person tracking; do
    **not** build segmentation · *Status:* Agreed ✅
2.  Track hands + handedness + upper-body pose + a **curated face subset**. Reject the full
    468-point face mesh as model input · *Status:* Agreed ✅
3.  Representation is **body-normalised 2D + per-hand world landmarks**, not metric 3D · *Status:*
    Agreed 
4.  **Closed vocabulary**, scoped to one named scenario. State the scope openly · *Status:* Agreed ✅. The scenario will be a normal, informal conversation between two individuals (friends, strangers, ...).
5.  The only trained component is a **small temporal classifier**. **No LLM is trained** · *Status:*
    Proposed
6.  Segmentation is **geometry + hysteresis + buffer-and-replay**, ported from
    [`APR_S5.3`](../ref_repo/tracking/apple/APR_apple_report.md). No model · *Status:* Agreed
7.  The agent runs **once per utterance**, never per frame · *Status:* Agreed
8.  Below the confidence threshold the system **does not emit a sentence**. It plans a repair action
    · *Status:* Agreed
9.  Build P2 (frame-sampled VLM) as a fallback **and** as a measured baseline · *Status:* Agree
10. Depth hardware is a **roadmap item**, not an MVP dependency · *Status:* Agreed
11. **At least one Deaf or hard-of-hearing person reviews the prototype before submission** ·
    *Status:* Agreed ✅. To be carried out by my team.
12. **Log token usage from the first commit; report cost per run as a metric** · *Status:* Agreed.
13. **Perception is MediaPipe's Tasks API at a pinned version.** Never the legacy `mp.solutions`
    interface, which is excluded from the 1.0-line wheel `[S21]` · *Status:* Agreed.
14. **Landmark task chosen by measurement, not argument.** Build `HolisticLandmarker` and
    `HandLandmarker` + `PoseLandmarker` behind one interface, time both, and record the result —
    [`ARC_S7.2`](#72-the-four-reference-repositories-compared) · *Status:* Agreed.
15. **The four tracking fixes in [`ARC_S6.5`](#65-perception-engineering-rules) are in scope from
    the first commit**, not deferred: detector rate-limiting, handedness averaging, hand identity
    and duplicate suppression · *Status:* Agreed
16. **No OpenPose code, model or derivative enters `src/`.** Its licence is non-commercial and
    assigns derivatives to CMU `[S22]`. It is cited, not used · *Status:* Agreed.
17. **The landmark budget starts at ~27–37 points**, not the full curated set: `RSA`'s 7 body +
    10 per hand, plus a mouth subset. Widen only where a measurement earns it —
    [`ARC_S3.2`](#32-the-landmark-budget) · *Status:* Rejected. Proceed with the budget proposed in decision 2.
18. **The reverse direction is `RSS` (`spoken-to-signed`), with the project's own lexicon.** It is
    MIT, CPU-only and cannot fabricate a sign — [`ARC_S5.7`](#57-the-reverse-direction) ·
    *Status:* Agreed.
19. **Every gloss carries per-token provenance**, on `RSS`'s four-state coverage ladder, and the
    output displays it. Refusal precision is measured per token · *Status:* Agreed.
20. **The segmenter and the sliding window are built behind one interface and compared**, exactly
    as decision 14 treats the landmark task — [`ARC_S5.6`](#56-the-four-routes-from-skeleton-to-text)
    · *Status:* Agreed
21. **No SLRT code, model or derivative enters `src/`.** The repository carries **no licence
    file**, so no permission to copy exists `[S25]`. It is cited, not used · *Status:* Agreed.
22. **No SAM-SLR code, model or derivative enters `src/`.** Its licence is self-contradictory and
    is treated as non-commercial `[S26]`. It is cited, not used · *Status:* Agreed.
23. **The reverse direction outputs a pose skeleton, not a photorealistic avatar.** An avatar that
    looks almost-human is a worse product than a skeleton that obviously is not · *Status:* Agreed.
24. **Evaluation splits by signer, and reports held-out-signer accuracy separately** —
    [`ARC_S8.4`](#84-proposed-metric-set) metric 10 · *Status:* Agreed.




## 9.1. Open Questions for the Team
> **Placeholder — four unresolved decisions.**
> **Missing:** answers to the four questions below. Until they are answered, the decisions in
> [`ARC_S9`](#9-decisions) stay **Proposed** and `PLN` cannot be written.
> **Update trigger:** a team decision on each question; record it in
> [`ARC_S11`](#11-change-log) and flip the affected decision rows to **Ratified**.
> **Owner:** team.

1. **Which scenario, and therefore which vocabulary?** The single highest-leverage unresolved
   decision. It determines the dataset, the demonstration, and the C3 score.
2. **SgSL or ASL?** SgSL is the stronger differentiator and the honest choice for a Singapore
   hackathon, but ASL has far more public training data. A defensible middle path: build for SgSL,
   and demonstrate on whichever vocabulary can actually be collected, stated plainly.
3. **Who is the named person?**
   [`JCR_S4.4`](JCR_judging_criteria.md#44-five-pressure-test-questions) question 1 is
   unanswered and blocks the problem statement.
4. **Data.** Record a bespoke vocabulary, use a public dataset, or both? This determines the
   week. ⚠ Two facts now constrain the answer: **there is no public SgSL data at all**, and the
   public corpora the literature uses are predominantly non-commercially licensed —
   [`ARC_S7.7.4`](#774-what-the-data-registry-settles).
5. **Is geometric segmentation sound?** ⚠ A 2024 study of the Swedish Sign Language corpus reports
   *"no clear correspondence between utterance boundaries and articulatory features of the hands
   and head extracted with MediaPipe"*, and that three human definitions of an utterance boundary
   disagree with each other `[S28]`. That is evidence **against**
   [`ARC_S5.3`](#53-recommended-approach)'s stage ④ as currently designed. It is read from a survey
   summary, covers one corpus and one sign language, and concerns *utterance* boundaries rather
   than the *sign* boundaries a closed-vocabulary classifier needs — so it does not straightforwardly
   transfer. **What follows is not that the design is wrong, but that its assumption is contested
   and must be measured**, which is what decision 20 exists to do.
6. **Should the segmenter use a detection model instead of geometry?** Real-time sign language
   detection on **the per-joint optical-flow norm plus a shallow contextualised model** is published
   and cheap, and its inputs are already computed for the velocity features `[S28]`. It is the
   named upgrade path from rule 14's geometric gate, and the thing `RSS`'s own source comment wishes
   it had.
7. **Is retrieval worth evaluating against classification?** Route R4 in
   [`ARC_S5.6`](#56-the-four-routes-from-skeleton-to-text) cannot return a sign outside its index,
   which is the anti-fabrication invariant as architecture rather than as threshold. ⚠ Nothing in
   `ref_repo/` evaluates it for this task.

---





# 10. SOURCES
1.  **`[S1]`**
    *Source:* Apple Developer Documentation, `maximumHandCount` —
    https://developer.apple.com/documentation/vision/vndetecthumanhandposerequest/maximumhandcount
    *Reliability:* Official
2.  **`[S2]`**
    *Source:* Google AI Edge, *Hand landmarks detection guide* —
    https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker
    *Reliability:* Official
3.  **`[S3]`**
    *Source:* Apple Developer Documentation, `VNGeneratePersonInstanceMaskRequest` —
    https://developer.apple.com/documentation/vision/vngeneratepersoninstancemaskrequest
    *Reliability:* Official
4.  **`[S4]`**
    *Source:* M. Erard, *Why Sign-Language Gloves Don't Help Deaf People* (The Atlantic, 2017), as
    summarised across secondary reproductions —
    https://allthingslinguistic.com/post/167390176466/why-sign-language-gloves-dont-help-deaf-people
    *Reliability:* ⚠ Reputable original; reproductions were read, not the original
5.  **`[S5]`**
    *Source:* M. De Coster, D. Shterionov, M. Van Herreweghe, J. Dambre, *Machine Translation from
    Signed to Spoken Languages: State of the Art and Challenges*, Universal Access in the
    Information Society (2023) — https://arxiv.org/abs/2202.03086
    *Reliability:* Peer-reviewed
6.  **`[S6]`**
    *Source:* *The Importance of Facial Features in Vision-based Sign Language Recognition: Eyes,
    Mouth or Full Face?* — https://arxiv.org/html/2507.20884v1
    *Reliability:* ⚠ Preprint
7.  **`[S7]`**
    *Source:* *Emotion Recognition in Sign Language Conversation* — https://arxiv.org/pdf/2605.23328
    *Reliability:* ⚠ Preprint
8.  **`[S8]`**
    *Source:* Apple Developer Documentation, `VNHumanHandPoseObservation.chirality` —
    https://developer.apple.com/documentation/vision/vnhumanhandposeobservation/chirality
    *Reliability:* Official
9.  **`[S9]`**
    *Source:* Google AI Edge, *Holistic landmarks detection task guide* —
    https://ai.google.dev/edge/mediapipe/solutions/vision/holistic_landmarker
    *Reliability:* Official
10. **`[S10]`**
    *Source:* *SignIT: A Comprehensive Dataset and Multimodal Analysis for Italian Sign Language
    Recognition* — https://arxiv.org/html/2512.14489
    *Reliability:* ⚠ Preprint; the accuracy table is a survey of others' results
11. **`[S11]`**
    *Source:* N. Alishzade, G. Abdullayeva, *Sign Language Recognition and Translation for
    Low-Resource Languages: Challenges and Pathways Forward* (2026) —
    https://arxiv.org/abs/2605.12096
    *Reliability:* ⚠ Preprint
12. **`[S12]`**
    *Source:* Apple Developer Documentation, `VNDetectHumanBodyPose3DRequest` —
    https://developer.apple.com/documentation/vision/vndetecthumanbodypose3drequest
    *Reliability:* Official
13. **`[S13]`**
    *Source:* *SignMouth: Leveraging Mouthing Cues for Sign Language Translation* —
    https://arxiv.org/html/2509.10266
    *Reliability:* ⚠ Preprint; figure taken from a search summary, **open the paper before quoting**
14. **`[S14]`**
    *Source:* How2Sign / YouTube-ASL two-stage training comparison, reported across recent SLT
    preprints
    *Reliability:* ⚠ Preprint, second-hand. **Verify before quoting**
15. **`[S15]`**
    *Source:* O. Mercanoglu Sincan, J. H. Low, S. Asasi, R. Bowden, *Gloss-Free Sign Language
    Translation: An Unbiased Evaluation of Progress in the Field* (Feb 2026) —
    https://arxiv.org/abs/2603.13240
    *Reliability:* ⚠ Preprint, but from an established group
16. **`[S16]`**
    *Source:* Google, *Building with AI: highlights for developers at Google I/O* (May 2025) —
    https://blog.google/technology/developers/google-ai-developer-updates-io-2025/ ; SignGemma
    described as coming to the Gemma family, best at ASL→English. ⚠ Current availability unconfirmed
    *Reliability:* Official announcement; status unverified
17. **`[S17]`**
    *Source:* *Do deaf communities actually want sign language gloves?*, Nature Electronics (2020) —
    https://www.nature.com/articles/s41928-020-0451-7
    *Reliability:* Peer-reviewed
18. **`[S18]`**
    *Source:* SADeaf, *Sign Language Interpreters* —
    https://sadeaf.org.sg/faqconc_cat/sl_interpreter/
    *Reliability:* Official (national association)
19. **`[S19]`**
    *Source:* SADeaf, *Singapore Sign Language (SgSL)* — https://sadeaf.org.sg/faqconc_cat/sgsl/
    *Reliability:* Official (national association)
20. **`[S20]`**
    *Source:* `doc/[D1]`, `[D2]`, `[D3]`, `[D6]` — hackathon training decks
    *Reliability:* Official (organiser)
21. **`[S21]`**
    *Source:* [`MPR`](../ref_repo/tracking/google-mediapipe/MPR_mediapipe_report.md), reporting
    `ref_repo/tracking/google-mediapipe/mediapipe/` at `251c0cb96` — the Hand Landmarker Python API and
    options, the `setup.py` packaging rule, the presence gate, the `min_tracking_confidence`
    wiring, the `num_hands` tracking gate, and the `HolisticLandmarker` output contract
    *Reliability:* Primary — read directly from the source, with `file:line` citations in `MPR`
22. **`[S22]`**
    *Source:* [`OPR_S2.2`](../ref_repo/tracking/openpose/OPR_openpose_report.md#22-licence), quoting
    `ref_repo/tracking/openpose/openpose/LICENSE`
    *Reliability:* Primary. ⚠ Read as an engineer, not a lawyer; a commercial path requires
    qualified review
23. **`[S23]`**
    *Source:* [`OPR_S6`](../ref_repo/tracking/openpose/OPR_openpose_report.md#6-performance), quoting
    `ref_repo/tracking/openpose/openpose/doc/06_maximizing_openpose_speed.md`
    *Reliability:* Official but self-reported by the project; not independently reproduced here
24. **`[S24]`**
    *Source:* [`DHR`](../ref_repo/tracking/depthai-hand-tracker/DHR_depthai_report.md), reporting
    `ref_repo/tracking/depthai-hand-tracker/depthai_hand_tracker/` at `9773123` — the single-hand tolerance
    counter, handedness averaging, duplicate-hand suppression and the hands-up-only prior
    *Reliability:* Primary for the code; ⚠ the frame-rate observations in that repository's README
    are one practitioner's, not a benchmark
25. **`[S25]`**
    *Source:* [`SLR`](../ref_repo/translation/slrt/SLR_slrt_report.md), reporting
    `ref_repo/translation/slrt/SLRT/` at `38a4f7b` — the TwoStream-SLT and Twostream-SLR results
    tables, the NLA-SLR vocabulary-size table, the 63/79-keypoint budget, the `Online` sliding-window
    parameters, the `wait_k: 2` setting, the CiCo retrieval figures, and the absence of a licence
    file
    *Reliability:* Primary for the code and configurations, read with `file:line` citations in
    `SLR`. The performance figures are **self-reported by the authors** in the repository's own
    documentation, corresponding to peer-reviewed NeurIPS 2022, CVPR 2022/2023, ICCV 2023, ECCV 2024
    and EMNLP 2024 papers that were **not read in full**; none was independently reproduced here
26. **`[S26]`**
    *Source:* [`SAR`](../ref_repo/translation/sam-slr/SAR_sam_slr_report.md), reporting
    `ref_repo/translation/sam-slr/CVPR21Chal-SLR/` at `de6c53a` — the AUTSL validation and test
    tables, the WLASL-2000 modality table, the 27-keypoint selection, the ensemble weights, and the
    licence contradiction
    *Reliability:* Primary for the code and the licence files. ⚠ The performance figures were
    **transcribed by eye from images** in `img/`, which are the CVPR 2021 Workshop paper's own
    tables; the paper was not read in full and nothing was reproduced
27. **`[S27]`**
    *Source:* [`SPR`](../ref_repo/translation/sign-pose/SPR_sign_pose_report.md), reporting
    `ref_repo/translation/sign-pose/pose/` at `7a36fcf` (`v0.14.1`) — `Pose.normalize()`,
    `pose_normalization_info()`, `correct_wrists()`, `normalize_hands_3d()`, `reduce_holistic()`,
    `augment2d()`, the frame-dropout family, and the `mediapipe<0.10.30` pin
    *Reliability:* Primary — read from the clone with `file:line` citations in `SPR`
28. **`[S28]`**
    *Source:* [`LTR`](../ref_repo/translation/signlang-literature/LTR_signlang_literature_report.md),
    reporting `ref_repo/translation/signlang-literature/sign-language-processing.github.io/` at
    `af5fb4a` — the 49-dataset registry and its licence and signer fields, the signer-overlap
    finding, the Börstell 2024 segmentation result, the pose-based detection method, the
    MediaPipe-preprocessing and noisy-gloss results, the SacreBLEU guidance and the metric survey
    *Reliability:* ⚠ **Secondary.** A maintained community survey (CC BY 4.0) characterising papers
    that were **not read** for this review, plus a registry whose licence fields are a community
    summary rather than the datasets' own terms. Verify against the underlying paper or licence
    before any of these appears on a slide as a number
29. **`[S29]`**
    *Source:* [`SSR`](../ref_repo/translation/spoken-to-signed/SSR_spoken_to_signed_report.md),
    reporting `ref_repo/translation/spoken-to-signed/spoken-to-signed-translation/` at `259aacd` —
    the three-stage pipeline, the `CoverageType` ladder and coverage flags, the signing-boundary
    and lowered-hand tests, `_drop_short_spans`, the Butterworth filter and face exclusion, the
    confidence-weighted seam distance, the citation-form duration comment, and the fingerspelling
    lexicon inventory
    *Reliability:* Primary — read from the clone with `file:line` citations in `SSR`. ⚠ The
    "12–15×" citation-form figure is an **uncited source comment**, not a measurement; the AT4SSL
    2023 paper and the cited *Sign Stitching* (BMVC 2024) were not read
30. **`[S30]`**
    *Source:* [`STR`](../ref_repo/translation/sign-translator/STR_sign_translator_report.md),
    reporting `ref_repo/translation/sign-translator/sign-language-translator/` at `cca5f3a` — the
    MediaPipe Tasks configuration, the word-sense example, the data-collection protocol, and the
    empty `sign_to_text` package
    *Reliability:* Primary — read from the clone. ⚠ This repository carries **no publication and
    reports no evaluation**; its claims are unrefereed

---





# 11. CHANGE LOG
1. **2026-08-28** · *Author:* Claude (Opus 5)
   *Change:* Created. Confirmed/challenged all four MVP steps against published sources; rejected
   the "train an LLM" premise; specified the recommended pipeline; ranked seven alternatives;
   modelled cost against the `D6` cap; proposed twelve decisions and four open questions.
2. **2026-08-28** · *Author:* Claude (Opus 5)
   *Change:* Reformatted to the revised conventions in
   [`RIX_S4`](../ref_index.md#4-markdown-formatting-rules): bold title, collapsible `# METADATA`,
   `#`-level numbered sections, HTML anchors removed, padded tables, third-person voice,
   placeholders for unfinished content.
3. **2026-08-28** · *Author:* Claude (Opus 5)
   *Change:* Applied the revised [`RIX_S4.4`](../ref_index.md#44-vertical-spacing) heading spacing
   and the [`RIX_S4.5`](../ref_index.md#45-tables-and-numbered-lists) table-versus-numbered-list
   rule: tables whose rows exceeded 100 characters became numbered lists.
4. **2026-08-30** · *Author:* Claude (Opus 5)
   *Change:* Revised against the four reference-repository reports. Added
   [`ARC_S7.2`](#72-the-four-reference-repositories-compared), which compares `RMP`, `RAP`, `RDH`
   and `ROP` and names MediaPipe's Tasks API as the perception layer; renumbered the alternatives
   that follow. Added [`ARC_S6.5`](#65-perception-engineering-rules), twelve concrete perception
   rules. Reduced the scope of [`ARC_S4.3`](#43-recommended-representation): `HolisticLandmarker`
   already emits pose-aligned hand world landmarks, so only scale normalisation and the derived
   features remain. Added metric 9, *perception health*, to
   [`ARC_S8.4`](#84-proposed-metric-set). Added decisions 13–16 (pin the Tasks API; choose the
   landmark task by measurement; the four tracking fixes are in scope; no OpenPose code in
   `src/`), and sources `[S21]`–`[S24]`. Repointed every `APL` reference to
   [`APR`](../ref_repo/tracking/apple/APR_apple_report.md) after that document moved and was recoded.
5. **2026-09-04** · *Author:* Claude (Opus 5)
   *Change:* Revised against the six translation-repository reports. Added
   [`ARC_S5.6`](#56-the-four-routes-from-skeleton-to-text), ranking the four routes from skeleton to
   text and recording what was rejected; and [`ARC_S5.7`](#57-the-reverse-direction), which
   specifies the spoken → sign half as a dependency on `RSS` rather than a build. Added
   [`ARC_S7.7`](#77-the-six-translation-repositories-compared), comparing `RSL`, `RSA`, `RSP`,
   `RSS`, `RLT` and `RST` and naming `RSP` and `RSS` as dependencies and `RSL`/`RSA` as cite-only on
   licence grounds. Extended the pipeline in [`ARC_S6.1`](#61-pipeline) with stages ⑪–⑭.
   **Strengthened the evidence base:** replaced the preprint pose-versus-RGB table in
   [`ARC_S4.1`](#41-verdict-right-instinct-over-specified) with `RSA`'s controlled ablation, which
   prices a depth camera at **0.99 points**; added the gloss-supervised ceiling (**28.95 BLEU-4**,
   with its three conditions) and the vocabulary-size curve (**92.6% → 61.3%**) to
   [`ARC_S5.2`](#52-state-of-the-art); and narrowed the landmark budget in
   [`ARC_S3.2`](#32-the-landmark-budget) to **27–37 points** on two published budgets. Recorded
   that `Pose.normalize()` already implements
   [`ARC_S4.3`](#43-recommended-representation) step 2. Added perception rules 13–18, metrics 10–12,
   decisions 17–24, open questions 5–7, and sources `[S25]`–`[S30]`.
   **Recorded evidence against this document's own design:** a 2024 study reporting no clear
   correspondence between utterance boundaries and MediaPipe articulatory features —
   [`ARC_S9.1`](#91-open-questions-for-the-team) question 5.
