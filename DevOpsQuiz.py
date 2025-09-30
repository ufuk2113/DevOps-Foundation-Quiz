import json
import random

# Fragen aus JSON laden
with open("fragen.json", "r", encoding="utf-8") as f:
    questions = json.load(f)

# Fragen mischen
random.shuffle(questions)

# Einfaches Terminal-Quiz
score = 0
for q in questions[:5]:  # erst mal nur 5 Fragen zum Testen
    print(q["question"])
    for i, option in enumerate(q["options"], 1):
        print(f"{i}. {option}")
    answer = input("Deine Antwort: ")
    if q["options"][int(answer)-1] == q["answer"]:
        print("Richtig!")
        score += 1
    else:
        print(f"Falsch! Richtige Antwort: {q['answer']}")
print(f"Punktzahl: {score}/{len(questions[:5])}")
