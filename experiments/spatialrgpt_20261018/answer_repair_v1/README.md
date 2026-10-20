# Seven-question answer-format repair (2026-10-20)

The user authorized re-running the seven invalid final answers and checking all
749 results. The 742 previously valid answers remain unchanged. This is a
separately disclosed repair protocol, not a claim of an unchanged original run.

Only the final answer requests are issued again. Original user question content,
images (including generated views), model, provider, decoding settings and SVC
artifacts are preserved. A system-format clarification requests physical length
in meters, and the submitted answer schema is tightened to a non-negative decimal
followed by `m`. Ground truth is not read by the repair program. The first valid
response is accepted, without selecting by score. No GPU/search/worker code is
imported and no videos are regenerated.

Each new payload has a separate immutable audit directory with a start marker,
raw response and transport/usage receipt for each attempt. Eight attempts is the
maximum for each new payload; all 56 old failed responses and all historical
costs remain recorded. Transport or model/provider failures stop for inspection.
No original result or final receipt is overwritten.

The independent verifier `verify_v3.py` re-audits all 749 historical sources, checks old item
hashes, image correspondence, exact request changes, model/provider/reasoning,
attempt completeness and first-valid acceptance, and strictly parses all final
answers (including finite numeric values). It then uses the pinned WorldLoop
scorer offline and sums unique historical plus new attempt receipts. Validity
means format and provenance are accepted; it does not imply a correct answer.

The original result is archived at `results/spatialrgpt-deepseek-20261020.md`.
Only code, settings, hashes and aggregate results are public. All requests,
responses, questions, labels, images and videos remain private on DAAI.

The initial verifier stopped on the six preflight items because it used the full-run image directory. V2 selects each item’s original preflight/full source, also requiring identical question and image hashes. Original failure evidence remains private; this correction made zero API/GPU calls.

V3 also loads and checks the original frozen recovery baseline so the one previously authorized ninth transport attempt retains its narrow exception; every other original payload still has an eight-attempt limit. The relevant historical item passed a separate offline check. Repeated file hashes are cached only while device, inode, size, modification time and change time stay unchanged. Cache invalidation tests passed. V1/V2 failure evidence is retained privately; no successful repair request was reissued.
