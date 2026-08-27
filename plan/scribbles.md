This document is used for ideation with AI

# CONTEXT
We are building a working prototype, preferably production grade, for a Hackathon called SimplifyNext Agentic AI Hackathon. Refer to SimplifyNext or NUS' official websites for further information regarding the competition (timeline, past winners' solutions, ...)

# PROBLEM
There still exists a communication or language barrier between hearing-loss people and those who do not suffer from this condition. They often rely on sign language (not everybody can converse in sign language) or technological solutions to type out what they want to say (disrupts normal conversational flow).

# SOLUTION & PRODUCT
We want to develop a software which seamlessly translates sign-language to conversational text or audio in real-time. This idea took inspiration from auto-captioning function in video streaming platforms such as youtube as well as Google Translate and other similar products.

The software runs on phones, tablets, computers, augmented-reality / smart glasses, essentially any devices that has visual capturing / video features. Without using gloves to translate sign language (which requires the "speaker" to wear the glove device), we want the software to rely entirely on visual data and to produce sensible conversational output in either audio or text form.

Current MVP (concept):
1. Recognise the focus and isolate the person(s) from environment noises (other people within the camera's peripheral, ...).
2. Track multiple points (as many as possible to acquire coherent conversation) on the hands and face (if necessary).
3. Translate the points' motion into a 3D skeleton.
4. Use the skeleton's movements / behaviours to translate them into coherent conversational text / audio

# EVALUATION
These are some areas of difficulty:
1. Covered / invisible hand movement
2. Multiple people performing sign language
3. Environment noises (glare, distracting movement, ...)
4. Depth perception
5. Motion blur