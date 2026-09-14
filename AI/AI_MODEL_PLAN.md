# AI Assessment Model Plan

## Objective

Develop an AI-assisted programming assessment system that
provides explainable and actionable feedback on student code.

## AI Outputs

1. Code quality assessment
2. Complexity analysis/explanation
3. Explainable feedback
4. Improvement recommendations
5. Code revision suggestions

## Non-LLM Components

Correctness will primarily be determined using:
- Compilation
- Test cases
- Runtime
- Memory
- Execution status

The LLM should not be the sole authority for correctness
or numerical scoring.

## Model Candidates

- Qwen2.5-Coder
- Microsoft CodeReviewer
- Other suitable code-specialized models

Final model will be selected after comparison.

## Fine-tuning

Use LoRA/QLoRA if practical.

## Baselines

1. Pretrained model without fine-tuning
2. Fine-tuned model
3. Potentially a conventional/LLM baseline

## Evaluation

Evaluate:
- Assessment quality
- Agreement with expert/TA labels
- Feedback quality
- Recommendation quality
- Score prediction error where applicable