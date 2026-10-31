import json, sys
Q = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "/data/workspace/prakom-quiz/today.json"))
print("count", len(Q))
for i, x in enumerate(Q, 1):
    e = len(x["explanation"])
    flag = "" if 175 <= e <= 200 else "<<<"
    print(i, "q", len(x["q"]), "opt", max(len(o) for o in x["options"]), "exp", e, "det", len(x["detail"]), "ans", x["answer"], flag)
