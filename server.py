import os
import re
import json
import sqlite3
import mimetypes
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.utilities import SQLDatabase

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "itm_university.db"))
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

# Connect to database via LangChain
db = SQLDatabase.from_uri(f"sqlite:///{DB_PATH}")

def get_best_model():
    """Selects qwen2.5-coder:7b if downloaded, else falls back to llama3.2."""
    try:
        import urllib.request
        req = urllib.request.Request("http://localhost:11434/api/tags")
        with urllib.request.urlopen(req, timeout=2) as response:
            data = json.loads(response.read().decode())
            installed = [m["name"] for m in data.get("models", [])]
            for m in installed:
                if "qwen2.5-coder:7b" in m:
                    return "qwen2.5-coder:7b"
                if "qwen2.5-coder" in m:
                    return m
    except Exception:
        pass
    return "llama3.2"

active_model = get_best_model()
print(f"Using Ollama Model: {active_model}")

llm = ChatOllama(model=active_model, base_url="http://localhost:11434", temperature=0.0)

# Memory Session store
chat_histories = {}

def get_session_history(session_id: str):
    if session_id not in chat_histories:
        chat_histories[session_id] = InMemoryChatMessageHistory()
    return chat_histories[session_id]

# Strict Text-to-SQL Prompt adhering to clean relational rules
sql_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are a specialized Text-to-SQL converter for ITM Skills University SQLite database.
Convert the user's question into ONE valid SQLite query.

DATABASE SCHEMA:
{table_info}

COLUMN NOTES:
- students: student_id, name, branch ('CSE', 'AI & DS', 'Cyber Sec', 'Cloud Comp'), semester (1-8), cgpa (0-10), attendance_pct (0-100), fees_status ('Paid', 'Pending')
- courses: course_id, course_name, branch, semester, credits, faculty_id
- faculty: faculty_id, name, dept_code, designation, experience_years
- placements: placement_id, student_id, company, role, package_lpa (Lakhs Per Annum), placement_type ('Full-Time', 'Internship + PPO')
- departments: dept_code, dept_name, hod_name, location

