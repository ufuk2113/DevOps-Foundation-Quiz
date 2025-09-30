import json
import random
import tkinter as tk
from tkinter import messagebox

# ----------------------------
# 1️⃣ Fragen aus JSON laden
# ----------------------------
with open("fragen.json", "r", encoding="utf-8") as f:
    questions = json.load(f)

# Fragen mischen
random.shuffle(questions)

# ----------------------------
# 2️⃣ Startdialog: Name & Anzahl Fragen
# ----------------------------
class StartDialog(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("DevOps Quiz Start")
        self.geometry("400x200")
        self.user_name = tk.StringVar()
        self.num_questions = tk.IntVar(value=10)

        tk.Label(self, text="Name:").pack(pady=5)
        tk.Entry(self, textvariable=self.user_name).pack()

        tk.Label(self, text="Anzahl Fragen:").pack(pady=5)
        tk.Entry(self, textvariable=self.num_questions).pack()

        tk.Button(self, text="Quiz starten", command=self.start_quiz).pack(pady=10)

    def start_quiz(self):
        name = self.user_name.get().strip()
        num_q = self.num_questions.get()
        if not name:
            messagebox.showwarning("Fehler", "Bitte Namen eingeben!")
            return
        if num_q < 1 or num_q > len(questions):
            messagebox.showwarning("Fehler", f"Bitte Zahl zwischen 1 und {len(questions)} eingeben!")
            return
        self.destroy()
        QuizWindow(name, num_q)

# ----------------------------
# 3️⃣ Quizfenster
# ----------------------------
class QuizWindow(tk.Tk):
    def __init__(self, user_name, num_questions):
        super().__init__()
        self.title("DevOps Quiz")
        self.geometry("600x400")

        self.user_name = user_name
        self.num_questions = num_questions
        self.current_index = 0
        self.score = 0

        self.quiz_questions = questions[:num_questions]

        self.question_var = tk.StringVar()
        self.option_var = tk.StringVar()

        self.create_widgets()
        self.show_question()

    def create_widgets(self):
        tk.Label(self, textvariable=self.question_var, wraplength=550, font=("Arial", 14)).pack(pady=20)
        self.radio_buttons = []
        for i in range(4):
            rb = tk.Radiobutton(self, text="", variable=self.option_var, value="", font=("Arial", 12))
            rb.pack(anchor="w")
            self.radio_buttons.append(rb)
        tk.Button(self, text="Antwort prüfen", command=self.check_answer).pack(pady=20)

    def show_question(self):
        if self.current_index >= self.num_questions:
            self.show_result()
            return
        q = self.quiz_questions[self.current_index]
        self.question_var.set(f"{self.current_index+1}. {q['question']}")
        self.option_var.set(None)
        for i, opt in enumerate(q["options"]):
            self.radio_buttons[i].config(text=opt, value=opt)

    # ----------------------------
    # 4️⃣ Antwort prüfen
    # ----------------------------
    def check_answer(self):
        selected = self.option_var.get()
        if not selected:
            messagebox.showwarning("Fehler", "Bitte eine Antwort auswählen!")
            return
        q = self.quiz_questions[self.current_index]
        if selected == q["answer"]:
            self.score += 1
            messagebox.showinfo("Richtig!", "Richtig!")
        else:
            messagebox.showinfo("Falsch!", f"Falsch! Richtige Antwort: {q['answer']}")
        self.current_index += 1
        self.show_question()

    def show_result(self):
        messagebox.showinfo("Ergebnis", f"{self.user_name}, deine Punktzahl: {self.score}/{self.num_questions}")
        self.destroy()


# ----------------------------
# 0️⃣ Programm starten
# ----------------------------
if __name__ == "__main__":
    start_dialog = StartDialog()
    start_dialog.mainloop()
