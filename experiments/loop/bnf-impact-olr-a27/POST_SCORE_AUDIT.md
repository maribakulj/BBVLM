# A27 post-score audit

Luna covered all 235 role IDs and correctly excluded the one non-editorial
region, but returned every content region as a singleton. Its stream-pair F1 is
therefore 0. This is a structural abstention, not an OLR success.

The preregistered escalation condition was met. Sol inspected the same eight
JPEG inputs with no access to the XML, private mapping, reference, evaluator, or
Luna output. The clarified prompt explicitly disallowed systematic singletons;
model and prompt therefore change together, so this is a post-hoc diagnostic,
not an independent causal model comparison.

Sol produced 34 streams for 13 PAGE OrderedGroups. Eligibility is exact. Stream
pair precision is 1.0, recall 0.4190, F1 0.5906; covered-pair order accuracy is
1.0 and end-to-end order-pair recall 0.4190. This beats the optimistic
geometry+oracle-role baseline F1 0.5052 but remains far below the 0.90 gate.

After scoring, the fragmentation pattern was inspected: every one of the 34 Sol
streams is wholly contained in one reference OrderedGroup; seven of thirteen
reference groups are recovered as one stream, while the six largest groups are
split into 2, 4, 5, 8, 6, and 2 fragments. There are no wrong cross-reference
merges on this page. This suggests a useful one-pass architecture — conservative
visual semantic streams followed by a cheap continuation merger — but A27 is
consumed and cannot validate that merger. OrderedGroup is still not explicit
article truth.

