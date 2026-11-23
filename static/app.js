// ITM Skills University AI Campus Portal - Client Logic

document.addEventListener("DOMContentLoaded", () => {
  const chatForm = document.getElementById("chat-form");
  const chatInput = document.getElementById("chat-input");
  const messagesContainer = document.getElementById("messages-container");
  const welcomeCard = document.getElementById("welcome-card");
  const btnSend = document.getElementById("btn-send");
  const btnReset = document.getElementById("btn-reset-session");
  const menuToggle = document.getElementById("menu-toggle");
  const sidebar = document.getElementById("sidebar");
  const toggleSchema = document.getElementById("toggle-schema");
  const schemaBody = document.getElementById("schema-body");
  const modelNameLabel = document.getElementById("model-name-label");

  // Persistent session ID
  let sessionId = localStorage.getItem("itm_session_id");
  if (!sessionId) {
    sessionId = "session_" + Math.random().toString(36).substring(2, 9);
    localStorage.setItem("itm_session_id", sessionId);
  }

  const sessionBadge = document.getElementById("session-badge");
  if (sessionBadge) {
    sessionBadge.textContent = "Session: " + sessionId.substring(0, 12);
  }

  // 1. Fetch live Database stats on load
  fetchDatabaseStats();

  async function fetchDatabaseStats() {
    try {
      const res = await fetch("/api/stats");
      if (res.ok) {
        const data = await res.json();
        if (data.stats) {
          if (data.stats.students) document.getElementById("stat-students").textContent = data.stats.students;
          if (data.stats.placements) document.getElementById("stat-placements").textContent = data.stats.placements;
          if (data.stats.courses) document.getElementById("stat-courses").textContent = data.stats.courses;
          if (data.stats.faculty) document.getElementById("stat-faculty").textContent = data.stats.faculty;
        }
        if (data.model && modelNameLabel) {
          modelNameLabel.textContent = data.model;
        }
      }
    } catch (err) {
      console.warn("Could not fetch database stats:", err);
    }
  }

  // 2. Make Sidebar Stat Cards Clickable!
  document.querySelectorAll(".stat-card").forEach(card => {
    card.addEventListener("click", () => {
      const action = card.getAttribute("data-action");
      let query = "";
      if (action === "view-students") {
        query = "Show all students with their branch, semester, CGPA, attendance, and fees status";
      } else if (action === "view-placements") {
        query = "Show all campus placement records with student name, company, role, and package LPA";
      } else if (action === "view-courses") {
        query = "Show all courses offered with their branch, credits, and faculty name";
      } else if (action === "view-faculty") {
        query = "Show all faculty members with department, designation, and experience";
      }
      if (query) submitQuery(query);
    });
  });

  // 3. Quick Prompt Chips (Sidebar & Strip above input)
  document.querySelectorAll(".chip, .strip-chip").forEach(chip => {
    chip.addEventListener("click", () => {
      const prompt = chip.getAttribute("data-prompt");
      if (prompt) submitQuery(prompt);
    });
  });

  // Auto-resize input textarea
  chatInput.addEventListener("input", () => {
    chatInput.style.height = "auto";
    chatInput.style.height = Math.min(chatInput.scrollHeight, 140) + "px";
  });

  // Enter to send (Shift+Enter for new line)
  chatInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      chatForm.dispatchEvent(new Event("submit"));
    }
  });

  // Toggle mobile sidebar
  if (menuToggle && sidebar) {
    menuToggle.addEventListener("click", () => sidebar.classList.toggle("open"));
  }

  // Toggle Schema accordion
  if (toggleSchema && schemaBody) {
    toggleSchema.addEventListener("click", () => {
      const isHidden = schemaBody.style.display === "none";
      schemaBody.style.display = isHidden ? "flex" : "none";
      const arrow = toggleSchema.querySelector(".accordion-arrow");
      if (arrow) arrow.textContent = isHidden ? "▾" : "▸";
    });
  }

  // Reset conversation memory
  btnReset.addEventListener("click", async () => {
    if (confirm("Start a new conversation? This resets conversational memory.")) {
      try {
        await fetch("/api/reset", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ session_id: sessionId })
        });
      } catch (err) {
        console.error("Error resetting session:", err);
      }
      messagesContainer.innerHTML = "";
      if (welcomeCard) messagesContainer.appendChild(welcomeCard);
      sessionId = "session_" + Math.random().toString(36).substring(2, 9);
      localStorage.setItem("itm_session_id", sessionId);
      sessionBadge.textContent = "Session: " + sessionId.substring(0, 12);
    }
  });

  // Handle Form Submission
  chatForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const query = chatInput.value.trim();
    if (query) submitQuery(query);
  });

  async function submitQuery(queryText) {
    if (!queryText) return;

    if (welcomeCard && welcomeCard.parentNode === messagesContainer) {
      welcomeCard.remove();
    }

    appendUserMessage(queryText);
    chatInput.value = "";
    chatInput.style.height = "auto";
    btnSend.disabled = true;

    if (window.innerWidth <= 840 && sidebar) {
      sidebar.classList.remove("open");
    }

    const loadingElem = appendLoading();
    scrollToBottom();

    try {
      const res = await fetch("/api/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: queryText,
          session_id: sessionId
        })
      });

      loadingElem.remove();

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        appendAssistantMessage({
          headline: "Database Error",
          summary: errorData.error || res.statusText,
          sql: null,
          columns: [],
          rows: [],
          suggestions: []
        });
        return;
      }

      const data = await res.json();
      appendAssistantMessage(data);

    } catch (err) {
      loadingElem.remove();
      appendAssistantMessage({
        headline: "Connection Error",
        summary: "Could not reach server: " + err.message + ". Check server.py.",
        sql: null,
        columns: [],
        rows: [],
        suggestions: []
      });
    } finally {
      btnSend.disabled = false;
      scrollToBottom();
      chatInput.focus();
    }
  }

  function appendUserMessage(text) {
    const row = document.createElement("div");
    row.className = "message-row user";
    const bubble = document.createElement("div");
    bubble.className = "user-bubble";
    bubble.textContent = text;
    row.appendChild(bubble);
    messagesContainer.appendChild(row);
  }

  function appendLoading() {
    const row = document.createElement("div");
    row.className = "message-row assistant";
    row.innerHTML = `
      <div class="loading-indicator">
        <span>Executing query on ITM Skills University Database...</span>
        <div class="loading-dots">
          <div class="loading-dot"></div>
          <div class="loading-dot"></div>
          <div class="loading-dot"></div>
        </div>
      </div>
    `;
    messagesContainer.appendChild(row);
    return row;
  }

  function appendAssistantMessage(data) {
    const row = document.createElement("div");
    row.className = "message-row assistant";

    const card = document.createElement("div");
    card.className = "assistant-card";

    // 1. Bold Headline with Exact Verified Row Count
    const headlineRow = document.createElement("div");
    headlineRow.className = "headline-row";

    const headline = document.createElement("h3");
    headline.className = "result-headline";
    headline.textContent = data.headline || `${data.rows ? data.rows.length : 0} results found`;
    headlineRow.appendChild(headline);

    if (data.rows && data.rows.length > 0) {
      const countBadge = document.createElement("span");
      countBadge.className = "result-count-badge";
      countBadge.textContent = `${data.rows.length} ${data.rows.length === 1 ? 'Record' : 'Records'}`;
      headlineRow.appendChild(countBadge);
    }
    card.appendChild(headlineRow);

    // 2. Short Clean Summary
    if (data.summary) {
      const summary = document.createElement("p");
      summary.className = "result-summary";
      summary.innerHTML = data.summary
        .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
      card.appendChild(summary);
    }

    // 3. Table Toolbar & Interactive Scrollable Table
    if (data.columns && data.columns.length > 0 && data.rows && data.rows.length > 0) {
      const toolbar = document.createElement("div");
      toolbar.className = "table-toolbar";

      // Live Search Filter Input
      const filterInput = document.createElement("input");
      filterInput.type = "text";
      filterInput.className = "filter-input";
      filterInput.placeholder = "🔍 Filter in results...";

      // Download CSV Button
      const btnDownload = document.createElement("button");
      btnDownload.type = "button";
      btnDownload.className = "btn-download-csv";
      btnDownload.innerHTML = `<span>⬇</span> Download CSV`;
      btnDownload.addEventListener("click", () => {
        downloadCSV(data.columns, data.rows);
      });

      toolbar.appendChild(filterInput);
      toolbar.appendChild(btnDownload);
      card.appendChild(toolbar);

      // Table Container
      const tableContainer = document.createElement("div");
      tableContainer.className = "table-scroll-container";

      const table = document.createElement("table");
      table.className = "data-table";

      // Thead
      const thead = document.createElement("thead");
      const hRow = document.createElement("tr");

      const thIndex = document.createElement("th");
      thIndex.className = "col-index";
      thIndex.textContent = "#";
      hRow.appendChild(thIndex);

      data.columns.forEach(col => {
        const th = document.createElement("th");
        // Clean column headers for display
        th.textContent = col.replace(/_/g, " ").toUpperCase();
        hRow.appendChild(th);
      });
      thead.appendChild(hRow);
      table.appendChild(thead);

      // Tbody
      const tbody = document.createElement("tbody");
      data.rows.forEach((rowVals, idx) => {
        const tr = document.createElement("tr");

        const tdIdx = document.createElement("td");
        tdIdx.className = "col-index";
        tdIdx.textContent = idx + 1;
        tr.appendChild(tdIdx);

        rowVals.forEach(val => {
          const td = document.createElement("td");
          // Status badges
          if (val === "Paid") {
            td.innerHTML = `<span class="badge-status badge-paid">🟢 Paid</span>`;
          } else if (val === "Pending") {
            td.innerHTML = `<span class="badge-status badge-pending">🔴 Pending</span>`;
          } else if (val === "Full-Time" || val === "Internship + PPO") {
            td.innerHTML = `<span class="badge-status badge-type">${val}</span>`;
          } else {
            td.textContent = (val !== null && val !== undefined) ? val : "-";
          }
          tr.appendChild(td);
        });
        tbody.appendChild(tr);
      });
      table.appendChild(tbody);
      tableContainer.appendChild(table);
      card.appendChild(tableContainer);

      // Live Filter Listener
      filterInput.addEventListener("input", () => {
        const term = filterInput.value.toLowerCase();
        const trs = tbody.querySelectorAll("tr");
        trs.forEach(tr => {
          const text = tr.textContent.toLowerCase();
          tr.style.display = text.includes(term) ? "" : "none";
        });
      });
    }

    // 4. Collapsed Technical Details (SQL at Bottom!)
    if (data.sql) {
      const details = document.createElement("details");
      details.className = "tech-details";
      details.innerHTML = `
        <summary>⚙️ Technical details (SQL Query)</summary>
        <div class="tech-content">
          <pre>${escapeHTML(data.sql)}</pre>
          <button class="btn-copy-sql" type="button">Copy SQL</button>
        </div>
      `;

      const copyBtn = details.querySelector(".btn-copy-sql");
      copyBtn.addEventListener("click", () => {
        navigator.clipboard.writeText(data.sql);
        copyBtn.textContent = "Copied!";
        setTimeout(() => copyBtn.textContent = "Copy SQL", 1600);
      });

      card.appendChild(details);
    }

    // 5. Dynamic Follow-Up Suggestions (Under Result)
    if (data.suggestions && data.suggestions.length > 0) {
      const suggContainer = document.createElement("div");
      suggContainer.className = "suggestion-container";

      const suggLabel = document.createElement("span");
      suggLabel.className = "suggestion-label";
      suggLabel.textContent = "Suggested follow-ups:";
      suggContainer.appendChild(suggLabel);

      data.suggestions.forEach(suggText => {
        const chip = document.createElement("button");
        chip.type = "button";
        chip.className = "suggestion-chip";
        chip.textContent = suggText;
        chip.addEventListener("click", () => submitQuery(suggText));
        suggContainer.appendChild(chip);
      });

      card.appendChild(suggContainer);
    }

    row.appendChild(card);
    messagesContainer.appendChild(row);
  }

  function downloadCSV(columns, rows) {
    if (!columns || !rows) return;
    let csvContent = "data:text/csv;charset=utf-8,";
    // Header
    csvContent += columns.map(c => `"${c}"`).join(",") + "\n";
    // Rows
    rows.forEach(row => {
      csvContent += row.map(val => `"${(val !== null && val !== undefined ? val : '')}"`).join(",") + "\n";
    });
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `itm_university_query_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  function escapeHTML(str) {
    return str.replace(/[&<>'"]/g,
      tag => ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        "'": '&#39;',
        '"': '&quot;'
      }[tag] || tag)
    );
  }

  function scrollToBottom() {
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }
});
