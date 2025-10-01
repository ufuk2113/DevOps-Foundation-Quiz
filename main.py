import tkinter as tk
from tkinter import messagebox
import json
import random
import csv
from datetime import datetime
import os
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# ==========================================================
# STEP 1: Fragen laden
# ==========================================================
with open("fragen.json", "r", encoding="utf-8") as f:
    questions = json.load(f)

# Tracking-Datei für STEP 9 (keine Wiederholungen)
asked_file = "asked_questions.json"
if os.path.exists(asked_file):
    with open(asked_file, "r", encoding="utf-8") as f:
        asked_ids = json.load(f)
else:
    asked_ids = []


# ==========================================================
# STEP 2: StartDialog (Name + Anzahl Fragen)
# ==========================================================
class StartDialog(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Quiz Start")
        self.geometry("400x200")

        tk.Label(self, text="Bitte Namen eingeben:").pack(pady=5)
        self.name_entry = tk.Entry(self)
        self.name_entry.pack(pady=5)

        tk.Label(self, text="Anzahl Fragen:").pack(pady=5)
        self.num_entry = tk.Entry(self)
        self.num_entry.insert(0, "10")
        self.num_entry.pack(pady=5)

        tk.Button(self, text="Quiz starten", command=self.start_quiz).pack(pady=10)

    def start_quiz(self):
        name = self.name_entry.get().strip()
        try:
            num_questions = int(self.num_entry.get().strip())
        except:
            messagebox.showerror("Fehler", "Bitte eine Zahl eingeben!")
            return
        if not name:
            messagebox.showerror("Fehler", "Bitte Namen eingeben!")
            return
        self.destroy()
        QuizWindow(name, num_questions)


# ==========================================================
# STEP 3–9: QuizWindow
# ==========================================================
class QuizWindow(tk.Tk):
    def __init__(self, user_name, num_questions):
        super().__init__()
        self.title("DevOps Foundation Quiz")
        self.geometry("600x400")
        self.user_name = user_name
        self.num_questions = num_questions
        self.current_index = 0
        self.score = 0
        self.quiz_questions = self.get_questions(num_questions)

        # Variablen
        self.question_var = tk.StringVar()
        self.option_var = tk.StringVar()

        # GUI Setup
        tk.Label(self, textvariable=self.question_var, wraplength=500, justify="left").pack(pady=20)
        self.radio_buttons = []
        for i in range(4):
            rb = tk.Radiobutton(self, text="", variable=self.option_var, value="", wraplength=500, justify="left")
            rb.pack(anchor="w")
            self.radio_buttons.append(rb)

        tk.Button(self, text="Antwort bestätigen", command=self.check_answer).pack(pady=20)

        self.show_question()

    # ======================================================
    # STEP 9: Fragen ohne Wiederholung
    # ======================================================
    def get_questions(self, num_questions):
        global asked_ids
        new_questions = [q for q in questions if q['question'] not in asked_ids]
        if len(new_questions) < num_questions:  # Reset falls Pool leer
            asked_ids = []
            new_questions = questions.copy()

        random.shuffle(new_questions)
        selected = new_questions[:num_questions]
        return selected

    # ======================================================
    # STEP 5: Kategorieanzeige integriert
    # ======================================================
    def show_question(self):
        if self.current_index >= self.num_questions:
            self.show_result()
            return
        q = self.quiz_questions[self.current_index]
        self.question_var.set(f"{self.current_index+1}. [{q['category']}] {q['question']}")
        self.option_var.set(None)
        for i, opt in enumerate(q["options"]):
            self.radio_buttons[i].config(text=opt, value=opt)

    # ======================================================
    # STEP 4: Antwort prüfen
    # ======================================================
    def check_answer(self):
        selected = self.option_var.get()
        q = self.quiz_questions[self.current_index]
        q["selected"] = selected
        if selected == q["answer"]:
            self.score += 1
        else:
            messagebox.showinfo("Falsch", f"Richtige Antwort: {q['answer']}")
        self.current_index += 1
        self.show_question()

    # ======================================================
    # STEP 6–8: Ergebnisse + Review + Export
    # ======================================================
    def show_result(self):
        percent = (self.score / self.num_questions) * 100
        messagebox.showinfo("Ergebnis", f"{self.user_name}, du hast {self.score}/{self.num_questions} Punkte erreicht ({percent:.2f}%)")

        # Save asked questions for STEP 9
        global asked_ids
        asked_ids.extend([q["question"] for q in self.quiz_questions])
        with open(asked_file, "w", encoding="utf-8") as f:
            json.dump(asked_ids, f, ensure_ascii=False, indent=2)

        self.show_review()

    def show_review(self):
        review_win = tk.Toplevel(self)
        review_win.title("Quiz Review")
        review_win.geometry("700x500")

        tk.Label(review_win, text=f"Review für {self.user_name}", font=("Arial", 14)).pack(pady=10)

        text_box = tk.Text(review_win, wrap="word")
        text_box.pack(expand=True, fill="both")

        for idx, q in enumerate(self.quiz_questions):
            text_box.insert("end", f"{idx+1}. [{q['category']}] {q['question']}\n")
            text_box.insert("end", f"  Gewählte Antwort: {q.get('selected','-')}\n")
            text_box.insert("end", f"  Richtige Antwort: {q['answer']}\n\n")

        tk.Button(review_win, text="CSV Export", command=self.export_csv).pack(side="left", padx=20, pady=10)
        tk.Button(review_win, text="PDF Export", command=self.export_pdf).pack(side="left", padx=20, pady=10)
        tk.Button(review_win, text="Neues Quiz starten", command=lambda: [review_win.destroy(), self.destroy(), StartDialog().mainloop()]).pack(side="left", padx=20, pady=10)
        tk.Button(review_win, text="Quiz beenden", command=self.quit).pack(side="right", padx=20, pady=10)

    # ======================================================
    # STEP 7: CSV Export
    # ======================================================
    def export_csv(self):
        filename = f"{self.user_name}_quiz_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        with open(filename, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["FrageNr", "Kategorie", "Frage", "Gewählte Antwort", "Richtige Antwort"])
            for idx, q in enumerate(self.quiz_questions):
                writer.writerow([
                    idx+1, q["category"], q["question"], q.get('selected','-'), q["answer"]
                ])
        messagebox.showinfo("CSV Export", f"Ergebnisse als {filename} gespeichert")

    # ======================================================
    # STEP 8: PDF Export
    # ======================================================
    def export_pdf(self):
        filename = f"{self.user_name}_quiz_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        doc = SimpleDocTemplate(filename)
        styles = getSampleStyleSheet()
        content = []

        content.append(Paragraph(f"Quiz Review für {self.user_name}", styles['Title']))
        content.append(Spacer(1, 12))

        for idx, q in enumerate(self.quiz_questions):
            content.append(Paragraph(f"{idx+1}. [{q['category']}] {q['question']}", styles['Normal']))
            content.append(Paragraph(f"Gewählte Antwort: {q.get('selected','-')}", styles['Normal']))
            content.append(Paragraph(f"Richtige Antwort: {q['answer']}", styles['Normal']))
            content.append(Spacer(1, 10))

        doc.build(content)
        messagebox.showinfo("PDF Export", f"Ergebnisse als {filename} gespeichert")


# ==========================================================
# STEP 2 Startpunkt
# ==========================================================
if __name__ == "__main__":
    StartDialog().mainloop()
