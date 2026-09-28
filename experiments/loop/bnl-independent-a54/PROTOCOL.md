# A54 protocol — fresh image-plus-candidate correction

The 16 block IDs in `split.json` were frozen from identifiers alone, with all
A45 IDs excluded, before opening any selected XML or PNG. Membership is never
changed after language or content inspection.

The experiment first runs unchanged PERO 0.7.0 and the frozen A37 vertical-box
router. The reference XML remains closed while the candidate text and opaque
VLM request are sealed. One blind Luna pass then sees each block image and its
PERO text candidate. It may return the candidate unchanged or make localized,
visually grounded corrections; it must separately mark uncertainty. The pass
does not see the BnL XML, reference text, scores, prior BnL responses, or other
models.

Evaluation opens the immutable provider XML only after both outputs are sealed.
Strict NFC, search-normalized and punctuation-free lexical CER stay separate.
The primary non-regression gate requires lower aggregate `search_v1` CER and
zero regression among blocks where PERO was already exact in that view. The
same rule is reported for `lexical_alnum`. These gates were declared before
scoring. Passing would support the correction design only; it would not prove
perfect OCR because the provider itself states a nonzero reference-error
ceiling and the sample contains blocks rather than complete pages.
