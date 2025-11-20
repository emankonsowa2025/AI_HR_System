const API_BASE = "/api";

let hasMessages = false;

// Welcome Screen Handler
function initWelcomeScreen() {
  const getStartedBtn = document.getElementById("getStartedBtn");
  const welcomeScreen = document.getElementById("welcomeScreen");
  const chatApp = document.getElementById("chatApp");

  getStartedBtn.addEventListener("click", () => {
    welcomeScreen.style.animation = "fadeOut 0.5s ease-out";
    setTimeout(() => {
      welcomeScreen.style.display = "none";
      chatApp.style.display = "flex";
      chatApp.style.animation = "fadeIn 0.5s ease-in";
    }, 500);
  });
}

// Fetch and display chat history
async function fetchHistory() {
  try {
    const res = await fetch(`${API_BASE}/history`);
    const msgs = await res.json();
    const hist = document.getElementById("history");
    
    if (!msgs || msgs.length === 0) {
      hasMessages = false;
      hist.innerHTML = `
        <div class="empty-state">
          <div class="empty-icon">💬</div>
          <h3>Start Your Conversation</h3>
          <p>Ask me anything about your career, skills, or job opportunities</p>
          <div class="quick-prompts">
            <button class="prompt-chip" data-prompt="What skills should I develop for a data scientist role?">📊 Skills for Data Science</button>
            <button class="prompt-chip" data-prompt="Can you analyze my skills and suggest suitable jobs?">🎯 Analyze My Skills</button>
            <button class="prompt-chip" data-prompt="What are the latest trends in software development?">💻 Tech Trends</button>
          </div>
        </div>
      `;
      initQuickPrompts();
      return;
    }

    hasMessages = true;
    hist.innerHTML = msgs
      .reverse()
      .map((m) => {
        const avatar = m.role === "user" ? "👤" : "🤖";
        return `
          <div class="msg ${m.role}">
            <div class="msg-avatar">${avatar}</div>
            <div class="msg-content">
              <div class="msg-role">${m.role}</div>
              <div class="msg-text">${escapeHtml(m.text)}</div>
            </div>
          </div>
        `;
      })
      .join("");
    
    // Scroll to bottom
    hist.scrollTop = hist.scrollHeight;
  } catch (error) {
    console.error("Error fetching history:", error);
  }
}

