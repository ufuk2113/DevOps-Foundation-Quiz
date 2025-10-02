import json
import random
import tkinter as tk
from tkinter import messagebox, ttk
import csv
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
import matplotlib.pyplot as plt
import io
import os

# ------------------- Model -------------------
class QuizModel:
    def __init__(self, questions_file="fragen.json", used_file="used_questions.json"):
        self.questions_file = questions_file
        self.used_file = used_file
        self.questions_data = self.load_questions()
        self.used_questions = self.load_used_questions()
        self.review_list = []
        self.score = 0
        self.current_question_index = 0
        self.quiz_size = 0
        self.diagramm_typ = "bar"

    def load_questions(self):
        try:
            with open(self.questions_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            messagebox.showerror("Fehler", f"Datei '{self.questions_file}' nicht gefunden!")
            exit()

    def load_used_questions(self):
        if os.path.exists(self.used_file):
            with open(self.used_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def save_used_questions(self):
        with open(self.used_file, "w", encoding="utf-8") as f:
            json.dump(self.used_questions, f, ensure_ascii=False, indent=4)

    def select_questions(self, quiz_size, no_repeat=True):
        self.quiz_size = quiz_size
        if no_repeat:
            available_questions = [q for q in self.questions_data if q['question'] not in self.used_questions]
            if len(available_questions) < quiz_size:
                available_questions = self.questions_data
                self.used_questions = []
            selected = random.sample(available_questions, quiz_size)
            self.used_questions.extend([q['question'] for q in selected])
            self.save_used_questions()
        else:
            selected = random.sample(self.questions_data, quiz_size)
        self.current_question_index = 0
        self.review_list.clear()
        self.score = 0
        return selected

    def record_review(self, question, selected_answers, is_correct):
        correct_answers = question['answer']
        if not isinstance(correct_answers, list):
            correct_answers = [correct_answers]
        self.review_list.append({
            "question": question['question'],
            "category": question['category'],
            "selected": selected_answers,
            "correct": correct_answers,
            "is_correct": is_correct
        })
        if is_correct:
            self.score += 1

# ------------------- View -------------------
class StartView(tk.Tk):
    def __init__(self, start_callback, questions_count):
        super().__init__()
        self.start_callback = start_callback
        self.questions_count = questions_count
        self.title("Quiz starten")
        self.geometry("400x400")
        self.resizable(False, False)
        self.create_widgets()

    def create_widgets(self):
        tk.Label(self, text="Name / Kürzel:", font=("Arial", 12)).pack(pady=5)
        self.name_entry = tk.Entry(self, font=("Arial", 12))
        self.name_entry.pack(pady=5)

        tk.Label(self, text="Anzahl der Fragen:", font=("Arial", 12)).pack(pady=5)
        self.num_questions = tk.IntVar(value=min(50, self.questions_count))
        tk.Spinbox(self, from_=10, to=self.questions_count, increment=10,
                   textvariable=self.num_questions, font=("Arial", 12)).pack(pady=5)

        self.no_repeat_var = tk.BooleanVar(value=True)
        tk.Checkbutton(self, text=f"Fragen nicht wiederholen bis alle {self.questions_count} durchlaufen sind",
                       variable=self.no_repeat_var, font=("Arial", 11)).pack(pady=10)

        tk.Label(self, text="Diagrammtyp für PDF:", font=("Arial", 12)).pack(pady=5)
        self.diagramm_var = tk.StringVar(value="bar")
        tk.Radiobutton(self, text="Balkendiagramm", variable=self.diagramm_var, value="bar",
                       font=("Arial", 11)).pack()
        tk.Radiobutton(self, text="Kreisdiagramm", variable=self.diagramm_var, value="pie",
                       font=("Arial", 11)).pack()

        tk.Button(self, text="Quiz starten", font=("Arial", 12, "bold"),
                  bg="#4CAF50", fg="white", activebackground="#45a049",
                  command=self.start_quiz).pack(pady=10)

    def start_quiz(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("Fehler", "Bitte einen Namen eingeben!")
            return
        self.destroy()
        self.start_callback(
            user_name=name,
            quiz_size=self.num_questions.get(),
            no_repeat=self.no_repeat_var.get(),
            diagramm_typ=self.diagramm_var.get()
        )

class QuizView(tk.Tk):
    def __init__(self, presenter):
        super().__init__()
        self.presenter = presenter
        self.title("DevOps Foundation Quiz")
        self.geometry("950x700")
        self.configure(bg="#f0f4f7")
        self.resizable(False, False)
        self.create_widgets()

    def create_widgets(self):
        self.top_frame = tk.Frame(self, bg="#d1e3f0", padx=20, pady=10)
        self.top_frame.pack(fill="x")
        self.question_frame = tk.Frame(self, bg="#ffffff", padx=20, pady=20, relief="groove", bd=2)
        self.question_frame.pack(pady=15, fill="x", padx=20)
        self.options_frame = tk.Frame(self, bg="#f7f9fb", padx=20, pady=10, relief="ridge", bd=2)
        self.options_frame.pack(pady=10, fill="x", padx=20)
        self.bottom_frame = tk.Frame(self, bg="#d1e3f0", padx=20, pady=10)
        self.bottom_frame.pack(fill="x", pady=10)

        self.progress_label = tk.Label(self.top_frame, text="", font=("Helvetica", 12, "bold"), bg="#d1e3f0")
        self.progress_label.pack(side="left")
        self.timer_label = tk.Label(self.top_frame, text="", font=("Helvetica", 12, "bold"), fg="red", bg="#d1e3f0")
        self.timer_label.pack(side="right")
        self.score_label = tk.Label(self.bottom_frame, text="Punkte: 0", font=("Helvetica", 12, "bold"), bg="#d1e3f0")
        self.score_label.pack(side="left")
        self.progress_bar = ttk.Progressbar(self.bottom_frame, length=500, mode="determinate")
        self.progress_bar.pack(side="right", padx=10)

        self.question_label = tk.Label(self.question_frame, text="", wraplength=900, font=("Helvetica", 16),
                                       justify="left", bg="#ffffff")
        self.question_label.pack()
        self.category_label = tk.Label(self.question_frame, text="", font=("Helvetica", 12, "italic"),
                                       fg="gray", bg="#ffffff")
        self.category_label.pack(pady=5)

        self.submit_btn = tk.Button(self, text="Antwort bestätigen", font=("Helvetica", 14, "bold"),
                                    bg="#4CAF50", fg="white", activebackground="#45a049",
                                    command=self.presenter.check_answer)
        self.submit_btn.pack(pady=10)

    def show_question(self, question_text, category, options):
        self.question_label.config(text=question_text)
        self.category_label.config(text=f"Kategorie: {category}")

        for widget in self.options_frame.winfo_children():
            widget.destroy()

        self.option_vars = []
        for opt in options:
            var = tk.IntVar()
            cb = tk.Checkbutton(self.options_frame, text=opt, variable=var,
                                font=("Helvetica", 14), wraplength=900, justify="left",
                                bg="#f7f9fb", activebackground="#e0f0ff")
            cb.var = var
            cb.pack(fill="x", pady=5)
            self.option_vars.append(cb)

    def get_selected_options(self):
        return [cb.cget("text") for cb in self.option_vars if cb.var.get() == 1]

    def update_score_progress(self, score, current_index, total_questions):
        self.score_label.config(text=f"Punkte: {score}/{total_questions}")
        self.progress_label.config(text=f"Frage {current_index + 1} von {total_questions}")
        self.progress_bar['value'] = (current_index / total_questions) * 100

    def highlight_answers(self, selected, correct):
        for cb in self.option_vars:
            text = cb.cget("text")
            cb.config(state="disabled")
            if text in correct:
                cb.config(bg="#4CAF50", fg="white")
            elif text in selected and text not in correct:
                cb.config(bg="#f44336", fg="white")

# ------------------- Presenter -------------------
class QuizPresenter:
    def __init__(self, model, user_name, quiz_size, no_repeat, diagramm_typ):
        self.model = model
        self.user_name = user_name
        self.quiz_size = quiz_size
        self.no_repeat = no_repeat
        self.model.diagramm_typ = diagramm_typ
        self.view = QuizView(self)
        self.questions = self.model.select_questions(quiz_size, no_repeat)
        self.time_left = 60
        self.timer_id = None
        self.load_question()
        self.view.mainloop()
    
    #Zeigt verbleibende Zeit an, zählt jede Sekunde runter. 
    #Wenn Zeit 0 erreicht → Frage als falsch markieren, richtige Antwort anzeigen, next_question() aufrufen.   
    def update_timer(self):
        if self.time_left > 0:
            self.view.timer_label.config(text=f"Verbleibende Zeit: {self.time_left} Sekunden")
            self.time_left -= 1
            self.timer_id = self.view.after(1000, self.update_timer)
        else:
            question = self.questions[self.model.current_question_index]
            messagebox.showinfo("Zeit abgelaufen!", f"Die Zeit ist abgelaufen.\nRichtige Antwort: {question['answer']}")
            self.model.record_review(question, [], False)
            self.next_question()
            
            
    def next_question(self):
        self.model.current_question_index += 1
        self.load_question()
    
    def load_question(self):
        if self.model.current_question_index >= len(self.questions):
            self.export_results()
            self.show_review()
            return
        q = self.questions[self.model.current_question_index]
        self.view.show_question(q['question'], q['category'], q['options'])
        self.view.update_score_progress(self.model.score, self.model.current_question_index, self.quiz_size)
        # Timer starten
        self.time_left = 60
        if self.timer_id:
            self.view.after_cancel(self.timer_id)
        self.update_timer()
        
        
    def check_answer(self):
        selected = self.view.get_selected_options()
        if not selected:
            messagebox.showwarning("Keine Auswahl", "Bitte wähle mindestens eine Antwort!")
            return

        question = self.questions[self.model.current_question_index]
        correct_answers = question['answer']
        if not isinstance(correct_answers, list):
            correct_answers = [correct_answers]

        is_correct = set(selected) == set(correct_answers)
        self.model.record_review(question, selected, is_correct)
        self.view.highlight_answers(selected, correct_answers)
        self.model.current_question_index += 1
        self.view.after(1500, self.load_question)

    def export_results(self):
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        name_clean = self.user_name.replace(" ", "_")
        csv_filename = f"Ergebnisse_{name_clean}_{now}.csv"
        pdf_filename = f"Ergebnisse_{name_clean}_{now}.pdf"

        percent = round((self.model.score / self.quiz_size) * 100, 2)
        passed = self.model.score >= int(self.quiz_size * 0.65)
        result_text = "✅ Bestanden" if passed else "❌ Nicht bestanden"

        # CSV
        with open(csv_filename, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Frage", "Kategorie", "Deine Antwort", "Richtige Antwort", "Status"])
            for item in self.model.review_list:
                writer.writerow([
                    item['question'], item['category'],
                    ", ".join(item['selected']), ", ".join(item['correct']),
                    "Richtig" if item['is_correct'] else "Falsch"
                ])
            writer.writerow([])
            writer.writerow(["Gesamtpunktzahl", f"{self.model.score}/{self.quiz_size} ({percent}%)"])
            writer.writerow(["Ergebnis", result_text])
        print(f"CSV gespeichert: {csv_filename}")

        # Diagramm
        correct_count = self.model.score
        wrong_count = self.quiz_size - self.model.score
        fig, ax = plt.subplots(figsize=(4, 3))
        if self.model.diagramm_typ == "bar":
            ax.bar(["Richtig", "Falsch"], [correct_count, wrong_count], color=["green", "red"])
            ax.set_ylabel("Anzahl Fragen")
            ax.set_title("Ergebnisübersicht")
        else:
            ax.pie([correct_count, wrong_count], labels=["Richtig", "Falsch"], colors=["green", "red"],
                   autopct="%1.1f%%", startangle=90)
            ax.set_title("Ergebnisübersicht")
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format="png")
        plt.close(fig)
        img_buffer.seek(0)

        # PDF
        styles = getSampleStyleSheet()
        doc = SimpleDocTemplate(pdf_filename, pagesize=A4)
        elements = []
        elements.append(Paragraph("DevOps Foundation Prüfungsergebnisse", styles['Title']))
        elements.append(Spacer(1, 12))
        elements.append(Paragraph(f"Teilnehmer: {self.user_name}", styles['Heading2']))
        elements.append(Paragraph(f"Gesamtpunktzahl: {self.model.score}/{self.quiz_size} ({percent}%)", styles['Heading2']))
        elements.append(Paragraph(f"Ergebnis: {result_text}", styles['Heading2']))
        elements.append(Spacer(1, 12))
        elements.append(Image(img_buffer, width=300, height=220))
        elements.append(Spacer(1, 20))
        for idx, item in enumerate(self.model.review_list, 1):
            status = "✅ Richtig" if item['is_correct'] else "❌ Falsch"
            q_text = f"<b>Frage {idx}:</b> {item['question']}<br/>" \
                     f"<b>Kategorie:</b> {item['category']}<br/>" \
                     f"<b>Deine Antwort:</b> {', '.join(item['selected'])}<br/>" \
                     f"<b>Richtige Antwort:</b> {', '.join(item['correct'])}<br/>" \
                     f"<b>Status:</b> {status}<br/><br/>"
            elements.append(Paragraph(q_text, styles['Normal']))
            elements.append(Spacer(1, 6))
        doc.build(elements)
        print(f"PDF gespeichert: {pdf_filename}")

    def show_review(self):
        review_root = tk.Toplevel()
        review_root.title("Prüfungsübersicht")
        review_root.geometry("950x600")
        review_root.configure(bg="#f0f4f7")

        percent = round((self.model.score / self.quiz_size) * 100, 2)
        passed = self.model.score >= int(self.quiz_size * 0.65)
        result_text = "✅ Bestanden" if passed else "❌ Nicht bestanden"

        tk.Label(review_root, text=f"Quiz beendet! Punktzahl: {self.model.score}/{self.quiz_size} ({percent}%)",
                 font=("Helvetica", 16, "bold"), bg="#f0f4f7").pack(pady=10)
        tk.Label(review_root, text=f"Ergebnis: {result_text}",
                 font=("Helvetica", 14, "bold"), bg="#f0f4f7",
                 fg="green" if passed else "red").pack(pady=5)

        canvas = tk.Canvas(review_root, bg="#f0f4f7")
        scrollbar = tk.Scrollbar(review_root, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg="#f0f4f7")
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for idx, item in enumerate(self.model.review_list, 1):
            status = "✅ Richtig" if item['is_correct'] else "❌ Falsch"
            text = f"Frage {idx}: {item['question']}\nKategorie: {item['category']}\n" \
                   f"Deine Antwort: {', '.join(item['selected'])}\n" \
                   f"Richtige Antwort: {', '.join(item['correct'])}\nStatus: {status}\n"
            tk.Label(scroll_frame, text=text, font=("Arial", 12), wraplength=900,
                     justify="left", anchor="w", bg="#f0f4f7").pack(pady=5, padx=10, fill="x")

        btn_frame = tk.Frame(review_root, bg="#f0f4f7")
        btn_frame.pack(pady=15)

        def new_quiz():
            review_root.destroy()
            self.view.destroy()
            main()

        tk.Button(btn_frame, text="Neues Quiz starten", font=("Helvetica", 14, "bold"),
                  bg="#4CAF50", fg="white", activebackground="#45a049",
                  command=new_quiz).pack(side="left", padx=10)
        tk.Button(btn_frame, text="Quiz beenden", font=("Arial", 12), fg="red",
                  command=self.view.quit).pack(side="left", padx=10)

# ------------------- Start -------------------
def main():
    model = QuizModel()
    questions_count = len(model.questions_data)

    def start_quiz_callback(user_name, quiz_size, no_repeat, diagramm_typ):
        QuizPresenter(model, user_name, quiz_size, no_repeat, diagramm_typ)

    start_view = StartView(start_quiz_callback, questions_count)
    start_view.mainloop()

if __name__ == "__main__":
    main()
