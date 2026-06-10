import json
import csv

with open("results.json") as f:
    results = json.load(f)

labeled = []

for i, r in enumerate(results):
    print(f"\n{'='*60}")
    print(f"[{i+1}/{len(results)}] {r['question']}")
    print(f"Category: {r['category']} / {r['type']}")
    print(f"\nAgent response:\n{r['output']}")
    print()

    while True:
        label = input("Label (g=good, b=bad, s=skip): ").strip().lower()
        if label in ("g", "b", "s"):
            break

    if label == "s":
        continue

    reason = ""
    if label == "b":
        reason = input("Failure reason (hallucination / wrong-answer / wrong-scope / failed-to-query): ").strip()

    labeled.append({
        "question": r["question"],
        "category": r["category"],
        "type": r["type"],
        "label": "good" if label == "g" else "bad",
        "failure_reason": reason,
        "output": r["output"],
    })
    print(f"  Saved as {'GOOD' if label == 'g' else 'BAD'}")

with open("labels.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["question", "category", "type", "label", "failure_reason", "output"])
    writer.writeheader()
    writer.writerows(labeled)

total = len(labeled)
bad = sum(1 for r in labeled if r["label"] == "bad")
print(f"\nDone. {bad}/{total} bad. Saved to labels.csv")
