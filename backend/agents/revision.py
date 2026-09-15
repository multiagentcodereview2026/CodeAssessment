from pydantic import BaseModel, Field
from agents.base import load_prompt, invoke_agent


class RevisionOutput(BaseModel):
    improved_code: str
    changes: list[dict] = Field(default_factory=list)
    change_summary: str
    improvement_explanation: str


async def revision_node(state):
    payload = {"source_code": state["submission"]["source_code"], "language": state["submission"]["language"], "feedback": state.get("feedback")}
    fallback = {"improved_code": payload["source_code"], "changes": [],
                "change_summary": "No AI revision available.", "improvement_explanation": "The original code is retained. No generated revision has been tested."}
    result = await invoke_agent(load_prompt("revision"), payload, RevisionOutput, fallback)
    result["verified"] = False
    return {"improved_code": result}
