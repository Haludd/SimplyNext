**RISK REGISTER**





# METADATA
<details>
<summary>Document code, status, review date, and usage instructions.</summary>

| Field                   | Value                             |
| :---------------------- | :-------------------------------- |
| **Code**                | `RSK`                             |
| **Status**              | Live                              |
| **Last reviewed**       | 2026-08-28                        |
| **Source of truth for** | Known problems                    |
| **Parent**              | [`SCR`](scribbles.md)             |
| **Solutions live in**   | [`ARC`](ARC_architecture.md)      |
| **Contents**            | 136 risks across eight categories |

**For the team.** An expansion of the *Evaluation* and *Issues* sections of
[`SCR`](scribbles.md) into a catalogue of potential problems. It identifies problems and does not
solve them; that separation is deliberate — see [`RSK_S1.1`](#11-overview).
[`RSK_S10`](#10-top-ten-risks) is the shortlist.

**For the assistant.** Do not add mitigations to this file. Risk IDs are permanent and are never
reused. New risks append to the relevant category with the next free number in that category's
sequence.

</details>

---





# 1. HOW TO USE THIS DOCUMENT
## 1.1. Overview
A **problem catalogue**. Every entry names something that can go wrong, states why it bites *this*
product specifically, and describes the signal by which it would be noticed.

> **Note — no solutions here, by design.** Mixing risks and mitigations in one document produces a
> register nobody can audit: every risk looks handled because a sentence next to it says so.
> Keeping them apart makes the unaddressed count visible. Mitigations belong in
> [`ARC`](ARC_architecture.md) and are referenced there by risk ID, never described here.




## 1.2. Coverage
[`SCR`](scribbles.md) lists five areas of difficulty (covered hands, multiple signers, environment
noise, depth perception, motion blur) and two issues (training an LLM, memory loss or
hallucination). Those seven are all present below — `CAP-4`, `CNV-1`, `CAP-6`, `CAP-8`, `CAP-2`,
`MOD-9`, `AGT-1` — alongside 129 more that the original list does not reach.




## 1.3. Identifiers and Ratings
Every risk has a permanent ID of the form `<CAT>-<n>`. IDs are never reused.

| Category                      | Prefix | Section                                      |
| :---------------------------- | :----- | :------------------------------------------- |
| Capture and vision            | `CAP`  | [`RSK_S2`](#2-capture-and-vision)            |
| Linguistic                    | `LNG`  | [`RSK_S3`](#3-linguistic)                    |
| Data and model                | `MOD`  | [`RSK_S4`](#4-data-and-model)                |
| Multi-person and conversation | `CNV`  | [`RSK_S5`](#5-multi-person-and-conversation) |
| System and platform           | `SYS`  | [`RSK_S6`](#6-system-and-platform)           |
| Agent and LLM                 | `AGT`  | [`RSK_S7`](#7-agent-and-llm)                 |
| Human, ethical and legal      | `HUM`  | [`RSK_S8`](#8-human-ethical-and-legal)       |
| Delivery and competition      | `DEL`  | [`RSK_S9`](#9-delivery-and-competition)      |

**Severity** — consequence if it happens:

| Rating | Meaning                                                              |
| :----- | :------------------------------------------------------------------- |
| **S3** | Product is wrong in a way that harms a user, or the submission fails |
| **S2** | Materially degrades quality, or costs a judging point                |
| **S1** | Visible but survivable                                               |

**Likelihood** — in a four-day build, with this team:

| Rating | Meaning                      |
| :----- | :--------------------------- |
| **L3** | Expect it                    |
| **L2** | Likely under demo conditions |
| **L1** | Possible                     |

---





# 2. CAPTURE AND VISION
Failures of the signal before any model sees it. These are the cheapest to induce accidentally and
the most visible on stage.




## 2.1. Optical and Photometric
1.  **`CAP-1`** · *Sev:* S2 · *Lik:* L3
    *Risk:* **Low light.** Landmark detectors degrade as the sensor gains up and noise rises
    *Impact:* Demo rooms and clinics are not photo studios. Confidence drops silently before
    detection fails outright
2.  **`CAP-2`** · *Sev:* S3 · *Lik:* L3
    *Risk:* **Motion blur.** Fast signs blur the hands past recognition at typical webcam shutter
    speeds
    *Impact:* Hand *movement* is a phoneme in sign language. The fastest, most information-dense
    moments are exactly the ones that blur
3.  **`CAP-3`** · *Sev:* S2 · *Lik:* L2
    *Risk:* **Backlight and glare.** A window or lamp behind the signer silhouettes them; a screen
    reflection washes out the face
    *Impact:* Silhouetting destroys handshape and all facial signal at once
4.  **`CAP-4`** · *Sev:* S3 · *Lik:* L3
    *Risk:* **Self-occlusion.** Hands cross, overlap, or pass in front of the face and torso
    *Impact:* ⚠ Named in [`SCR`](scribbles.md). The literature confirms *"easy occlusion and
    blurring of hands"* as a core obstacle in continuous recognition `[S1]`. Two-handed signs
    occlude **by design**
5.  **`CAP-5`** · *Sev:* S2 · *Lik:* L3
    *Risk:* **Out-of-frame signing.** Signing space extends above the head and beyond the shoulders;
    a laptop webcam crops it
    *Impact:* Signs distinguished only by location become identical when the location is off-screen
6.  **`CAP-6`** · *Sev:* S2 · *Lik:* L2
    *Risk:* **Background motion.** People walking behind the signer, screens, ceiling fans
    *Impact:* Can capture the person-tracker or introduce spurious detections. ⚠ Named in
    [`SCR`](scribbles.md) as "environment noises"
7.  **`CAP-7`** · *Sev:* S1 · *Lik:* L2
    *Risk:* **Visually similar background.** Skin-toned wall, wooden furniture, a poster of a person
    *Impact:* Detectors trained on natural images have known false-positive modes here
8.  **`CAP-8`** · *Sev:* S2 · *Lik:* L3
    *Risk:* **No reliable depth.** Movement toward and away from the camera is a real signing
    dimension and a single RGB camera measures it poorly
    *Impact:* ⚠ Named in [`SCR`](scribbles.md). MediaPipe world landmarks are metric only *within* a
    hand, origin at the hand's geometric centre `[S2]` — they do not place the hand in the room
9.  **`CAP-9`** · *Sev:* S3 · *Lik:* L2
    *Risk:* **Skin tone, lighting interaction, and appearance bias.** Detector accuracy is not
    uniform across skin tones, hand sizes, nail polish, rings, sleeves, gloves for warmth
    *Impact:* An accessibility product that works less well for some users is a failure with a moral
    dimension, not just a metric
10. **`CAP-10`** · *Sev:* S2 · *Lik:* L2
    *Risk:* **Signer wears glasses, a mask, or a head covering**
    *Impact:* Masks remove the mouth channel entirely — the channel that carries lexical and
    morphological marking `[S3]`




## 2.2. Geometric
1. **`CAP-11`** · *Sev:* S2 · *Lik:* L3
   *Risk:* **Camera angle.** Off-axis, low (laptop), or high mounting foreshortens the signing plane
   *Impact:* Every training video was shot from one viewpoint. The deployment will not be
2. **`CAP-12`** · *Sev:* S2 · *Lik:* L3
   *Risk:* **Distance.** Too close crops the signing space; too far and hands drop below the
   detector's resolution
   *Impact:* The usable band is narrower than users expect and is never signposted
3. **`CAP-13`** · *Sev:* S3 · *Lik:* L2
   *Risk:* **Mirroring.** Front cameras usually preview mirrored. Whether the *pixels* are mirrored
   is a separate question from whether the *preview* is
   *Impact:* Silently swaps left and right hand — inverting dominant/non-dominant role, which is
   grammatical information
4. **`CAP-14`** · *Sev:* S2 · *Lik:* L2
   *Risk:* **Rotation and orientation.** Phone rotated, tablet in landscape, video captured in a
   different orientation than assumed
   *Impact:* Apple's own sample sidesteps this by locking to portrait and hard-coding `orientation:
   .up` — see [`APL_S5.2`](../doc/APL_apple_ref_report.md#52-coordinate-spaces--three-of-them). That
   shortcut is not available here
5. **`CAP-15`** · *Sev:* S1 · *Lik:* L2
   *Risk:* **Aspect-ratio and letterbox mismatch** between the model's input, the preview, and the
   source video
   *Impact:* Produces landmarks that are correct and drawn in the wrong place — a bug that looks
   like a tracking failure




## 2.3. Subject Selection and Framing
1. **`CAP-16`** · *Sev:* S2 · *Lik:* L2
   *Risk:* **Wrong subject chosen.** Someone nearer the camera than the signer is picked as the
   subject
   *Impact:* "Largest hand wins" is a heuristic, and heuristics have adversaries — including a
   helpful bystander who gestures
2. **`CAP-17`** · *Sev:* S3 · *Lik:* L2
   *Risk:* **Subject flip mid-utterance.** Tracker switches person between frames
   *Impact:* Splices two people's signing into one sentence. Fails silently and confidently
3. **`CAP-18`** · *Sev:* S2 · *Lik:* L2
   *Risk:* **Signer moves, leans, or turns** during an utterance
   *Impact:* Body-relative normalisation assumes a stable torso reference
4. **`CAP-19`** · *Sev:* S2 · *Lik:* L2
   *Risk:* **Partial visibility.** Signer seated behind a desk, or only the upper chest is in frame
   *Impact:* Removes the lower signing space and the torso reference at once




## 2.4. Sensor and Pipeline
1. **`CAP-20`** · *Sev:* S2 · *Lik:* L3
   *Risk:* **Variable frame rate.** Webcams drop frame rate in low light; browsers throttle
   background tabs
   *Impact:* A temporal model trained at a fixed rate sees a time-warped signal it was never shown
2. **`CAP-21`** · *Sev:* S1 · *Lik:* L2
   *Risk:* **Rolling shutter.** Fast lateral hand motion shears within a single frame
   *Impact:* Distorts handshape precisely during fast movement
3. **`CAP-22`** · *Sev:* S1 · *Lik:* L2
   *Risk:* **Auto-exposure and auto-focus hunting.** The camera re-meters when a hand enters frame
   *Impact:* Produces a brightness or sharpness step in the middle of a sign
4. **`CAP-23`** · *Sev:* S2 · *Lik:* L2
   *Risk:* **Compression artefacts** from a video-call pipeline or a compressed recording
   *Impact:* Fingers are thin, high-frequency structures — the first thing a codec discards
5. **`CAP-24`** · *Sev:* S2 · *Lik:* L2
   *Risk:* **Coordinate-space error.** Three coordinate systems are in play; MediaPipe's origin is
   top-left where Apple's Vision is bottom-left
   *Impact:* Documented explicitly as the most likely porting bug —
   [`APL_S10.2`](../doc/APL_apple_ref_report.md#102-swift--python-port-table)

---





# 3. LINGUISTIC
The risks that come from sign language being a language, not a gesture set. These are the ones a
purely engineering-minded team will under-weight, and the ones a knowledgeable judge will probe.




## 3.1. Non-manual Grammar
1. **`LNG-1`** · *Sev:* S3 · *Lik:* L3
   *Risk:* **Non-manual markers ignored or under-modelled.** Brow raise, brow furrow, head tilt,
   torso shift, eye gaze, mouthing
   *Impact:* Erard's critique of glove systems is that they *"misconstrue the nature of ASL […] by
   focusing on what the hands do"*, when grammar includes *"raised or lowered eyebrows, a shift in
   the orientation of the signer's torso, or a movement of the mouth"* `[S4]`. **Any hands-only
   system inherits this criticism in full**
2. **`LNG-2`** · *Sev:* S3 · *Lik:* L3
   *Risk:* **Sentence type is carried non-manually.** In many sign languages the difference between
   a statement, a yes/no question and a conditional is a facial marker, not a word
   *Impact:* The same hand sequence can be *"you are going"*, *"are you going?"* or *"if you go…"*.
   Getting this wrong changes meaning, not style
3. **`LNG-3`** · *Sev:* S3 · *Lik:* L2
   *Risk:* **Negation is non-manual.** A headshake can negate an entire clause with no manual sign
   *Impact:* The system can output the exact opposite of what was signed, fluently and confidently
4. **`LNG-4`** · *Sev:* S2 · *Lik:* L2
   *Risk:* **Facial expression is doubly loaded** — it encodes grammar *and* affect simultaneously
   *Impact:* ⚠ The literature identifies exactly this ambiguity: the same facial movement can
   indicate a linguistic function or an emotional response `[S3]`. A model must disentangle them;
   the current design will not
5. **`LNG-5`** · *Sev:* S2 · *Lik:* L2
   *Risk:* **Different regions of the face carry different levels.** Upper face for syntax and
   prosody; mouth for lexis and morphology `[S3]`
   *Impact:* Sampling "some face landmarks" without knowing which is a coin flip




## 3.2. Structure and Segmentation
1. **`LNG-6`** · *Sev:* S3 · *Lik:* L3
   *Risk:* **Coarticulation.** Signs deform under the influence of their neighbours; the transition
   between two signs looks like a third
   *Impact:* Named in the recognition literature alongside occlusion as a core obstacle `[S1]`.
   There are no spaces in signing
2. **`LNG-7`** · *Sev:* S3 · *Lik:* L3
   *Risk:* **No sign boundaries.** Continuous signing must be segmented before it can be recognised
   *Impact:* Segmentation errors cascade: one bad boundary corrupts every downstream sign in the
   utterance
3. **`LNG-8`** · *Sev:* S2 · *Lik:* L3
   *Risk:* **Transitional movement mistaken for a sign.** The hand travelling between two signs is
   meaningless motion the classifier has never been told to ignore
   *Impact:* Produces phantom words inside otherwise correct sentences
4. **`LNG-9`** · *Sev:* S3 · *Lik:* L3
   *Risk:* **Sign languages are not word-ordered spoken languages.** Topic-comment structure,
   spatial agreement, simultaneity
   *Impact:* A gloss-to-word mapping produces something that reads like broken English and is not a
   translation
5. **`LNG-10`** · *Sev:* S2 · *Lik:* L2
   *Risk:* **Simultaneity.** Two hands can carry two different pieces of information at once; the
   face can carry a third
   *Impact:* Sequential output cannot represent simultaneous input without a decision about how to
   linearise it




## 3.3. Lexicon and Reference
1. **`LNG-11`** · *Sev:* S3 · *Lik:* L3
   *Risk:* **Fingerspelling.** Names, addresses, brands and unknown words are spelled letter by
   letter, fast, with heavy coarticulation
   *Impact:* Exactly the content that matters most in a clinic or service counter, and the hardest
   to recognise
2. **`LNG-12`** · *Sev:* S3 · *Lik:* L2
   *Risk:* **Spatial referencing (loci).** A signer assigns a referent to a point in space and
   points back to it later
   *Impact:* The meaning of a pointing sign depends on something established seconds earlier.
   Stateless recognition cannot resolve it
3. **`LNG-13`** · *Sev:* S3 · *Lik:* L2
   *Risk:* **Classifier / depicting constructions.** Productive, quasi-iconic forms that are not
   lexical items and cannot be listed in a vocabulary
   *Impact:* Unbounded by definition, so a closed vocabulary cannot cover them
4. **`LNG-14`** · *Sev:* S3 · *Lik:* L2
   *Risk:* **Number, time and quantity systems** are structurally distinct from spoken-language
   numerals
   *Impact:* Dosages, times, prices, room numbers — the highest-consequence content in any practical
   scenario
5. **`LNG-15`** · *Sev:* S2 · *Lik:* L3
   *Risk:* **Regional and generational variation.** Different signs for the same concept across
   communities and age groups
   *Impact:* SADeaf describes SgSL as a combination of Shanghainese Sign Language, ASL, Signing
   Exact English and locally developed signs `[S5]` — genuine internal variation, not noise
6. **`LNG-16`** · *Sev:* S3 · *Lik:* L3
   *Risk:* **SgSL is not ASL.** Nearly all public datasets, pretrained models and benchmarks are ASL
   or European sign languages
   *Impact:* A model trained on ASL and demoed as a Singapore solution is a mismatch a local judge
   will catch
7. **`LNG-17`** · *Sev:* S2 · *Lik:* L2
   *Risk:* **Register and code-switching.** Signers shift between SgSL, Signing Exact English and
   mouthed English depending on the interlocutor
   *Impact:* The input distribution changes based on who the signer thinks they are talking to —
   including a machine
8. **`LNG-18`** · *Sev:* S2 · *Lik:* L3
   *Risk:* **Signer idiolect.** Personal signs, name signs, individual style
   *Impact:* Unseen at training time by construction
9. **`LNG-19`** · *Sev:* S1 · *Lik:* L2
   *Risk:* **Prosody and emphasis.** Speed, size and repetition of a sign carry emphasis and aspect
   *Impact:* Discarded by a classifier that only reads sign identity

---





# 4. DATA AND MODEL
## 4.1. Data
1. **`MOD-1`** · *Sev:* S3 · *Lik:* L3
   *Risk:* **Data scarcity.** Over 300 sign languages are described as *"severely low-resource due
   to limited documentation, sparse datasets, and insufficient computational tools"* `[S6]`
   *Impact:* SgSL is squarely in that group. There is no large public SgSL corpus to train on
2. **`MOD-2`** · *Sev:* S3 · *Lik:* L3
   *Risk:* **Self-collected data is tiny and unrepresentative.** Anything recorded in four days will
   be a handful of signers in one room
   *Impact:* Trains a model that recognises *those signers*, in *that room*
3. **`MOD-3`** · *Sev:* S3 · *Lik:* L2
   *Risk:* **Signer overlap between train and test.** The easiest split to get wrong
   *Impact:* Inflates reported accuracy dramatically. A signer-independent split is a different,
   much harder number
4. **`MOD-4`** · *Sev:* S3 · *Lik:* L2
   *Risk:* **Label quality.** Sign annotation requires fluency; a hearing team labelling from video
   will make systematic errors
   *Impact:* Errors correlate with the hardest cases, so they hide precisely where accuracy matters
5. **`MOD-5`** · *Sev:* S2 · *Lik:* L3
   *Risk:* **Glosses are not translations.** A gloss is a label for a sign, not a word of English
   *Impact:* Treating a gloss sequence as a sentence produces confident nonsense
6. **`MOD-6`** · *Sev:* S3 · *Lik:* L2
   *Risk:* **Demographic skew.** Age, gender, skin tone, handedness, disability affecting the hands
   *Impact:* Compounds `CAP-9`. A left-dominant signer may be effectively unsupported
7. **`MOD-7`** · *Sev:* S3 · *Lik:* L2
   *Risk:* **Consent and provenance of training video.** Sign-language video is identifiable by
   definition — the face is the data
   *Impact:* Scraped or borrowed video carries consent problems that are not hypothetical for this
   community




## 4.2. Model and Evaluation
1.  **`MOD-8`** · *Sev:* S3 · *Lik:* L3
    *Risk:* **Closed vocabulary is a hard ceiling.** Anything outside it cannot be recognised, only
    mis-recognised
    *Impact:* Users do not know where the boundary is, and the system gives no sign of having
    crossed it
2.  **`MOD-9`** · *Sev:* S2 · *Lik:* L3
    *Risk:* **Confusion between visually similar signs.** Minimal pairs differing only in one finger
    or one facial marker
    *Impact:* ⚠ Adding facial features is reported to reduce such confusion *from 37% to 11%* `[S7]`
    — meaning it is very high without them, and non-zero with them
3.  **`MOD-10`** · *Sev:* S2 · *Lik:* L2
    *Risk:* **Pose loses information RGB retains.** A pose vector is under 150 numbers against over
    786,000 pixel features in a 512×512 frame `[S8]`
    *Impact:* Fine handshape, finger contact and touch are compressed into joint positions that may
    not distinguish them
4.  **`MOD-11`** · *Sev:* S3 · *Lik:* L2
    *Risk:* **Landmark model failure is invisible downstream.** MediaPipe emits coordinates whether
    or not it is confident
    *Impact:* A plausible-looking skeleton on garbage input is worse than no skeleton
5.  **`MOD-12`** · *Sev:* S2 · *Lik:* L2
    *Risk:* **Accuracy figures in the literature are not comparable.** Reported ranges — WLASL-100
    RGB 65.89–80.72%, pose 55.43–81.47% `[S8]` — are on curated, isolated-sign, studio-recorded
    benchmarks
    *Impact:* Quoting them as expected performance here would be misleading, and continuous
    real-world signing is much harder than isolated recognition
6.  **`MOD-13`** · *Sev:* S1 · *Lik:* L2
    *Risk:* **Published progress may itself be overstated.** A 2026 unified re-implementation found
    that *"many of the performance gains reported in the literature often diminish when models are
    evaluated under consistent conditions"* `[S9]`
    *Impact:* Any cited baseline may be optimistic
7.  **`MOD-14`** · *Sev:* S2 · *Lik:* L2
    *Risk:* **BLEU and similar metrics do not measure whether a deaf person was understood**
    *Impact:* The field is explicitly moving *"from reference-based to task-specific metrics"*
    `[S6]`. A good BLEU score is not evidence of a working product
8.  **`MOD-15`** · *Sev:* S3 · *Lik:* L3
    *Risk:* **Overfitting to the demo.** Four days of iteration against one demo script
    *Impact:* The measurement then covers only what was tuned. Real generalisation is untested
9.  **`MOD-16`** · *Sev:* S3 · *Lik:* L3
    *Risk:* **Confidence scores are uncalibrated.** A classifier's softmax output is not a
    probability
    *Impact:* Every downstream decision — gate, threshold, repair trigger — rests on this number
    being meaningful
10. **`MOD-17`** · *Sev:* S2 · *Lik:* L2
    *Risk:* **Temporal window mismatch.** Sign duration varies by several times between signs and
    between signers
    *Impact:* A fixed window truncates long signs and pads short ones with neighbours
11. **`MOD-18`** · *Sev:* S2 · *Lik:* L2
    *Risk:* **Class imbalance.** Common signs dominate; rare signs are never learned
    *Impact:* The rare signs are often the informative ones

---





# 5. MULTI-PERSON AND CONVERSATION
## 5.1. Multiple People
1. **`CNV-1`** · *Sev:* S2 · *Lik:* L2
   *Risk:* **Two or more people signing at once.** ⚠ Named in [`SCR`](scribbles.md)
   *Impact:* Requires per-person tracking, per-person state, and per-person attribution — three
   systems where the plan has one
2. **`CNV-2`** · *Sev:* S3 · *Lik:* L2
   *Risk:* **Utterance mis-attribution.** The right words assigned to the wrong person
   *Impact:* In a medical or legal setting this is a serious harm, not a UI glitch
3. **`CNV-3`** · *Sev:* S2 · *Lik:* L3
   *Risk:* **Bystander gestures read as signs.** A wave, a point, someone scratching their nose
   *Impact:* Produces words that nobody said. Undetectable from inside the pipeline
4. **`CNV-4`** · *Sev:* S2 · *Lik:* L1
   *Risk:* **Interpreter present.** A human interpreter in frame signing the hearing person's words
   *Impact:* The system may caption the interpreter as if they were the deaf participant




## 5.2. Conversation Dynamics
1. **`CNV-5`** · *Sev:* S2 · *Lik:* L2
   *Risk:* **Turn-taking is not modelled.** Signed conversation has its own turn structure,
   including overlap
   *Impact:* Captions arriving out of turn are worse than late captions
2. **`CNV-6`** · *Sev:* S3 · *Lik:* L3
   *Risk:* **One-way communication.** Erard's critique of gloves is that they *"render ASL
   intelligible to hearing people"* while the hearing person cannot respond through them `[S4]`
   *Impact:* ⚠ **This system has the same shape unless the return channel is designed.** A
   structural criticism of the product concept, not of its implementation
3. **`CNV-7`** · *Sev:* S3 · *Lik:* L2
   *Risk:* **The signer cannot see what was said on their behalf** unless the output is placed where
   they can see it
   *Impact:* A translation the speaker cannot check is a translation they cannot correct
4. **`CNV-8`** · *Sev:* S2 · *Lik:* L2
   *Risk:* **No repair mechanism matching how humans repair.** Deaf signers repair misunderstanding
   constantly and rapidly
   *Impact:* A system that cannot be corrected in the flow of conversation gets abandoned
5. **`CNV-9`** · *Sev:* S2 · *Lik:* L3
   *Risk:* **Latency breaks conversational rhythm.** Even one to two seconds changes who speaks next
   *Impact:* Measured accuracy can be fine while the conversation is unusable
6. **`CNV-10`** · *Sev:* S2 · *Lik:* L3
   *Risk:* **Utterance boundaries are guessed.** A pause is not reliably the end of a sentence
   *Impact:* Splits or merges sentences, changing meaning

---





# 6. SYSTEM AND PLATFORM
1.  **`SYS-1`** · *Sev:* S2 · *Lik:* L3
    *Risk:* **End-to-end latency exceeds usability** once capture, segmentation, classification and
    a cloud round trip are summed
    *Impact:* Each stage is individually acceptable and the total is not
2.  **`SYS-2`** · *Sev:* S2 · *Lik:* L2
    *Risk:* **Frame backlog.** If processing is slower than capture, the queue grows and output
    falls further behind with time
    *Impact:* The system appears to work at first and degrades over a long demo
3.  **`SYS-3`** · *Sev:* S2 · *Lik:* L2
    *Risk:* **Thread and queue design.** Apple's sample uses `DispatchQueue.main.sync` as
    back-pressure; the equivalent naive port deadlocks or stalls —
    [`APL_S4.3`](../doc/APL_apple_ref_report.md#43-threading-model)
    *Impact:* Easy to copy the pattern without the reasoning
4.  **`SYS-4`** · *Sev:* S2 · *Lik:* L2
    *Risk:* **CPU thermal throttling** on a laptop during a long demo
    *Impact:* Frame rate drops mid-presentation, changing the input distribution the model sees
5.  **`SYS-5`** · *Sev:* S2 · *Lik:* L3
    *Risk:* **Device fragmentation.** [`SCR`](scribbles.md) promises phones, tablets, computers and
    glasses
    *Impact:* Each has a different camera, frame rate, orientation and compute budget. Each is a
    separate integration
6.  **`SYS-6`** · *Sev:* S2 · *Lik:* L2
    *Risk:* **Browser and permission friction.** Camera permission, HTTPS requirements,
    background-tab throttling
    *Impact:* Fails on a stranger's machine in ways it never fails on a development machine
7.  **`SYS-7`** · *Sev:* S2 · *Lik:* L2
    *Risk:* **Network dependency.** The agent stage requires connectivity
    *Impact:* Contradicts the "works anywhere" positioning, and venue Wi-Fi is a genuine demo-day
    risk
8.  **`SYS-8`** · *Sev:* S3 · *Lik:* L2
    *Risk:* **AWS budget cap.** `D6` states access is revoked at **US$20** and the account
    terminated at **US$30**, with additional leases *"not granted"* barring exceptions
    *Impact:* A runaway loop can end the project, not just cost money
9.  **`SYS-9`** · *Sev:* S2 · *Lik:* L2
    *Risk:* **Bedrock model access is per-model and per-region.** `D1` warns *"valid credentials do
    not guarantee a working call"*
    *Impact:* Fails at exactly the wrong moment, with an error that looks like a code bug
10. **`SYS-10`** · *Sev:* S1 · *Lik:* L3
    *Risk:* **SSO session expiry.** `D1` notes sessions expire after 8–12 hours
    *Impact:* Predictable, and predictably forgotten on the morning of a deadline
11. **`SYS-11`** · *Sev:* S2 · *Lik:* L2
    *Risk:* **Single shared AWS account** across the team, with one lease per group `[D6]`
    *Impact:* One member's runaway job spends everyone's budget
12. **`SYS-12`** · *Sev:* S1 · *Lik:* L2
    *Risk:* **Model or API drift.** Pinned model IDs, region prefixes and SDK versions change
    *Impact:* `D3` explicitly advises reading model IDs from a constant, *"never build them"*
13. **`SYS-13`** · *Sev:* S2 · *Lik:* L2
    *Risk:* **No teardown.** `D2` warns that `destroy` leaves shared infrastructure — S3 buckets,
    ECR repositories, CloudWatch log groups — behind
    *Impact:* Silent ongoing spend against the cap

---





# 7. AGENT AND LLM
The category with the highest severity concentration, because these failures are **fluent**.




## 7.1. Fabrication
1. **`AGT-1`** · *Sev:* S3 · *Lik:* L3
   *Risk:* **Hallucinated meaning.** Handed a noisy, low-confidence gloss sequence, a language model
   will produce a grammatical, plausible, confident sentence regardless
   *Impact:* ⚠ Named in [`SCR`](scribbles.md). **This is the single most dangerous failure mode in
   the product.** The output is not merely wrong — it puts words in a deaf person's mouth, in their
   voice, to a hearing listener who has no way to check
2. **`AGT-2`** · *Sev:* S3 · *Lik:* L3
   *Risk:* **Plausible completion of a partial utterance.** The model finishes a sentence the signer
   had not finished
   *Impact:* Indistinguishable from correct output at the point of use
3. **`AGT-3`** · *Sev:* S3 · *Lik:* L2
   *Risk:* **Prior-driven guessing.** The model fills gaps from what people usually say in that
   context rather than from the glosses
   *Impact:* Systematically biases output toward the expected, which is exactly wrong when the
   signer is saying something unexpected
4. **`AGT-4`** · *Sev:* S3 · *Lik:* L3
   *Risk:* **Fluency masks failure.** Well-formed English reads as understanding
   *Impact:* Users, judges and the team all over-trust it. This is a failure mode of *evaluation* as
   much as of the system
5. **`AGT-5`** · *Sev:* S2 · *Lik:* L2
   *Risk:* **The critic agrees with the assembler.** Two calls to the same model share the same
   priors and the same blind spots
   *Impact:* A reflection loop can produce confidence without adding information




## 7.2. Loop and Context
1. **`AGT-6`** · *Sev:* S3 · *Lik:* L2
   *Risk:* **Unbounded loops.** `D3_p22`: *"A refine loop that exits when the critic is satisfied
   will sometimes never be satisfied, and we discover it from the bill"*
   *Impact:* Directly compounds `SYS-8`
2. **`AGT-7`** · *Sev:* S2 · *Lik:* L3
   *Risk:* **Context rot.** `D3_p22`: *"Well before the limit, accuracy and consistency degrade
   while cost and latency rise on every turn of the loop"*
   *Impact:* A long conversation degrades gradually rather than failing visibly
3. **`AGT-8`** · *Sev:* S2 · *Lik:* L2
   *Risk:* **Payload bloat.** Landmark arrays or frame data reaching the prompt
   *Impact:* `D2` is explicit that heavy payloads belong in graph state and prompts should carry
   only metadata or references. Violating this multiplies cost per turn
4. **`AGT-9`** · *Sev:* S2 · *Lik:* L2
   *Risk:* **Vague tool descriptions.** `D3_p22`: *"A vague description produces an unused tool or a
   badly called one"*
   *Impact:* Fails as under-use, which is invisible, rather than as an error
5. **`AGT-10`** · *Sev:* S2 · *Lik:* L2
   *Risk:* **Output schema violations.** Free-text where structured output was expected
   *Impact:* `D3_p32` makes schema validation pass rate a headline metric for a reason
6. **`AGT-11`** · *Sev:* S2 · *Lik:* L3
   *Risk:* **Non-determinism.** `D1`: *"The same input may therefore yield a different answer on a
   second attempt"*
   *Impact:* Undermines both reproducibility and the demo
7. **`AGT-12`** · *Sev:* S1 · *Lik:* L2
   *Risk:* **Truncation at `max_tokens`.** `D1`: cut prose still reads as complete; cut JSON fails
   to parse and *"looks like a model error but is not"*
   *Impact:* Silent for text output, confusing for structured output




## 7.3. Prompt and Lexicon Integrity
1. **`AGT-13`** · *Sev:* S2 · *Lik:* L1
   *Risk:* **Retrieved lexicon content is trusted as instruction** rather than as data
   *Impact:* Any content injected into the prompt from a store becomes a possible instruction
   channel
2. **`AGT-14`** · *Sev:* S2 · *Lik:* L2
   *Risk:* **Stale or wrong lexicon entries** propagate as authoritative translations
   *Impact:* The system's confidence comes from the lexicon, not from the evidence
3. **`AGT-15`** · *Sev:* S2 · *Lik:* L2
   *Risk:* **Personalisation memory poisoned.** Per-signer adaptation learns from a mis-recognition
   the user did not correct
   *Impact:* Degrades over time, in a way that only affects that user




## 7.4. Confidence and Honesty
1. **`AGT-16`** · *Sev:* S3 · *Lik:* L3
   *Risk:* **No calibrated notion of "unsure".** Without one, there is nothing to threshold on and
   no basis to refuse
   *Impact:* Every honesty mechanism in the design depends on this one number being meaningful.
   Compounds `MOD-16`
2. **`AGT-17`** · *Sev:* S2 · *Lik:* L3
   *Risk:* **The threshold is a guess.** Too high and the system constantly asks for repeats; too
   low and it fabricates
   *Impact:* There is no safe default, and both failure directions are user-visible
3. **`AGT-18`** · *Sev:* S3 · *Lik:* L2
   *Risk:* **Uncertainty is not communicated to the hearing listener.** The listener hears a fluent
   sentence and cannot tell it was a guess
   *Impact:* Shifts the entire burden of verification onto the deaf user
4. **`AGT-19`** · *Sev:* S2 · *Lik:* L2
   *Risk:* **Confidence is displayed but ignored.** A number on screen that no one reads is not a
   safeguard
   *Impact:* Common failure of "the confidence score is displayed" designs

---





# 8. HUMAN, ETHICAL AND LEGAL
These determine whether the product *should* exist in the form proposed, and several map
directly onto judging criteria.




## 8.1. Community and Legitimacy
1. **`HUM-1`** · *Sev:* S3 · *Lik:* L3
   *Risk:* **Built without Deaf involvement.** The literature is blunt: *"research in this domain is
   performed mostly by computer scientists in isolation"*, and *"the inclusion of deaf and hearing
   end users […] in use case identification, data collection and evaluation is of the utmost
   importance"* `[S10]`
   *Impact:* ⚠ Also `D3_p7`'s **"Comfortable Guess"** failure mode, which costs points under
   [`JCR_S4.3`](JCR_judging_criteria.md#43-problem-statement-failure-modes) — a rare case where the
   ethical and scoring risks are literally the same risk
2. **`HUM-2`** · *Sev:* S3 · *Lik:* L2
   *Risk:* **Solving the hearing world's problem.** Gloves are criticised as *"rooted in the
   preoccupations of the hearing world, not the needs of Deaf signers"* `[S4]`
   *Impact:* A camera-based system inherits this unless the deaf user's needs drive the design
3. **`HUM-3`** · *Sev:* S2 · *Lik:* L2
   *Risk:* **Framing sign language as a deficit to be corrected** rather than a language to be
   translated
   *Impact:* Language, tone and demo framing all carry this risk, independently of the technology
4. **`HUM-4`** · *Sev:* S2 · *Lik:* L2
   *Risk:* **Displacing rather than supporting interpreters.** SADeaf lists 2 Deaf and more than 6
   hearing staff interpreters, plus 55 community interpreters on an ad-hoc basis `[S11]`
   *Impact:* A small professional community. Positioning matters, and getting it wrong is both a
   harm and a credibility loss
5. **`HUM-5`** · *Sev:* S3 · *Lik:* L2
   *Risk:* **Over-claiming capability.** Presenting a closed-vocabulary demo as general translation
   *Impact:* Users may rely on it in situations where it cannot work. Also directly attacks C2 and
   C5 — see [`JCR_S2.2`](JCR_judging_criteria.md#22-c2--original--innovative-idea-20)




## 8.2. Consequences of Error
1. **`HUM-6`** · *Sev:* S3 · *Lik:* L2
   *Risk:* **High-stakes settings.** Medical, legal, financial, emergency
   *Impact:* The scenarios with the greatest need have the least tolerance for error
2. **`HUM-7`** · *Sev:* S3 · *Lik:* L2
   *Risk:* **No liability or accountability model.** Who is responsible when a mistranslation causes
   harm
   *Impact:* Unanswered by every system in this space, this one included
3. **`HUM-8`** · *Sev:* S3 · *Lik:* L2
   *Risk:* **Automation bias.** Hearing listeners will trust the caption over the person
   *Impact:* Compounds `AGT-4` and `AGT-18`. The person who could correct the system is the one
   least likely to be believed
4. **`HUM-9`** · *Sev:* S3 · *Lik:* L2
   *Risk:* **Loss of agency.** Words attributed to a person that they did not say and cannot retract
   *Impact:* The most serious harm the system can cause, and it is a *design* property, not a bug




## 8.3. Privacy and Data Protection
1. **`HUM-10`** · *Sev:* S3 · *Lik:* L2
   *Risk:* **Sign-language video is inherently identifying.** The face is part of the linguistic
   signal and cannot be removed
   *Impact:* Standard anonymisation techniques delete the data. Pose-based representations are
   explicitly named as a privacy-preserving choice in the literature `[S6]` — which implies video is
   the opposite
2. **`HUM-11`** · *Sev:* S3 · *Lik:* L2
   *Risk:* **Continuous video capture of a private conversation**, potentially including bystanders
   who never consented
   *Impact:* An always-on camera in a clinic captures more than the consultation
3. **`HUM-12`** · *Sev:* S2 · *Lik:* L2
   *Risk:* **Cloud transmission.** Anything leaving the device increases exposure
   *Impact:* Compounds `HUM-10` and `HUM-11`
4. **`HUM-13`** · *Sev:* S2 · *Lik:* L2
   *Risk:* **PDPA and comparable obligations** around collection, purpose limitation and retention
   of personal data in Singapore
   *Impact:* Applies to recorded training data, not only to the deployed product
5. **`HUM-14`** · *Sev:* S2 · *Lik:* L2
   *Risk:* **Retention of conversation transcripts and personalisation memory**
   *Impact:* A record of private conversations that was never intended to be kept
6. **`HUM-15`** · *Sev:* S2 · *Lik:* L2
   *Risk:* **Consent for training data recorded during the hackathon**
   *Impact:* Compounds `MOD-7`. Recording teammates is easy; documenting consent is easy to skip




## 8.4. Accessibility of the Product
1. **`HUM-16`** · *Sev:* S2 · *Lik:* L2
   *Risk:* **Output modality mismatch.** Audio output is useless to the deaf user; the system's own
   feedback must be visual
   *Impact:* An accessibility tool that is not itself accessible
2. **`HUM-17`** · *Sev:* S2 · *Lik:* L2
   *Risk:* **The submission video is uncaptioned.** `D3_p48` asks for *"clear voiceover or captions
   for accessibility"*
   *Impact:* For this project specifically, an uncaptioned demo video is a self-inflicted wound in
   front of the judges most likely to notice
3. **`HUM-18`** · *Sev:* S2 · *Lik:* L2
   *Risk:* **Reading-level and language assumptions** in the output. Written English is a second
   language for many signers
   *Impact:* Fluent English output can be less accessible than a simpler rendering

---





# 9. DELIVERY AND COMPETITION
1.  **`DEL-1`** · *Sev:* S3 · *Lik:* L2
    *Risk:* **"The Solved Problem."** `D3_p7` warns that where *"a mature product already does this
    well […] the bar for our version sits impossibly high"*
    *Impact:* Google announced SignGemma as an open model for sign-language translation at I/O 2025
    `[S12]`. A judge who knows this can legitimately award **0** on C2 —
    [`JCR_S2.2`](JCR_judging_criteria.md#22-c2--original--innovative-idea-20)
2.  **`DEL-2`** · *Sev:* S3 · *Lik:* L3
    *Risk:* **"The Boiling Ocean."** `D3_p7`: a statement *"true, enormous, and beyond what any team
    can move in four days"*
    *Impact:* "Translate sign language" is precisely this shape
3.  **`DEL-3`** · *Sev:* S2 · *Lik:* L3
    *Risk:* **"The Everyone Problem."** A user described as *"deaf people"* rather than one nameable
    person at one moment
    *Impact:* Blocks a 2 on C5 and undermines C1
4.  **`DEL-4`** · *Sev:* S2 · *Lik:* L2
    *Risk:* **"The Missing Because."** Need asserted without evidence
    *Impact:* [`JCR_S4.4`](JCR_judging_criteria.md#44-five-pressure-test-questions) demands *"a
    figure, a source, and a date"*
5.  **`DEL-5`** · *Sev:* S3 · *Lik:* L2
    *Risk:* **Agentic justification is thin.** If the system is a classifier with a language model
    bolted on, `D3_p10`'s test — *"what would a fixed workflow miss?"* — has no good answer
    *Impact:* Attacks C4 and C2 simultaneously
6.  **`DEL-6`** · *Sev:* S3 · *Lik:* L3
    *Risk:* **Demo fragility.** Live camera, live network, live model, live lighting
    *Impact:* Four independent single points of failure on stage
7.  **`DEL-7`** · *Sev:* S3 · *Lik:* L2
    *Risk:* **Demo works only for one team member.** The person it was tuned on
    *Impact:* A judge asking to try it is the fastest way to discover this
8.  **`DEL-8`** · *Sev:* S3 · *Lik:* L2
    *Risk:* **Cannot run from a clean clone.** Missing `requirements.txt`, hard-coded paths,
    committed or missing secrets
    *Impact:* `D3_p42` states judges check *"whether solution can run as demonstrated in video"*
9.  **`DEL-9`** · *Sev:* S2 · *Lik:* L2
    *Risk:* **Evaluation missing from the slides.** `D3_p42` requires *"Testing/Evaluation should be
    covered in your slides"*
    *Impact:* An explicit, easily-avoided point loss
10. **`DEL-10`** · *Sev:* S2 · *Lik:* L2
    *Risk:* **Architecture diagram does not match the code.** `D3_p42` checks *"if presentation
    methodology is reflective at code level"*
    *Impact:* A directly checkable mismatch
11. **`DEL-11`** · *Sev:* S3 · *Lik:* L1
    *Risk:* **Deliverable limits exceeded.** 10 slides, 5 minutes, 5 GB, one submission `[D3_p37,
    p42]`
    *Impact:* Hard limits, and *"1 submission only"* means no second attempt
12. **`DEL-12`** · *Sev:* S3 · *Lik:* L3
    *Risk:* **Scope creep.** Multi-person, multi-language, glasses support, bidirectional
    conversation
    *Impact:* Each is defensible individually; together they guarantee nothing finishes
13. **`DEL-13`** · *Sev:* S2 · *Lik:* L2
    *Risk:* **Team capability mismatch.** Sign-language linguistics, computer vision, agent
    engineering and presentation are four different skills
    *Impact:* No team of three to five has all four in depth
14. **`DEL-14`** · *Sev:* S3 · *Lik:* L3
    *Risk:* **Integration left to the last day.** Perception, model and agent developed separately
    *Impact:* The interfaces are where the time goes
15. **`DEL-15`** · *Sev:* S3 · *Lik:* L2
    *Risk:* **No fallback demo.** If the live pipeline fails on stage, there is nothing to show
    *Impact:* The difference between a bad score and a zero on C4 and C5

---





# 10. TOP TEN RISKS
Every `S3` × `L3` in the register, plus the two structural criticisms of the product concept.

1.  **`AGT-1`** · *Category:* Agent
    *Risk:* Hallucinated meaning — fluent, confident, wrong words attributed to a deaf person
2.  **`LNG-1`** · *Category:* Linguistic
    *Risk:* Non-manual grammar ignored — the exact criticism levelled at every glove system `[S4]`
3.  **`CNV-6`** · *Category:* Conversation
    *Risk:* One-way communication — a structural criticism of the product concept, not the code
4.  **`HUM-1`** · *Category:* Human
    *Risk:* Built without Deaf involvement — an ethical failure and a scoring failure in one
5.  **`LNG-6` / `LNG-7`** · *Category:* Linguistic
    *Risk:* Coarticulation and the absence of sign boundaries — the unsolved core of continuous
    recognition
6.  **`MOD-1` / `MOD-2`** · *Category:* Data
    *Risk:* No SgSL data at scale, and anything recorded is tiny and unrepresentative
7.  **`CAP-2` / `CAP-4`** · *Category:* Capture
    *Risk:* Motion blur and self-occlusion — worst exactly when information density is highest
8.  **`AGT-16`** · *Category:* Agent
    *Risk:* No calibrated notion of "unsure" — every honesty mechanism depends on this one number
9.  **`DEL-2` / `DEL-12`** · *Category:* Delivery
    *Risk:* Boiling the ocean, and scope creep
10. **`DEL-6` / `DEL-15`** · *Category:* Delivery
    *Risk:* Fragile live demo with no fallback

> **Note:** items 3 and 4 are not engineering problems and cannot be fixed by engineering. They are
> the reason [`ARC_S7.5`](ARC_architecture.md#75-p6--gloves-rejected-on-the-record) and
> [`ARC_S9`](ARC_architecture.md#9-decisions) (decision D11) exist.

---





# 11. SOURCES
1.  **`[S1]`**
    *Source:* *Continuous sign language recognition algorithm based on object detection and
    variable-length coding sequence*, Scientific Reports (2024) —
    https://www.nature.com/articles/s41598-024-78319-0
    *Reliability:* Peer-reviewed
2.  **`[S2]`**
    *Source:* Google AI Edge, *Hand landmarks detection guide* —
    https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker
    *Reliability:* Official
3.  **`[S3]`**
    *Source:* *Emotion Recognition in Sign Language Conversation* — https://arxiv.org/pdf/2605.23328
    *Reliability:* ⚠ Preprint
4.  **`[S4]`**
    *Source:* M. Erard, *Why Sign-Language Gloves Don't Help Deaf People* (The Atlantic, 2017), read
    via secondary reproductions —
    https://allthingslinguistic.com/post/167390176466/why-sign-language-gloves-dont-help-deaf-people
    *Reliability:* ⚠ Reputable original; reproductions read, not the original
5.  **`[S5]`**
    *Source:* SADeaf, *Singapore Sign Language (SgSL)* — https://sadeaf.org.sg/faqconc_cat/sgsl/
    *Reliability:* Official (national association)
6.  **`[S6]`**
    *Source:* N. Alishzade, G. Abdullayeva, *Sign Language Recognition and Translation for
    Low-Resource Languages* (2026) — https://arxiv.org/abs/2605.12096
    *Reliability:* ⚠ Preprint
7.  **`[S7]`**
    *Source:* *The Importance of Facial Features in Vision-based Sign Language Recognition* —
    https://arxiv.org/html/2507.20884v1
    *Reliability:* ⚠ Preprint
8.  **`[S8]`**
    *Source:* *SignIT: A Comprehensive Dataset and Multimodal Analysis for Italian Sign Language
    Recognition* — https://arxiv.org/html/2512.14489
    *Reliability:* ⚠ Preprint; accuracy table surveys others' results
9.  **`[S9]`**
    *Source:* O. Mercanoglu Sincan et al., *Gloss-Free Sign Language Translation: An Unbiased
    Evaluation of Progress in the Field* (Feb 2026) — https://arxiv.org/abs/2603.13240
    *Reliability:* ⚠ Preprint, established group
10. **`[S10]`**
    *Source:* M. De Coster et al., *Machine Translation from Signed to Spoken Languages: State of
    the Art and Challenges*, Universal Access in the Information Society (2023) —
    https://arxiv.org/abs/2202.03086
    *Reliability:* Peer-reviewed
11. **`[S11]`**
    *Source:* SADeaf, *Sign Language Interpreters* —
    https://sadeaf.org.sg/faqconc_cat/sl_interpreter/
    *Reliability:* Official (national association)
12. **`[S12]`**
    *Source:* Google, *Building with AI: highlights for developers at Google I/O* (May 2025) —
    https://blog.google/technology/developers/google-ai-developer-updates-io-2025/
    *Reliability:* Official
13. **`[S13]`**
    *Source:* `doc/[D1]`, `[D2]`, `[D3]`, `[D6]` — hackathon training decks
    *Reliability:* Official (organiser)

> **Warning on the preprints.** Six of the thirteen sources above are arXiv preprints and have not
> been peer-reviewed. They are cited here because a risk register is allowed to take a warning
> seriously on weaker evidence than a design decision would need. **Do not put a number from a
> `⚠`-tagged source on a slide without opening the paper first.**

---





# 12. CHANGE LOG
1. **2026-08-28** · *Author:* Claude (Opus 5)
   *Change:* Created. Expanded the seven items in [`SCR`](scribbles.md) into **136 catalogued
   risks** across eight categories (`CAP` 24, `LNG` 19, `MOD` 18, `CNV` 10, `SYS` 13, `AGT` 19,
   `HUM` 18, `DEL` 15), with severity and likelihood ratings and a top-ten. No mitigations included,
   by design.
2. **2026-08-28** · *Author:* Claude (Opus 5)
   *Change:* Reformatted to the revised conventions in
   [`RIX_S4`](../ref_index.md#4-markdown-formatting-rules): bold title, collapsible `# METADATA`,
   `#`-level numbered sections, HTML anchors removed, padded tables, third-person voice,
   placeholders for unfinished content.
3. **2026-08-28** · *Author:* Claude (Opus 5)
   *Change:* Applied the revised [`RIX_S4.4`](../#44-vertical-spacing) heading spacing and the
   [`RIX_S4.5`](../#45-tables-and-numbered-lists) table-versus-numbered-list rule: tables whose rows exceeded 100
   characters became numbered lists.
