"""VoiceOrder Shop: turn a customer's voice note into an order with Meta Muse Spark.

    pip install git+https://github.com/UtsavInTech/upgrade-gate
    MODEL_API_KEY=... python app/parse_note.py audio/extract-03-hi.wav

It uses exactly the model in release/model.json and exactly the prompt in tasks/my_tasks.jsonl,
so the upgrade gate's verdict on a pull request is a verdict on this app.
"""
from __future__ import annotations

import json
import os
import re
import sys

from upgrade_gate.cli import parse_candidate
from upgrade_gate.client import ModelClient, build_messages

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROMPT = ("Listen to the attached audio. This is a customer's voice note. Reply with only a JSON object with keys "
          "order_number, pincode and city. Write order_number and pincode as digit strings and city in English.")


def shipped_model() -> str:
    with open(os.path.join(ROOT, "release", "model.json"), encoding="utf-8") as f:
        return json.load(f)["model"]


def shop_checks(order: dict) -> list:
    """The shop's usual form checks. Note: a real but wrong pincode passes them."""
    problems = []
    if not re.fullmatch(r"\d{5}", str(order.get("order_number", ""))):
        problems.append("order number must be 5 digits")
    if not re.fullmatch(r"[1-9]\d{5}", str(order.get("pincode", ""))):
        problems.append("pincode must be 6 digits")
    if not str(order.get("city", "")).strip():
        problems.append("city is missing")
    return problems


def parse_note(wav_path: str) -> dict:
    c = parse_candidate(shipped_model())
    res = ModelClient().chat(c.model_id, build_messages({"prompt": PROMPT, "attachments": [wav_path]}), c.params)
    if res.error:
        raise SystemExit("model error: %s" % res.error)
    m = re.search(r"\{.*\}", res.text or "", re.S)
    order = json.loads(m.group(0)) if m else {}
    return {"model": c.name, "order": order, "problems": shop_checks(order), "reply": res.text}


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python app/parse_note.py NOTE.wav")
    out = parse_note(sys.argv[1])
    print(json.dumps(out, indent=2, ensure_ascii=False))
    print("SAVED" if not out["problems"] else "ASK THE CUSTOMER: " + "; ".join(out["problems"]))
