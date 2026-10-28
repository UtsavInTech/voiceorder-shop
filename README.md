# VoiceOrder Shop

A small demo shop that ships a Meta Muse Spark model, set up with **[Upgrade Gate](https://github.com/UtsavInTech/upgrade-gate)**
in one command. Every pull request that changes the shipped model runs both models on the shop's own voice
notes and blocks the upgrade if the new one starts failing quietly.

## What the shop does

Customers leave a voice note in Hindi, Hinglish or English with their order number, pincode and city.
[`app/parse_note.py`](app/parse_note.py) sends it to the model in [`release/model.json`](release/model.json)
(`spark-1.2@low` today) and runs the shop's form checks before the order is saved.

The risk: a model that hears a *real but wrong* pincode passes every form check, and the parcel goes to the wrong
city. Accuracy alone can hide that.

## How the gate was set up

```sh
pip install git+https://github.com/UtsavInTech/upgrade-gate
upgrade-gate init --model spark-1.2@low --n 45 --budget 2
```

`init` wrote four files. We then did the two things it asks for:

| File | What we changed |
|---|---|
| [`release/model.json`](release/model.json) | nothing: the model the shop ships |
| [`release/policy.json`](release/policy.json) | wrote the reason (`why`): a wrong or blank pincode loses the order; "I can't hear" is fine |
| [`tasks/my_tasks.jsonl`](tasks/my_tasks.jsonl) | replaced the 3 examples with **45 voice notes** (15 orders × English, Hindi, Hinglish) with known answers, same prompt as the app |
| [`.github/workflows/upgrade-gate.yml`](.github/workflows/upgrade-gate.yml) | nothing: the pull request check (live sample, $2 cap) |

Plus one repository secret, `MODEL_API_KEY`.

## The upgrade

The pull request **"Upgrade to Muse Spark 1.3"** changes one line in `release/model.json`. The check
`upgrade-gate / my-tasks` sends all 45 notes to both models, 3 tries each (270 calls, about $0.55, capped at $2),
and reports GO, NO-GO or INCONCLUSIVE with the failing cases. The workflow summary shows the result; NO-GO fails
the check.

The voice clips are synthetic (text-to-speech), the same public clips as the Upgrade Gate study, which found
1.3 returning wrong or blank answers without warning far more often on them. This repo reruns that check fresh,
on every push, so the result is whatever the models do today.
