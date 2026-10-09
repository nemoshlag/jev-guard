"""Stand-in for a System One server (Jev/Kev) so the demo runs with no model or GPU.

It uses a crude keyword heuristic and exists ONLY to show the request/response flow.
For real classification run Kev (`docker compose --profile local-model up`) or use hosted Jev.
"""

import re

from fastapi import FastAPI

app = FastAPI()

HINTS = re.compile(r"\b(my name is|lives at|her name|his name|date of birth|born on)\b", re.I)


@app.post("/v1/systemone")
def systemone(body: dict) -> dict:
    p = 0.94 if HINTS.search(str(body["state"])) else 0.04
    return {
        "model": body["model"],
        "answers": {q: {"type": "noul", "noul": p} for q in body["questions"]},
    }
