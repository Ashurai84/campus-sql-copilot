# 🎓 Campus SQL Copilot (AI-Powered University Database Assistant)

> An enterprise-grade, conversational Text-to-SQL system designed for university faculty and administrators. Converts natural language queries (English & Hinglish) into validated SQLite operations with **zero hallucination**, verified statistical counts in Python, conversational memory, and a clean botanical pastel dashboard.

---

## 🌟 Key Highlights

- **🔒 100% Privacy & On-Premises Inference**: Powered by local Ollama (`qwen2.5-coder:7b` / `llama3.2`). Student academic records, fees status, and placements never leave college hardware.
- **🛡️ Anti-Hallucination & Verified Arithmetic**: Eliminates the SQLite aggregate trap (`SELECT COUNT(*), col`). Row counts are computed in Python (`len(rows)`), guaranteeing 100% factual accuracy in headlines and summaries.
- **🧠 Conversational Memory (`RunnableWithMessageHistory`)**: Remembers context across multi-turn inquiries (e.g. *"CSE ke top 3 students kaun hain?"* followed by *"Inki attendance kitni hai?"*).
- **🎨 Non-Technical Teacher UI**: Styled in a soothing botanical pastel palette (Terracotta, Matcha Sage, Warm Oatmeal, Soft Amber — **no harsh blues or purples**).
  - Sticky table headers with sequential row numbering (`# 1`, `# 2`...).
  - Live in-browser search filtering.
  - 1-click **Download CSV** export.
  - Collapsed technical details with 1-click **Copy SQL** button.
  - Interactive clickable stat cards & dynamic follow-up chips.

---

## 🏗️ Architecture Flow

```text
User Query (English / Hinglish)
           │
           ▼
[ChatPromptTemplate with Few-Shot Rules]
           │
           ▼
[Local Ollama: Qwen2.5-Coder / Llama3.2]  ───► Outputs strict, single SELECT SQL
           │
           ▼
[Regex Cleaner & SQL Validator]          ───► Strips markdown blocks (```sql)
           │
           ▼
[SQLite Execution (itm_university.db)]   ───► Executes raw query
           │
           ▼
[Python Ground-Truth Computation]        ───► Computes len(rows), parses schema
           │
           ▼
[Clean JSON Response to Frontend]        ───► Headline, Full Table, CSV, Collapsed SQL
```

---

## 🗄️ Relational Database Schema

The database (`itm_university.db`) is normalized across 5 interconnected tables:

```text
departments (dept_code, dept_name, hod_name, location)
    │
    ├── faculty (faculty_id, name, dept_code, designation, experience_years)
    │     └── courses (course_id, course_name, branch, semester, credits, faculty_id)
    │
    └── students (student_id, name, branch, semester, cgpa, attendance_pct, fees_status)
          └── placements (placement_id, student_id, company, role, package_lpa, placement_type)
```

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- **Python 3.10+**
- **Ollama** installed on your system ([Download Ollama](https://ollama.ai))

### 2. Pull Local Model
```bash
# Recommended high-accuracy coding model:
ollama pull qwen2.5-coder:7b

# Or lightweight fallback:
ollama pull llama3.2
```

### 3. Clone and Setup Environment
```bash
git clone https://github.com/<your-username>/<repo-name>.git
cd <repo-name>

python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Initialize Database
```bash
python seed_db.py
```

### 5. Launch Application
```bash
python server.py
```
Open **[http://localhost:8000](http://localhost:8000)** in your browser!

---

## 🧪 Example Inquiries Handled

| Question (English / Hinglish) | Generated SQL | Output Feature |
| :--- | :--- | :--- |
| *"Kaun kaun se students ne fees pay ki hai?"* | `SELECT student_id, name, branch, semester, fees_status FROM students WHERE fees_status = 'Paid' ORDER BY name ASC;` | Full 12-row table, Green badge, CSV download |
| *"Unme se CSE branch ke kaun kaun hain?"* | `SELECT name, branch FROM students WHERE branch = 'CSE';` | Multi-turn conversational memory |
| *"Kitne students ki attendance 75% se kam hai?"* | `SELECT name, branch, semester, attendance_pct FROM students WHERE attendance_pct < 75 ORDER BY attendance_pct ASC;` | Real-time Python count & list |
| *"Highest package kiska laga aur kis company mein?"* | `SELECT s.name, p.company, p.role, p.package_lpa FROM placements p JOIN students s ON p.student_id = s.student_id ORDER BY p.package_lpa DESC LIMIT 1;` | Cross-table relational JOIN |

---

## 🛠️ Tech Stack

- **LLM Engine**: Ollama (`qwen2.5-coder:7b`, `llama3.2`)
- **Orchestration**: LangChain (`ChatOllama`, `ChatPromptTemplate`, `RunnableWithMessageHistory`)
- **Database**: SQLite3, SQLAlchemy
- **Backend API**: Python standard `http.server` (Lightweight REST JSON endpoints)
- **Frontend**: Vanilla HTML5, CSS3 (CSS Grid, Variables, Botanical Pastel Theme), JavaScript (Fetch API, Blob CSV generation)

---

## 📜 License
MIT License. Free to use and adapt for academic and educational projects.
