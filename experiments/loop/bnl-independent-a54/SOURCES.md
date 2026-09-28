# A54 sources

- Bibliothèque nationale du Luxembourg, historical-newspaper raw ground truth,
  read 2026-09-28. The provider describes 1,702 uncropped blocks, ALTO pairs,
  multilingual content, CC0 licensing, and double-keyed transcription at a
  declared minimum 99.95% accuracy. The declaration is strong but is not a
  claim of mathematical perfection. <https://data.bnl.lu/data/historical-newspapers/>
- Yao et al., *Reading Between the Lines: Abstaining from VLM-Generated OCR
  Errors via Latent Representation Probes*, arXiv:2511.19806, full 13-page
  paper read 2026-09-28. It finds prompted self-abstention and verbalized
  confidence poorly calibrated for OCR, while lightweight probes over
  intermediate hidden states improve abstention accuracy in open VLMs. A54
  cannot access proprietary-agent latent states, so it treats Luna uncertainty
  only as diagnostic and measures an external non-regression gate instead.
- Greif, Griesshaber and Greif, *Multimodal LLMs for OCR, OCR Post-Correction,
  and Named Entity Recognition in Historical Documents*, arXiv:2504.00414,
  full paper read in A53. Its image-plus-independent-OCR condition motivates
  the single-pass input; it does not justify trusting self-confidence.