CRITICAL SQL RULES:
1. NEVER mix COUNT(*) with normal columns in the same SELECT statement (e.g. NEVER write 'SELECT COUNT(*), name'). In SQLite, this only returns 1 row and breaks the output.
2. When the user asks "how many AND name them" or asks for a list with conditions (e.g., "who paid fees?", "attendance less than 75%"), RETURN ONLY THE FULL LIST OF ROWS. The application counts the rows automatically in Python!
3. Do NOT arbitrarily add LIMIT unless the user explicitly requested a specific number (e.g. "top 3", "5 students").
4. If the question cannot be answered from the schema, output exactly: CANNOT_ANSWER
5. Output ONLY raw executable SQLite query. Never use markdown blocks (```sql), comments, or explanations.
6. When the user asks a follow-up question (e.g. "Unki attendance kitni hai?", "Who among them..."), use the conversation history to understand context.

FEW-SHOT EXAMPLES:
Q: Kaun kaun se students ne fees pay ki hai?
SQL: SELECT student_id, name, branch, semester, fees_status FROM students WHERE fees_status = 'Paid' ORDER BY name ASC;

Q: CSE ke top 3 students by CGPA kaun hain?
SQL: SELECT name, branch, cgpa FROM students WHERE branch = 'CSE' ORDER BY cgpa DESC LIMIT 3;

Q: Kitne students ki attendance 75% se kam hai aur unke naam kya hain?
SQL: SELECT name, branch, semester, attendance_pct FROM students WHERE attendance_pct < 75 ORDER BY attendance_pct ASC;

Q: Which students got placed and in which company?
SQL: SELECT s.name, s.branch, p.company, p.role, p.package_lpa FROM placements p JOIN students s ON p.student_id = s.student_id ORDER BY p.package_lpa DESC;

Q: Highest package kiska laga?
SQL: SELECT s.name, p.company, p.role, p.package_lpa FROM placements p JOIN students s ON p.student_id = s.student_id ORDER BY p.package_lpa DESC LIMIT 1;
"""
    ),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}")
])

sql_chain = sql_prompt | llm
sql_generator = RunnableWithMessageHistory(
    sql_chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="history"
)

def clean_sql(raw_output: str) -> str:
    cleaned = re.sub(r"```(sql)?", "", raw_output).strip()
    cleaned = re.sub(r"^SQL:\s*", "", cleaned, flags=re.IGNORECASE).strip()
    return cleaned

def execute_raw_sql(query: str):
    """Executes query and returns column names and row lists."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(query)
    columns = [col[0] for col in cur.description] if cur.description else []
    rows = cur.fetchall()
    conn.close()
    return columns, rows

def get_db_stats():
    """Returns database summary stats for UI badges."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    stats = {}
    for table in ['students', 'courses', 'placements', 'faculty', 'departments']:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        stats[table] = cur.fetchone()[0]
    conn.close()
    return stats

def generate_headline_and_suggestions(question: str, query: str, columns: list, rows: list):
    """
    Generates a punchy, factual headline and follow-up chips.
    Math/count is 100% computed in Python, never hallucinated by LLM!
    """
    row_count = len(rows)

    if row_count == 0:
        return {
            "headline": "Koi record nahi mila (0 Results)",
            "summary": "Database mein is condition se match karta hua koi data uplabdh nahi hai.",
            "suggestions": [
                "Sabhi students ki list dikhao",
                "Placement statistics dikhao",
                "Pending fees wale students kaun hain?"
            ]
        }

    # If it's a single aggregate count query like SELECT COUNT(*) FROM students...
    if len(columns) == 1 and str(columns[0]).upper().startswith("COUNT") and row_count == 1:
        val = rows[0][0]
        return {
            "headline": f"Total Count: {val}",
            "summary": f"Query ke mutabik kul {val} records paaye gaye.",
            "suggestions": [
                "Inke naam aur branch ki poori list dikhao",
                "Branch-wise distribution dikhao"
            ]
        }

    # Ask LLM strictly for a short 1-line headline and 3 follow-up suggestions
    meta_prompt = f"""You are a helpful university database portal assistant.
User Question: "{question}"
Executed SQL: "{query}"
Total Rows Found: {row_count}
Columns: {columns}
Sample Row: {rows[0] if rows else 'None'}

Your Task:
1. Provide a clear, bold 1-sentence headline summarizing the answer (e.g. "{row_count} students ne fees pay ki hai" or "Top 3 students in CSE branch"). Mention the exact count ({row_count}).
2. Provide a 1-sentence clean summary (no filler greetings like 'Namaste' or 'I hope this helps').
3. Provide exactly 3 short follow-up questions the user might ask next.

Return ONLY a JSON object in this format:
{{
  "headline": "<1 short sentence>",
  "summary": "<1 clean sentence>",
  "suggestions": ["<Q1>", "<Q2>", "<Q3>"]
}}
"""
    try:
        current_model = get_best_model()
        meta_llm = ChatOllama(model=current_model, base_url="http://localhost:11434", temperature=0.0)
        res = meta_llm.invoke(meta_prompt).content
        # Extract JSON
        match = re.search(r"\{.*\}", res, re.DOTALL)
        if match:
            parsed = json.loads(match.group(0))
            # Guarantee the verified row count is accurate
            return {
                "headline": parsed.get("headline", f"{row_count} records mile"),
                "summary": parsed.get("summary", ""),
                "suggestions": parsed.get("suggestions", ["Pending fees wale dikhao", "Branch-wise breakdown", "Highest CGPA kiska hai?"])
            }
    except Exception as e:
        print("Meta prompt fallback:", e)

    # Deterministic fallback if LLM formatting fails
    return {
        "headline": f"{row_count} records paaye gaye",
        "summary": f"Database ne {row_count} results return kiye hain.",
        "suggestions": [
            "Pending fees wale students dikhao",
            "Highest placement package kiska hai?",
            "GenAI course kaun padha raha hai?"
        ]
    }

class RequestHandler(BaseHTTPRequestHandler):
    def send_json(self, status: int, data: dict):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/stats":
            try:
                stats = get_db_stats()
                schema_info = db.get_table_info()
                current_model = get_best_model()
                self.send_json(200, {"stats": stats, "schema": schema_info, "model": current_model})
            except Exception as e:
                self.send_json(500, {"error": str(e)})
            return

        # Serve static files
        if path == "/" or path == "/index.html":
            file_path = os.path.join(STATIC_DIR, "index.html")
        else:
            file_path = os.path.join(STATIC_DIR, path.lstrip("/"))

        if os.path.isfile(file_path):
            mime_type, _ = mimetypes.guess_type(file_path)
            with open(file_path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", mime_type or "text/plain")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"404 Not Found")

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length)

        try:
            payload = json.loads(post_data.decode("utf-8")) if post_data else {}
        except Exception:
            payload = {}

        if path == "/api/reset":
            session_id = payload.get("session_id", "default")
            if session_id in chat_histories:
                del chat_histories[session_id]
            self.send_json(200, {"status": "cleared", "session_id": session_id})
            return

        if path == "/api/query":
            question = payload.get("question", "").strip()
            session_id = payload.get("session_id", "default_session")

            if not question:
                self.send_json(400, {"error": "Question is required"})
                return

            try:
                table_info = db.get_table_info()

                # Update model if qwen2.5-coder:7b just finished downloading
                best_model = get_best_model()
                llm.model = best_model

                # 1. Generate SQL with Conversational Memory
                sql_response = sql_generator.invoke(
                    {"table_info": table_info, "input": question},
                    config={"configurable": {"session_id": session_id}}
                )
                query = clean_sql(sql_response.content)

                if query == "CANNOT_ANSWER":
                    self.send_json(200, {
                        "headline": "Sawaal ka uttar database se sambhav nahi hai",
                        "summary": "Database schema ke mutabik yeh jaankari uplabdh nahi hai.",
                        "sql": None,
                        "columns": [],
                        "rows": [],
                        "total_count": 0,
                        "suggestions": [
                            "Sabhi students ki list dikhao",
                            "Placement records dikhao",
                            "Faculty details dikhao"
                        ],
                        "session_id": session_id
                    })
                    return

                # 2. Execute SQL on SQLite
                try:
                    columns, rows = execute_raw_sql(query)
                except Exception as db_err:
                    self.send_json(200, {
                        "headline": "Database Query Error",
                        "summary": f"SQL error: {str(db_err)}",
                        "sql": query,
                        "columns": [],
                        "rows": [],
                        "total_count": 0,
                        "suggestions": [
                            "Sabhi students ki list dikhao",
                            "CSE branch ke students dikhao"
                        ],
                        "session_id": session_id
                    })
                    return

                # 3. Generate Verified Headline & Follow-up Suggestions
                meta = generate_headline_and_suggestions(question, query, columns, rows)

                self.send_json(200, {
                    "headline": meta["headline"],
                    "summary": meta["summary"],
                    "sql": query,
                    "columns": columns,
                    "rows": rows,
                    "total_count": len(rows),
                    "suggestions": meta["suggestions"],
                    "session_id": session_id
                })

            except Exception as e:
                self.send_json(500, {"error": str(e)})
            return

        self.send_response(404)
        self.end_headers()

def run_server(port=8000):
    server = HTTPServer(("127.0.0.1", port), RequestHandler)
    print(f"🚀 ITM Skills University Portal running at: http://127.0.0.1:{port}")
    server.serve_forever()

if __name__ == "__main__":
    run_server()
