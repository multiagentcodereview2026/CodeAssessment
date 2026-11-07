from agents.revision import ExpectedComplexity


def test_new_guidance_uses_auxiliary_space_convention():
    assert ExpectedComplexity().space_definition == "auxiliary"


def test_saved_total_space_guidance_remains_readable():
    assert ExpectedComplexity(space_definition="total").space_definition == "total"
