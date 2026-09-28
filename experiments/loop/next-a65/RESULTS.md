# A65 — crop geometry experiment completed

50 official Validation pages, 1,092 valid TextRegions and 15,010 valid line
polygons. SHA256 matches A58 for all 50 source XML. No Test page, image or
transcription value opened. Four synthetic checks pass; no inference simulated.

| Mask | Lines losing >1% annotation area | >5% | Area-weighted loss |
|---|---:|---:|---:|
| Parent polygon | 4,069 | 1,063 | 1.3665% |
| Parent rectangle | 2,222 | 703 | 0.7803% |
| Union of all text polygons | 4,061 | 1,042 | 1.3237% |

Negative result: simply ignoring the parent class and merging all text masks
hardly removes the discrepancy. Most is not rescued by other text polygons;
therefore semantic-border fragmentation is not established as the main cause
here. Rectangles preserve more annotation area but are not a free solution:
105/1,092 regions capture foreign polygon area exceeding 1% of their rectangle.
153/1,092 parent polygons have IoU below .80 with their own enclosing rectangle
(mean .92921). This is a representation comparison, not detector accuracy.

Quarantined without repair: 3 invalid parent regions, their 2 child lines,
and 12 other invalid line polygons. These remain reported, not silently removed
from claims about all lines. Total source line inventory: 15,024.

Cost: 6.842 seconds CPU, Shapely 2.1.2; zero model forwards. Shapely and NumPy
installed only in an isolated local venv. No heavy detector installed.

Decision: do not mask OCR input at fine role boundaries by default. Retain
native image context and assign roles after line detection, but this remains a
candidate architecture, not a validated improvement. Next benchmark must use
actual predicted regions/images and measure neighbouring text intrusion as
well as coverage. Area outside annotation is not missing ink or CER; imperfect
line polygons and differing margin conventions may explain part of the effect.
All seven global scientific gates remain false.

Publication policy: continue codex/autonomous-research-a34 after every commit;
never merge or update main/master. Claude unchanged at 76056c5 before A65.
