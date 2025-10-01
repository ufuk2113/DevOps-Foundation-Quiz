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
from abc import ABC, abstractmethod


# === MODEL CLASSES ===
class Question:
    """Repräsentiert eine einzelne Frage"""
    def __init__(self, question, options, answer, category):
        self.question = question
        self.options = options
        self.answer = answer if isinstance(answer, list) else [answer]
        self.category = category

    def is_correct(self, selected_options):
        return set(selected_options) == set(self.answer)


class QuizModel:
    """Verwaltet die Quiz-Daten und Logik"""
    def __init__(self, json_file="fragen.json"):
        self.json_file = json_file
        self.used_questions_file = "used_questions.json"
        self.questions_data = self.load_questions()
        self.current_quiz = None

    def load_questions(self):
        """Lädt Fragen aus JSON-Datei"""
        try:
            with open(self.json_file, "r", encoding="utf-8") as file:
                data = json.load(file)
                return [Question(q['question'], q['options'], q['answer'], q['category']) 
                       for q in data]
        except FileNotFoundError:
            print(f"Fehler: Die Datei '{self.json_file}' wurde nicht gefunden.")
            exit()

    def create_quiz(self, quiz_size, no_repeat=False):
        """Erstellt ein neues Quiz mit den angegebenen Parametern"""
        if no_repeat:
            used_questions_ids = self.load_used_questions()
            available_questions = [q for q in self.questions_data 
                                 if q.question not in used_questions_ids]
            
            if len(available_questions) < quiz_size:
                available_questions = self.questions_data
                used_questions_ids = []
            
            questions = random.sample(available_questions, quiz_size)
            self.save_used_questions(used_questions_ids + [q.question for q in questions])
        else:
            questions = random.sample(self.questions_data, quiz_size)
        
        return QuizSession(questions)

    def load_used_questions(self):
        """Lädt bereits verwendete Fragen"""
        if os.path.exists(self.used_questions_file):
            with open(self.used_questions_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def save_used_questions(self, used_questions):
        """Speichert verwendete Fragen"""
        with open(self.used_questions_file, "w", encoding="utf-8") as f:
            json.dump(used_questions, f, ensure_ascii=False, indent=4)


class QuizSession:
    """Repräsentiert eine Quiz-Sitzung"""
    def __init__(self, questions):
        self.questions = questions
        self.current_question_index = 0
        self.score = 0
        self.review_data = []
        self.start_time = datetime.now()

    @property
    def current_question(self):
        return self.questions[self.current_question_index] if self.questions else None

    @property
    def total_questions(self):
        return len(self.questions)

    @property
    def progress(self):
        return (self.current_question_index / self.total_questions) * 100

    def next_question(self):
        """Geht zur nächsten Frage"""
        if self.current_question_index < self.total_questions - 1:
            self.current_question_index += 1
            return True
        return False

    def check_answer(self, selected_options):
        """Überprüft die Antwort und gibt Feedback"""
        if not selected_options:
            return False, "Keine Auswahl getroffen"
        
        is_correct = self.current_question.is_correct(selected_options)
        if is_correct:
            self.score += 1
        
        # Review-Daten speichern
        self.review_data.append({
            "question": self.current_question.question,
            "category": self.current_question.category,
            "selected": selected_options,
            "correct": self.current_question.answer,
            "is_correct": is_correct
        })
        
        return is_correct, None

    @property
    def percentage(self):
        return round((self.score / self.total_questions) * 100, 2)

    def is_passed(self):
        return self.score >= int(self.total_questions * 0.65)


# === CONTROLLER CLASSES ===
class QuizController:
    """Koordinierte die Interaktion zwischen Model und View"""
    def __init__(self):
        self.model = QuizModel()
        self.current_session = None
        self.user_name = ""
        self.diagram_type = "bar"

    def start_new_quiz(self, user_name, quiz_size, no_repeat, diagram_type):
        """Startet ein neues Quiz"""
        self.user_name = user_name
        self.diagram_type = diagram_type
        self.current_session = self.model.create_quiz(quiz_size, no_repeat)
        return self.current_session

    def submit_answer(self, selected_options):
        """Verarbeitet die Antwortabgabe"""
        if not self.current_session:
            return False, "Keine aktive Quiz-Sitzung"
        
        return self.current_session.check_answer(selected_options)

    def export_results(self):
        """Exportiert die Ergebnisse"""
        if not self.current_session:
            return
        
        exporter = ResultExporter(self.current_session, self.user_name, self.diagram_type)
        exporter.export_all()


class ResultExporter:
    """Kümmert sich um den Export der Ergebnisse"""
    def __init__(self, quiz_session, user_name, diagram_type):
        self.quiz = quiz_session
        self.user_name = user_name
        self.diagram_type = diagram_type

    def export_all(self):
        """Exportiert sowohl CSV als auch PDF"""
        self.export_csv()
        self.export_pdf()

    def export_csv(self):
        """Exportiert Ergebnisse als CSV"""
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        name_clean = self.user_name.replace(" ", "_")
        filename = f"Ergebnisse_{name_clean}_{now}.csv"

        with open(filename, mode="w", encoding="utf-8", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Frage", "Kategorie", "Deine Antwort", "Richtige Antwort", "Status"])
            
            for item in self.quiz.review_data:
                writer.writerow([
                    item["question"],
                    item["category"],
                    ", ".join(item["selected"]),
                    ", ".join(item["correct"]),
                    "Richtig" if item["is_correct"] else "Falsch"
                ])
            
            writer.writerow([])
            writer.writerow(["Gesamtpunktzahl", f"{self.quiz.score}/{self.quiz.total_questions} ({self.quiz.percentage}%)"])
            writer.writerow(["Ergebnis", "✅ Bestanden" if self.quiz.is_passed() else "❌ Nicht bestanden"])

    def create_diagram(self):
        """Erstellt das Diagramm für den PDF-Export"""
        correct_count = self.quiz.score
        wrong_count = self.quiz.total_questions - self.quiz.score
        
        fig, ax = plt.subplots(figsize=(4, 3))
        if self.diagram_type == "bar":
            ax.bar(["Richtig", "Falsch"], [correct_count, wrong_count], color=["green", "red"])
            ax.set_ylabel("Anzahl Fragen")
            ax.set_title("Ergebnisübersicht")
        elif self.diagram_type == "pie":
            ax.pie([correct_count, wrong_count], labels=["Richtig", "Falsch"], 
                   colors=["green", "red"], autopct="%1.1f%%", startangle=90)
            ax.set_title("Ergebnisübersicht")
        
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format="png")
        plt.close(fig)
        img_buffer.seek(0)
        return img_buffer

    def export_pdf(self):
        """Exportiert Ergebnisse als PDF"""
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        name_clean = self.user_name.replace(" ", "_")
        filename = f"Ergebnisse_{name_clean}_{now}.pdf"

        styles = getSampleStyleSheet()
        doc = SimpleDocTemplate(filename, pagesize=A4)
        elements = []

        # Header
        elements.append(Paragraph("DevOps Foundation Prüfungsergebnisse", styles['Title']))
        elements.append(Spacer(1, 12))
        elements.append(Paragraph(f"Teilnehmer: {self.user_name}", styles['Heading2']))
        elements.append(Paragraph(f"Gesamtpunktzahl: {self.quiz.score}/{self.quiz.total_questions} ({self.quiz.percentage}%)", 
                                styles['Heading2']))
        elements.append(Paragraph(f"Ergebnis: {'✅ Bestanden' if self.quiz.is_passed() else '❌ Nicht bestanden'}", 
                                styles['Heading2']))
        elements.append(Spacer(1, 12))

        # Diagramm
        img_buffer = self.create_diagram()
        img = Image(img_buffer, width=300, height=220)
        elements.append(img)
        elements.append(Spacer(1, 20))

        # Detailierte Ergebnisse
        for idx, item in enumerate(self.quiz.review_data, 1):
            status = "✅ Richtig" if item['is_correct'] else "❌ Falsch"
            q_text = f"<b>Frage {idx}:</b> {item['question']}<br/>" \
                     f"<b>Kategorie:</b> {item['category']}<br/>" \
                     f"<b>Deine Antwort:</b> {', '.join(item['selected'])}<br/>" \
                     f"<b>Richtige Antwort:</b> {', '.join(item['correct'])}<br/>" \
                     f"<b>Status:</b> {status}<br/><br/>"
            elements.append(Paragraph(q_text, styles['Normal']))
            elements.append(Spacer(1, 6))

        doc.build(elements)


# === VIEW CLASSES ===
class BaseView(ABC):
    """Abstrakte Basisklasse für Views"""
    @abstractmethod
    def show(self):
        pass
    
    @abstractmethod
    def hide(self):
        pass


class StartView(tk.Tk, BaseView):
    """Startbildschirm für Quiz-Konfiguration"""
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.setup_ui()

    def setup_ui(self):
        self.title("Quiz starten")
        self.geometry("400x400")
        self.resizable(False, False)

        # UI Elemente
        tk.Label(self, text="Name / Kürzel:", font=("Arial", 12)).pack(pady=5)
        self.name_entry = tk.Entry(self, font=("Arial", 12))
        self.name_entry.pack(pady=5)

        tk.Label(self, text="Anzahl der Fragen:", font=("Arial", 12)).pack(pady=5)
        self.num_questions = tk.IntVar(value=50)
        tk.Spinbox(self, from_=10, to=len(self.controller.model.questions_data), 
                  increment=10, textvariable=self.num_questions, font=("Arial", 12)).pack(pady=5)

        self.no_repeat_var = tk.BooleanVar(value=True)
        tk.Checkbutton(self, text="Fragen nicht wiederholen bis alle durchlaufen",
                      variable=self.no_repeat_var, font=("Arial", 11)).pack(pady=10)

        # Diagrammtyp
        self.diagramm_var = tk.StringVar(value="bar")
        tk.Label(self, text="Diagrammtyp für PDF:", font=("Arial", 12)).pack(pady=5)
        tk.Radiobutton(self, text="Balkendiagramm", variable=self.diagramm_var, 
                      value="bar", font=("Arial", 11)).pack()
        tk.Radiobutton(self, text="Kreisdiagramm", variable=self.diagramm_var, 
                      value="pie", font=("Arial", 11)).pack()

        tk.Button(self, text="Quiz starten", font=("Arial", 12, "bold"),
                 bg="#4CAF50", fg="white", activebackground="#45a049", 
                 command=self.start_quiz).pack(pady=10)

    def start_quiz(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("Fehler", "Bitte einen Namen eingeben!")
            return
        
        quiz_size = self.num_questions.get()
        no_repeat = self.no_repeat_var.get()
        diagram_type = self.diagramm_var.get()
        
        self.hide()
        quiz_view = QuizView(self.controller, name, quiz_size, no_repeat, diagram_type)
        quiz_view.show()

    def show(self):
        self.mainloop()

    def hide(self):
        self.destroy()


class QuizView(tk.Tk, BaseView):
    """Haupt-Quiz-Interface"""
    def __init__(self, controller, user_name, quiz_size, no_repeat, diagram_type):
        super().__init__()
        self.controller = controller
        self.user_name = user_name
        self.quiz_size = quiz_size
        self.no_repeat = no_repeat
        self.diagram_type = diagram_type
        
        self.quiz_session = None
        self.time_left = 60
        self.timer_id = None
        self.selected_options = []
        
        self.setup_ui()
        self.start_quiz()

    def setup_ui(self):
        self.title("DevOps Foundation Prüfung")
        self.geometry("950x700")
        self.configure(bg="#f0f4f7")
        self.resizable(False, False)

        # Frames
        self.top_frame = tk.Frame(self, bg="#d1e3f0", padx=20, pady=10)
        self.top_frame.pack(fill="x")
        
        self.question_frame = tk.Frame(self, bg="#ffffff", padx=20, pady=20, relief="groove", bd=2)
        self.question_frame.pack(pady=15, fill="x", padx=20)
        
        self.options_frame = tk.Frame(self, bg="#f7f9fb", padx=20, pady=10, relief="ridge", bd=2)
        self.options_frame.pack(pady=10, fill="x", padx=20)
        
        self.bottom_frame = tk.Frame(self, bg="#d1e3f0", padx=20, pady=10)
        self.bottom_frame.pack(fill="x", pady=10)

        # UI Elemente
        self.progress_label = tk.Label(self.top_frame, text="", font=("Helvetica", 12, "bold"), bg="#d1e3f0")
        self.progress_label.pack(side="left")
        
        self.timer_label = tk.Label(self.top_frame, text="", font=("Helvetica", 12, "bold"), fg="red", bg="#d1e3f0")
        self.timer_label.pack(side="right")
        
        self.score_label = tk.Label(self.bottom_frame, text="Punkte: 0/0", font=("Helvetica", 12, "bold"), bg="#d1e3f0")
        self.score_label.pack(side="left")
        
        self.progress_bar = ttk.Progressbar(self.bottom_frame, length=500, mode="determinate")
        self.progress_bar.pack(side="right", padx=10)

        self.question_label = tk.Label(self.question_frame, text="", wraplength=900, 
                                      font=("Helvetica", 16), justify="left", bg="#ffffff")
        self.question_label.pack()
        
        self.category_label = tk.Label(self.question_frame, text="", font=("Helvetica", 12, "italic"),
                                      fg="gray", bg="#ffffff")
        self.category_label.pack(pady=5)

        self.submit_btn = tk.Button(self, text="Antwort bestätigen", font=("Helvetica", 14, "bold"),
                                   bg="#4CAF50", fg="white", activebackground="#45a049",
                                   command=self.submit_answer)
        self.submit_btn.pack(pady=10)

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def start_quiz(self):
        """Startet das Quiz"""
        self.quiz_session = self.controller.start_new_quiz(
            self.user_name, self.quiz_size, self.no_repeat, self.diagram_type
        )
        self.load_question()

    def update_timer(self):
        """Aktualisiert den Timer"""
        if self.time_left > 0:
            self.timer_label.config(text=f"Verbleibende Zeit: {self.time_left} Sekunden")
            self.time_left -= 1
            self.timer_id = self.after(1000, self.update_timer)
        else:
            messagebox.showinfo("Zeit abgelaufen!", 
                              f"Die Zeit ist abgelaufen.\nRichtige Antwort: {self.quiz_session.current_question.answer}")
            self.next_question()

    def load_question(self):
        """Lädt die aktuelle Frage"""
        if not self.quiz_session or not self.quiz_session.current_question:
            self.finish_quiz()
            return

        question = self.quiz_session.current_question
        
        # Frage anzeigen
        self.question_label.config(text=f"Frage {self.quiz_session.current_question_index + 1}: {question.question}")
        self.category_label.config(text=f"Kategorie: {question.category}")
        self.progress_label.config(text=f"Frage {self.quiz_session.current_question_index + 1} von {self.quiz_size}")
        self.progress_bar['value'] = self.quiz_session.progress
        self.score_label.config(text=f"Punkte: {self.quiz_session.score}/{self.quiz_size}")

        # Optionen anzeigen
        for widget in self.options_frame.winfo_children():
            widget.destroy()
        
        self.selected_options = []
        for option in question.options:
            var = tk.IntVar()
            cb = tk.Checkbutton(self.options_frame, text=option, variable=var,
                               font=("Helvetica", 14), wraplength=900, justify="left",
                               bg="#f7f9fb", activebackground="#e0f0ff")
            cb.var = var
            cb.pack(fill="x", pady=5)
            self.selected_options.append(cb)

        # Timer zurücksetzen
        self.time_left = 60
        if self.timer_id:
            self.after_cancel(self.timer_id)
        self.update_timer()

    def submit_answer(self):
        """Verarbeitet die Antwortabgabe"""
        selected = [cb.cget("text") for cb in self.selected_options if cb.var.get() == 1]
        
        if not selected:
            messagebox.showwarning("Keine Auswahl", "Bitte wähle mindestens eine Antwort aus!")
            return

        is_correct, error = self.controller.submit_answer(selected)
        
        if error:
            messagebox.showerror("Fehler", error)
            return

        # Visuelles Feedback
        for cb in self.selected_options:
            text = cb.cget("text")
            cb.config(state="disabled")
            if text in self.quiz_session.current_question.answer:
                cb.config(bg="#4CAF50", fg="white")
            elif text in selected and text not in self.quiz_session.current_question.answer:
                cb.config(bg="#f44336", fg="white")

        self.after(1500, self.next_question)

    def next_question(self):
        """Geht zur nächsten Frage"""
        if self.timer_id:
            self.after_cancel(self.timer_id)
        
        if not self.quiz_session.next_question():
            self.finish_quiz()
        else:
            self.load_question()

    def finish_quiz(self):
        """Beendet das Quiz und zeigt die Ergebnisse"""
        self.controller.export_results()
        self.hide()
        review_view = ReviewView(self.controller, self.quiz_session, self.user_name)
        review_view.show()

    def on_closing(self):
        """Behandelt das Schließen des Fensters"""
        if messagebox.askyesno("Quiz beenden", "Willst du das Programm wirklich beenden?"):
            self.quit()

    def show(self):
        self.mainloop()

    def hide(self):
        self.destroy()


class ReviewView(tk.Toplevel, BaseView):
    """Zeigt die Quiz-Ergebnisse an"""
    def __init__(self, controller, quiz_session, user_name):
        super().__init__()
        self.controller = controller
        self.quiz_session = quiz_session
        self.user_name = user_name
        self.setup_ui()

    def setup_ui(self):
        self.title("Prüfungsübersicht")
        self.geometry("950x600")
        self.configure(bg="#f0f4f7")

        # Ergebnis-Übersicht
        result_text = "✅ Bestanden" if self.quiz_session.is_passed() else "❌ Nicht bestanden"
        result_color = "green" if self.quiz_session.is_passed() else "red"

        tk.Label(self, text=f"Quiz beendet! Deine Punktzahl: {self.quiz_session.score}/{self.quiz_session.total_questions} ({self.quiz_session.percentage}%)",
                font=("Helvetica", 16, "bold"), bg="#f0f4f7").pack(pady=10)
        
        tk.Label(self, text=f"Ergebnis: {result_text}", font=("Helvetica", 14, "bold"), 
                bg="#f0f4f7", fg=result_color).pack(pady=5)

        # Scrollbare Detail-Ansicht
        canvas = tk.Canvas(self, bg="#f0f4f7")
        scrollbar = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg="#f0f4f7")
        
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Detailierte Ergebnisse
        for idx, item in enumerate(self.quiz_session.review_data, 1):
            status = "✅ Richtig" if item['is_correct'] else "❌ Falsch"
            text = f"Frage {idx}: {item['question']}\nKategorie: {item['category']}\n" \
                  f"Deine Antwort: {', '.join(item['selected'])}\n" \
                  f"Richtige Antwort: {', '.join(item['correct'])}\nStatus: {status}\n"
            
            tk.Label(scroll_frame, text=text, font=("Arial", 12), wraplength=900,
                    justify="left", anchor="w", bg="#f0f4f7").pack(pady=5, padx=10, fill="x")

        # Buttons
        btn_frame = tk.Frame(self, bg="#f0f4f7")
        btn_frame.pack(pady=15)

        tk.Button(btn_frame, text="Neues Quiz starten", font=("Helvetica", 14, "bold"),
                 bg="#4CAF50", fg="white", activebackground="#45a049",
                 command=self.new_quiz).pack(side="left", padx=10)

        tk.Button(btn_frame, text="Quiz beenden", font=("Arial", 12), 
                 fg="red", command=self.confirm_exit).pack(side="left", padx=10)

    def new_quiz(self):
        """Startet ein neues Quiz"""
        self.hide()
        start_view = StartView(self.controller)
        start_view.show()

    def confirm_exit(self):
        """Bestätigt das Beenden des Programms"""
        if messagebox.askyesno("Quiz beenden", "Willst du das Programm wirklich beenden?"):
            self.quit()

    def show(self):
        self.wait_window()

    def hide(self):
        self.destroy()


# === APPLICATION ENTRY POINT ===
def main():
    """Hauptfunktion zum Starten der Anwendung"""
    controller = QuizController()
    start_view = StartView(controller)
    start_view.show()

if __name__ == "__main__":
    main()