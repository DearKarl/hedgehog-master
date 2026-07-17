# Evidence-Grounded Scientific Presentation Pipelines

## Abstract

The proposed pipeline improves evidence traceability by 18% while reducing manual review time by 24 ms per claim. The architecture separates document extraction, claim verification, semantic planning, deterministic diagram compilation, and PowerPoint export. This separation makes the generated figures reproducible and keeps every substantive statement linked to a precise source locator.

## Method

The evidence score is defined as $S = \frac{v}{n}$, where $v$ is the number of verified statements and $n$ is the number of substantive statements. The system evaluates each extracted sentence against a source page before assigning verified status. Formula assets and external image prompts remain registered in project-local manifests.

## Results

The evaluation demonstrates that deterministic layout produces byte-stable SVG across repeated runs. The structured claim registry also reduces unsupported statements by 31% in the controlled research-deck benchmark.

## References

1. Example Author. A sufficiently detailed reference entry for testing evidence extraction and bibliography registration. 2026.
