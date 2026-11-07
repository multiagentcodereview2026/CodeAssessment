# Core-method complexity contract

The submission and private candidate paths share analyze_static_complexity
and analyze_submission_complexity.

- Time covers the algorithm and reachable helpers.
- Space is auxiliary: input and required output storage are excluded.
- Scratch buffers, copies, recursion and library workspace remain included.
- Judge runtime and measured process memory still describe the whole program.
  They are not core-method growth measurements.
- Source slicing is for analysis only. Original code goes to the judge.
- Ambiguous entry points, overloaded methods, unsupported bulk-input wrappers,
  parser failures and mixed I/O/calculation request hybrid review.
- AI receives code and the same scope convention, without private targets.
- A saved assessment is not rewritten. Projection's existing baseline check
  requests a new assessment when current analysis differs from saved evidence.

This change does not migrate or certify any problem-bank target. Dataset label
verification remains a separate task. Exact analysis of arbitrary programs is
not claimed; unsupported cases must remain reviewable.
