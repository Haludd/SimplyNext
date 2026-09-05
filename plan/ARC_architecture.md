**ARCHITECTURE — CONFIRMATION, SOURCES AND ALTERNATIVES**





# METADATA
<details>
<summary>Document code, status, review date, and usage instructions.</summary>

| Field                      | Value                            |
| :------------------------- | :------------------------------- |
| **Code**                   | `ARC`                            |
| **Status**                 | Live                             |
| **Last reviewed**          | 2026-08-30                       |
| **Source of truth for**    | Technical direction              |
| **Parent**                 | [`SCR`](scribbles.md)            |
| **Scored against**         | [`JCR`](JCR_judging_criteria.md) |
| **Problems catalogued in** | [`RSK`](RSK_risk_register.md)    |
| **Evidence base**          | `APS` · `MPS` · `DHS` · `OPS`    |

**For the team.** This document tests the MVP in [`SCR`](scribbles.md) step by step against
published evidence, states the architecture to build, and ranks the alternatives by cost, hardware
and risk. [`ARC_S7.2`](#72-the-four-reference-repositories-compared) compares the four reference
repositories head-to-head and names the one the perception layer is built on; its evidence base is
the four repository syntheses [`APS`](../doc/APS_apple_synthesis.md),
[`MPS`](../doc/MPS_mediapipe_synthesis.md), [`DHS`](../doc/DHS_depthai_synthesis.md) and
[`OPS`](../doc/OPS_openpose_synthesis.md). The sixteen decisions in [`ARC_S9`](#9-decisions) are
**Proposed** and await team sign-off; the master plan `PLN` is blocked on them.

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
   [`APR_S6.4`](../ref_repo/apple/APR_apple_report.md)) so the subject does not flip between
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
[`APR_S6.6`](../ref_repo/apple/APR_apple_report.md): convert once, at the boundary, and let every
downstream module see only signing-space coordinates.

> **Note — step 2 is partly already built.** The reading of the MediaPipe source recorded in
> [`MPR_S7.1`](../ref_repo/google-mediapipe/MPR_mediapipe_report.md#71-holistic-landmarker) shows
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
```




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
Added 2026-08-30, from the reading of the four reference repositories. Each rule below is a
concrete instruction for stages ①–⑤ that the earlier drafting of this document did not know it
needed. Sources: [`MPS`](../doc/MPS_mediapipe_synthesis.md),
[`DHS`](../doc/DHS_depthai_synthesis.md), [`APS`](../doc/APS_apple_synthesis.md).

1.  **Use the Tasks API, never the legacy Solutions API** · *Stage:* ②
    *Rule:* Import from `mediapipe.tasks.python.vision`. `mp.solutions.hands` is excluded from the
    1.0-line wheel by `setup.py`, and almost every tutorial online uses it `[S21]`
2.  **Pin the MediaPipe version in `requirements.txt`** · *Stage:* ②
    *Rule:* An exact version, chosen against the live index and recorded with the date it was
    checked. The upstream repository has 5,617 commits and has already removed a public API
3.  **Run the landmarker in `VIDEO` or `LIVE_STREAM` mode** · *Stage:* ②
    *Rule:* `IMAGE` mode silently disables the tracking loop and runs the palm detector on every
    call. `LIVE_STREAM` additionally drops frames under load, which is
    [`APR`](../ref_repo/apple/APR_apple_report.md) lesson L7 implemented inside the library
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

> **Warning — the y-flip.** MediaPipe's normalised origin is the **top-left**; Apple's Vision
> origin is the **bottom-left**. Copying `y = 1 - y` out of
> [`APR_S5.2`](../ref_repo/apple/APR_apple_report.md#52-coordinate-spaces--three-of-them) into a
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
   [`APR_S5.3`](../ref_repo/apple/APR_apple_report.md)
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
   [`APR_S5.3`](../ref_repo/apple/APR_apple_report.md).
   No model, no training data, deterministic. Gated additionally by a hands-in-signing-space test —
   [`ARC_S6.5`](#65-perception-engineering-rules) rule 10
6. **Classifier**
   *Choice:* Small temporal model over the feature sequence, closed vocabulary
   *Why:* The only trained component. Hours on a laptop. ⚠ MediaPipe Model Maker ships a frozen
   `gesture_embedder` that may serve as a landmark feature stage; its input format is unverified —
   [`MPR_S7.4`](../ref_repo/google-mediapipe/MPR_mediapipe_report.md#74-model-maker)
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

> **Note:** *refusal precision* is the differentiator expressed as a number. Every competing
> system optimises "how often is it right". This one also reports "when it was unsure, how often
> was it right to be unsure" — because for this product a confident wrong sentence is worse than no
> sentence. See [`RSK_S7`](RSK_risk_register.md#7-agent-and-llm).

---





# 9. DECISIONS
Ratify or amend these, then [`PLN`](../ref_index.md#22-planned-documents) can be written against
them.

1.  Subject selection is a **tracking** problem. Build hysteresis-held largest-person tracking; do
    **not** build segmentation · *Status:* Proposed
2.  Track hands + handedness + upper-body pose + a **curated face subset**. Reject the full
    468-point face mesh as model input · *Status:* Proposed
3.  Representation is **body-normalised 2D + per-hand world landmarks**, not metric 3D · *Status:*
    Proposed
4.  **Closed vocabulary**, scoped to one named scenario. State the scope openly · *Status:* Proposed
5.  The only trained component is a **small temporal classifier**. **No LLM is trained** · *Status:*
    Proposed
6.  Segmentation is **geometry + hysteresis + buffer-and-replay**, ported from
    [`APR_S5.3`](../ref_repo/apple/APR_apple_report.md). No model · *Status:* Proposed
7.  The agent runs **once per utterance**, never per frame · *Status:* Proposed
8.  Below the confidence threshold the system **does not emit a sentence**. It plans a repair action
    · *Status:* Proposed
9.  Build P2 (frame-sampled VLM) as a fallback **and** as a measured baseline · *Status:* Proposed
10. Depth hardware is a **roadmap item**, not an MVP dependency · *Status:* Proposed
11. **At least one Deaf or hard-of-hearing person reviews the prototype before submission** ·
    *Status:* Proposed
12. **Log token usage from the first commit; report cost per run as a metric** · *Status:* Proposed
13. **Perception is MediaPipe's Tasks API at a pinned version.** Never the legacy `mp.solutions`
    interface, which is excluded from the 1.0-line wheel `[S21]` · *Status:* Proposed
14. **Landmark task chosen by measurement, not argument.** Build `HolisticLandmarker` and
    `HandLandmarker` + `PoseLandmarker` behind one interface, time both, and record the result —
    [`ARC_S7.2`](#72-the-four-reference-repositories-compared) · *Status:* Proposed
15. **The four tracking fixes in [`ARC_S6.5`](#65-perception-engineering-rules) are in scope from
    the first commit**, not deferred: detector rate-limiting, handedness averaging, hand identity
    and duplicate suppression · *Status:* Proposed
16. **No OpenPose code, model or derivative enters `src/`.** Its licence is non-commercial and
    assigns derivatives to CMU `[S22]`. It is cited, not used · *Status:* Proposed




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
   week.

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
    *Source:* [`MPR`](../ref_repo/google-mediapipe/MPR_mediapipe_report.md), reporting
    `ref_repo/google-mediapipe/mediapipe/` at `251c0cb96` — the Hand Landmarker Python API and
    options, the `setup.py` packaging rule, the presence gate, the `min_tracking_confidence`
    wiring, the `num_hands` tracking gate, and the `HolisticLandmarker` output contract
    *Reliability:* Primary — read directly from the source, with `file:line` citations in `MPR`
22. **`[S22]`**
    *Source:* [`OPR_S2.2`](../ref_repo/openpose/OPR_openpose_report.md#22-licence), quoting
    `ref_repo/openpose/openpose/LICENSE`
    *Reliability:* Primary. ⚠ Read as an engineer, not a lawyer; a commercial path requires
    qualified review
23. **`[S23]`**
    *Source:* [`OPR_S6`](../ref_repo/openpose/OPR_openpose_report.md#6-performance), quoting
    `ref_repo/openpose/openpose/doc/06_maximizing_openpose_speed.md`
    *Reliability:* Official but self-reported by the project; not independently reproduced here
24. **`[S24]`**
    *Source:* [`DHR`](../ref_repo/depthai-hand-tracker/DHR_depthai_report.md), reporting
    `ref_repo/depthai-hand-tracker/depthai_hand_tracker/` at `9773123` — the single-hand tolerance
    counter, handedness averaging, duplicate-hand suppression and the hands-up-only prior
    *Reliability:* Primary for the code; ⚠ the frame-rate observations in that repository's README
    are one practitioner's, not a benchmark

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
   [`APR`](../ref_repo/apple/APR_apple_report.md) after that document moved and was recoded.
