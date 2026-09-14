from schemas import StyleResult
from scoring.style_scorer import calculate_style_score


result = StyleResult(
    overall_score=55,
    readability_score=70,
    naming_score=50,
    maintainability_score=70,
    documentation_score=30,
    issues=[],
    suggestions=[],
    explanation="Test style result",
    confidence=0.9
)


score = calculate_style_score(result)


print("Style Score:", score)
print("Expected Score: 59.0")

assert score == 59.0

print("Style scorer test successful!")