// Send message to the API
async function sendMessage(text) {
  const hist = document.getElementById("history");
  const typingIndicator = document.getElementById("typingIndicator");
  
  // Add user message immediately
  if (hasMessages) {
    const userMsg = `
      <div class="msg user">
        <div class="msg-avatar">👤</div>
        <div class="msg-content">
          <div class="msg-role">You</div>
          <div class="msg-text">${escapeHtml(text)}</div>
        </div>
      </div>
    `;
    hist.innerHTML += userMsg;
  }
  
  hist.scrollTop = hist.scrollHeight;
  typingIndicator.style.display = "flex";

  try {
    const res = await fetch(`${API_BASE}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text }),
    });
    
    const data = await res.json();
    typingIndicator.style.display = "none";
    
    await fetchHistory();
    
    // Text-to-speech for assistant reply
    if (data.messages && data.messages.length) {
      const reply = data.messages[0].text;
      if (window.speechSynthesis) {
        const utterance = new SpeechSynthesisUtterance(reply);
        utterance.rate = 1.0;
        utterance.pitch = 1.0;
        window.speechSynthesis.speak(utterance);
      }
    }
  } catch (error) {
    console.error("Error sending message:", error);
    typingIndicator.style.display = "none";
    
    const errorMsg = `
      <div class="msg assistant">
        <div class="msg-avatar">🤖</div>
        <div class="msg-content">
          <div class="msg-role">Assistant</div>
          <div class="msg-text">Sorry, I encountered an error. Please try again.</div>
        </div>
      </div>
    `;
    hist.innerHTML += errorMsg;
    hist.scrollTop = hist.scrollHeight;
  }
}

// Initialize quick prompt buttons
function initQuickPrompts() {
  const promptChips = document.querySelectorAll(".prompt-chip");
  promptChips.forEach((chip) => {
    chip.addEventListener("click", () => {
      const prompt = chip.getAttribute("data-prompt");
      const msgInput = document.getElementById("message");
      msgInput.value = prompt;
      msgInput.focus();
    });
  });
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

// Clear chat history
async function clearChat() {
  if (confirm("Are you sure you want to clear the chat history?")) {
    // In a real app, you'd call an API to clear server-side history
    const hist = document.getElementById("history");
    hasMessages = false;
    hist.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">💬</div>
        <h3>Start Your Conversation</h3>
        <p>Ask me anything about your career, skills, or job opportunities</p>
        <div class="quick-prompts">
          <button class="prompt-chip" data-prompt="What skills should I develop for a data scientist role?">📊 Skills for Data Science</button>
          <button class="prompt-chip" data-prompt="Can you analyze my skills and suggest suitable jobs?">🎯 Analyze My Skills</button>
          <button class="prompt-chip" data-prompt="What are the latest trends in software development?">💻 Tech Trends</button>
        </div>
      </div>
    `;
    initQuickPrompts();
  }
}

// Initialize the application
document.addEventListener("DOMContentLoaded", () => {
  // Initialize welcome screen
  const welcomeScreen = document.getElementById("welcomeScreen");
  const chatApp = document.getElementById("chatApp");
  
  if (welcomeScreen) {
    initWelcomeScreen();
  } else {
    // If no welcome screen, show chat directly
    chatApp.style.display = "flex";
    fetchHistory();
  }

  const sendBtn = document.getElementById("send");
  const msgInput = document.getElementById("message");
  const speechBtn = document.getElementById("speech");
  const clearBtn = document.getElementById("clearChat");

  // Send message on button click
  sendBtn.addEventListener("click", async () => {
    const txt = msgInput.value.trim();
    if (!txt) return;
    await sendMessage(txt);
    msgInput.value = "";
    adjustTextareaHeight(msgInput);
  });

  // Send message on Enter (Shift+Enter for new line)
  msgInput.addEventListener("keydown", async (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      const txt = msgInput.value.trim();
      if (!txt) return;
      await sendMessage(txt);
      msgInput.value = "";
      adjustTextareaHeight(msgInput);
    }
  });

  // Auto-resize textarea
  msgInput.addEventListener("input", () => {
    adjustTextareaHeight(msgInput);
  });

  // Clear chat button
  if (clearBtn) {
    clearBtn.addEventListener("click", clearChat);
  }

  // Speech recognition
  if (window.webkitSpeechRecognition || window.SpeechRecognition) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.lang = "en-US";
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onstart = () => {
      speechBtn.style.background = "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)";
      speechBtn.style.color = "white";
    };

    recognition.onend = () => {
      speechBtn.style.background = "transparent";
      speechBtn.style.color = "#64748b";
    };

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      msgInput.value = transcript;
      adjustTextareaHeight(msgInput);
      msgInput.focus();
    };

    recognition.onerror = (event) => {
      console.error("Speech recognition error:", event.error);
      speechBtn.style.background = "transparent";
      speechBtn.style.color = "#64748b";
    };

    speechBtn.addEventListener("click", () => {
      recognition.start();
    });
  } else {
    speechBtn.disabled = true;
  }
});

// Auto-resize textarea based on content
function adjustTextareaHeight(textarea) {
  textarea.style.height = "24px";
  textarea.style.height = Math.min(textarea.scrollHeight, 120) + "px";
}

// Add fade out animation
const style = document.createElement("style");
style.textContent = `
  @keyframes fadeOut {
    from { opacity: 1; transform: scale(1); }
    to { opacity: 0; transform: scale(0.95); }
  }
`;
document.head.appendChild(style);
