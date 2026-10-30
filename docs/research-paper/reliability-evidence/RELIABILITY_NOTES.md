# Complexity reliability follow-up

Source commit: `752c0d0`.

The Python diagnostic mixed traversal of a collection with `range(len(a))`.
The old dimension extraction treated these as independent dimensions. A narrow
AST supplement now relates supported traversal forms and stable size aliases to
their source collection. Independent collections retain separate dimensions.

An additional substring check for `l += 1` also matched `total += 1`. Exact
identifier matching fixes the resulting false amortized-loop classification.

Selected opaque iteration/call costs, collection mutation, shadowed builtins,
and rebound bounds produce REVIEW_REQUIRED with structural-review-blocked.
Runtime or model agreement cannot override this block. Missing weighted
complexity evidence keeps the final total incomplete under the existing rubric.
This does not establish soundness for arbitrary student programs.

Validation: 359 backend tests passed, including 23 added regressions. Nine
frontend rendering checks, lint, and production build passed. Tests use isolated
fixtures and do not reset the application database.

pilot-after-fix.json records a rerun of the published 20 synthetic snippets with
optional model review disabled. Time, space and joint proposal agreement are
20/20 after repair. The baseline remains 19/20 joint at d4cdb86. The repair used
the known diagnostic: these counts are not held-out accuracy or human validation.
