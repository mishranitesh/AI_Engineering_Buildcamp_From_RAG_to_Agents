import json
import csv

# Load judge labels from results_judged.json
with open("results_judged.json") as f:
    judged = json.load(f)

# Load human labels from labels.csv
human_labels = {}
with open("labels.csv") as f:
    for row in csv.DictReader(f):
        human_labels[row["question"]] = row["label"]

tp = fp = fn = tn = 0
mismatches = []

for r in judged:
    q = r["question"]
    judge = r["judge_label"]
    human = human_labels.get(q, "good")  # default good if skipped

    if judge == "bad" and human == "bad":
        tp += 1
    elif judge == "bad" and human == "good":
        fp += 1
        mismatches.append(("FP", q, judge, human))
    elif judge == "good" and human == "bad":
        fn += 1
        mismatches.append(("FN", q, judge, human))
    else:
        tn += 1

total = tp + fp + fn + tn
accuracy  = (tp + tn) / total
precision = tp / (tp + fp)
recall    = tp / (tp + fn)

print(f"TP={tp}  FP={fp}  FN={fn}  TN={tn}  Total={total}")
print(f"Accuracy:  {accuracy:.2%}")
print(f"Precision: {precision:.2%}")
print(f"Recall:    {recall:.2%}")
print("\nMismatches:")
for m in mismatches:
    print(f"  {m[0]}: '{m[1]}' | judge={m[2]}, human={m[3]}")
