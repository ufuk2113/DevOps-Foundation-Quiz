# DevOps Foundation Quiz App

Eine interaktive Lern-App zur Vorbereitung auf die **DevOps Foundation Prüfung**.  
Die Anwendung zeigt Multiple-Choice-Fragen mit Kategorien, speichert Ergebnisse und bietet Export-Funktionen.

---

## 🚀 Features

- **Fragenpool mit 300 Fragen** (JSON-Datei `fragen.json`)
- **Startdialog** mit Eingabe von Name und Anzahl Fragen
- **Quiz-Fenster** mit Anzeige der Fragen & Antwortmöglichkeiten
- **Kategorie-Anzeige** pro Frage
- **Antwortprüfung** mit Feedback bei falschen Antworten
- **Review-Fenster** am Ende des Quizzes:
  - Übersicht aller Fragen
  - Gewählte Antworten & richtige Antworten
  - Buttons: „Neues Quiz starten“ & „Quiz beenden“
- **CSV-Export** der Ergebnisse (inkl. Kategorie & Antworten)
- **PDF-Export** der Ergebnisse (mit [ReportLab](https://pypi.org/project/reportlab/))
- **Fragenpool ohne Wiederholung**: Fragen erscheinen erst erneut, wenn alle einmal durchlaufen wurden

---

## 🛠️ Installation

### 1. Repository klonen
```bash
git clone https://github.com/dein-user/devops-foundation-quiz.git
cd devops-foundation-quiz
```

### 2. Abhängigkeiten installieren
Python 3.8+ wird empfohlen.

```bash
pip install reportlab
```

### 3. Fragen-Datei vorbereiten
Die Datei `fragen.json` enthält die 300 Fragen.  
Format pro Frage:
```json
{
  "question": "Was bedeutet „Shift-Left“ im DevOps-Kontext?",
  "options": [
    "Entwickler übernehmen die Rolle der Tester.",
    "Qualität und Tests werden früh im Prozess integriert.",
    "Deployment wird nach links im Lifecycle verschoben.",
    "Entwickler und Operations arbeiten getrennt."
  ],
  "answer": "Qualität und Tests werden früh im Prozess integriert.",
  "category": "CI/CD & Testautomatisierung"
}
```

---

## ▶️ Nutzung

1. Starte die App:
```bash
python main.py
```

2. Gib deinen Namen und die gewünschte Anzahl Fragen ein.  
3. Bearbeite die Fragen und bestätige deine Antworten.  
4. Am Ende siehst du:
   - Punkte & Prozent
   - Review aller Fragen
   - Exportoptionen (CSV & PDF)
   - Möglichkeit zum Neustart oder Beenden

---

## 📊 Ergebnis-Export

- **CSV-Datei**: Enthält alle Fragen, Kategorien, gewählte und richtige Antworten.  
  Beispiel-Dateiname: `Max_quiz_20251001_153045.csv`

- **PDF-Datei**: Enthält dieselben Daten in formatiertem Bericht.  
  Beispiel-Dateiname: `Max_quiz_20251001_153045.pdf`

---

## 📂 Projektstruktur

```
.
├── main.py                # Hauptprogramm
├── fragen.json            # Fragenpool (300 Fragen)
├── asked_questions.json   # Tracking-Datei (automatisch erstellt)
├── README.md              # Dokumentation
```

---

## 📌 Git Commit History (Empfohlen)

- `Initial commit: added base project with questions file`
- `Added StartDialog with name and question count input`
- `Added basic QuizWindow with question and answer options`
- `Implemented answer checking with feedback for wrong answers`
- `Added category display for each question`
- `Added review window with restart and exit options`
- `Added CSV export for quiz results with timestamp`
- `Added PDF export for quiz results with timestamp (requires reportlab)`
- `Added persistent question tracking to avoid repeats across sessions`

---

## ✅ Lizenz

Dieses Projekt dient ausschließlich **Lern- und Trainingszwecken**.  
Keine Garantie auf Vollständigkeit oder Korrektheit der Fragen.
