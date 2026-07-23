# Evaluating Visual Brief Retrieval

An automated visual ordering can look plausible while failing at the top of the
list. Evaluate the exact retrieval objective before treating a score as useful.

## Label The Target Directly

Create a small, consented benchmark with human labels for the actual visual
brief:

- positive: a clear match
- negative: a clear non-match
- uncertain: evidence is insufficient
- hard negative: superficially similar but wrong for an important reason

Administrative or eligibility facts must come from verified metadata. Do not
infer them from an image.

## Separate Fit From Measurement Reliability

Visual fit and image reliability are different quantities.

Fit may describe task-relevant visible geometry or presentation. Reliability
should describe whether the image supports those measurements:

- face size and crop
- pose
- occlusion
- eye visibility
- blur and exposure

Low reliability should lower confidence or trigger abstention. It should not be
interpreted as a poor visual fit.

## Use Retrieval Metrics

For a ranked review workflow, report metrics that reflect the reviewer
experience:

- `precision@K`: relevant results among the first `K`
- `recall@K`: benchmark positives recovered in the first `K`
- abstention coverage: rows withheld because evidence was weak
- inter-rater agreement: how consistently reviewers apply the brief
- cross-photo stability: whether the same record changes substantially across
  comparable images

Declare `K` and the acceptance threshold before evaluating the holdout set.
Generic classification accuracy and unrelated attribute buckets are not
substitutes for retrieval quality.

## Prevent Calibration Leakage

Use separate groups for:

1. brief writing and label calibration
2. score or threshold tuning
3. final holdout evaluation

Do not repeatedly tune on the same top results and then report them as an
independent benchmark.

## Keep The Human Review Surface Honest

A useful export should include:

- the fit score
- measurement reliability
- component scores or descriptors
- model and score versions
- review reasons
- an explicit human-review flag

Preserve `null` when a backend lacks evidence. A complete-looking score is
worse than an honest abstention.

## Data-Minimizing Defaults

- Process locally unless consent explicitly permits remote review.
- Persist aggregate measurements instead of raw landmarks when possible.
- Do not persist identity embeddings for visual-brief evaluation.
- Keep source images, reports, and benchmark labels out of the public
  repository.
- Record enough model and configuration metadata to reproduce the evaluation.

## Release Gate

Do not enable automated ordering merely because sample outputs look reasonable.
Release only after the predeclared top-of-list metric passes on a holdout set
and reviewers can inspect the evidence behind every score.
