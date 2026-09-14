from scoring.score_aggregator import calculate_final_score


score = calculate_final_score(
    correctness_score=80,
    complexity_score=90,
    style_score=70,
    originality_score=95
)


print("Final Score:", score)
print("Expected Score: 83.0")

assert score == 83.0

print("Score aggregator test successful!")