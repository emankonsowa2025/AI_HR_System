
// =====================
// AskTech Chat Application
// =====================

// ===== Global State =====
let historyEl, messageEl, sendBtn, speechBtn, languageSelect, logoutBtn;
let recognition = null;
let currentLanguage = 'ar-SA'; // Default to Arabic
let isSpeaking = false; // Prevent multiple TTS calls
let isAuthChecked = false; // Prevent multiple auth checks

// =====================
// Text-to-Speech Utilities
// =====================
function sanitizeForSpeech(t) {
    if (!t) return '';
    let s = t;
    s = s.replace(/\*\*(.*?)\*\*/g, '$1');
    s = s.replace(/\*(.*?)\*/g, '$1');
    s = s.replace(/_(.*?)_/g, '$1');
    s = s.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '$1');
    s = s.split(/\r?\n/)
         .map(line => line.replace(/^\s*((?:[-•*])|(?:\d+[\.)]))\s+/, ''))
         .join('\n');
    s = s.replace(/\*/g, '');
    s = s.replace(/^\s*#{1,6}\s+/gm, '');
    s = s.replace(/[ ]{2,}/g, ' ');
    return s.trim();

function speakText(text, lang) {
    if (isSpeaking) {
        console.log('⚠️ Already speaking, ignoring new speech request');
        return;
    }
    const cleanText = sanitizeForSpeech(text);
    if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(cleanText);
        utterance.lang = lang;
        utterance.rate = 0.85;
        utterance.pitch = 1;
        utterance.volume = 1;
        let voices = window.speechSynthesis.getVoices();
        if (lang.startsWith('ar')) {
            const preferredVoices = [
                'Microsoft Hoda - Arabic (Saudi Arabia)',
                'Google Arabic',
                'Arabic Saudi Arabia',
                'ar-SA',
                'ar-EG'
            ];
            let arabicVoice = null;
            for (const preferred of preferredVoices) {
                arabicVoice = voices.find(v => v.name === preferred || v.lang === preferred);
                if (arabicVoice) break;
            }
            if (!arabicVoice) {
                arabicVoice = voices.find(v => v.lang && v.lang.startsWith('ar'));
            }
            if (arabicVoice) utterance.voice = arabicVoice;
        }
        const avatar = document.getElementById('interviewerAvatar');
        utterance.onstart = () => {
            isSpeaking = true;
            if (avatar) avatar.classList.add('speaking');
        };
        utterance.onend = () => {
            isSpeaking = false;
            if (avatar) avatar.classList.remove('speaking');
        };
        utterance.onerror = () => {
            isSpeaking = false;
            if (avatar) avatar.classList.remove('speaking');
        };
        window.speechSynthesis.speak(utterance);
    }
}
}

// Clear chat history on server
async function clearServerHistory() {
    const token = localStorage.getItem('access_token');
    if (!token) {
        console.log('No token found, cannot clear history');
        return false;
    }

    try {
        console.log('🗑️ Clearing server chat history...');
        const response = await fetch('/api/history', {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (response.ok) {
            const data = await response.json();
            console.log('✅ Server history cleared:', data);
            return true;
        } else {
            console.warn('⚠️ Failed to clear server history:', response.status);
            return false;
        }
    } catch (error) {
        console.error('❌ Error clearing server history:', error);
        return false;
    }
}

// Load chat history on page load
async function loadHistory() {
    const token = localStorage.getItem('access_token');
    if (!token) {
        console.log('No token found, redirecting to login...');
        window.location.href = '/login';
        return;
    }

    try {
        console.log('Loading history with token:', token.substring(0, 20) + '...');
        const response = await fetch('/api/history', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        console.log('History response status:', response.status);

        if (response.status === 401 || response.status === 403) {
            // Token expired, invalid, or forbidden
            console.warn('Authentication failed, clearing token and redirecting...');
            localStorage.removeItem('access_token');
            localStorage.removeItem('user');
            window.location.href = '/login';
            return;
        }

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const messages = await response.json();
        
        console.log('Loaded messages:', messages.length);
        historyEl.innerHTML = '';
        messages.forEach(msg => {
            appendMessage(msg.role, msg.text);
        });
        
        // Scroll to bottom
        historyEl.scrollTop = historyEl.scrollHeight;
    } catch (error) {
        console.error('Error loading history:', error);
        appendMessage('system', '❌ Error loading chat history: ' + error.message);
    }
}

// Append message to history
function sanitizeForDisplay(t) {
    if (!t) return '';
    let s = t;
    // Remove markdown bold/italics markers
    s = s.replace(/\*\*(.*?)\*\*/g, '$1');
    s = s.replace(/\*(.*?)\*/g, '$1');
    s = s.replace(/_(.*?)_/g, '$1');
    // Convert markdown links [text](url) -> text
    s = s.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '$1');
    // Strip markdown headings (leading #...)
    s = s.replace(/^\s*#{1,6}\s+/gm, '');
    // Remove any stray asterisks used as bullets
    s = s.replace(/^\s*\*/gm, '');
    // Collapse excessive spaces
    s = s.replace(/[ ]{2,}/g, ' ');
    return s.trim();
}

function createListFromText(text, lang) {
    const raw = text || '';
    const lines = raw.split(/\r?\n/).map(l => l.trim()).filter(Boolean);
    if (lines.length <= 1) return null;

    // Detect if lines are mostly bullets or numbers
    let bulletCount = 0, numberCount = 0;
    lines.forEach(l => {
        if (/^[-*•]\s+/.test(l)) bulletCount++;
        else if (/^\d+[\.)]\s+/.test(l)) numberCount++;
    });

    const useBullets = bulletCount >= numberCount;
    const listEl = document.createElement(useBullets ? 'ul' : 'ol');
    if (lang && lang.startsWith('ar')) {
        listEl.setAttribute('dir', 'rtl');
    }

    lines.forEach(line => {
            let cleaned = line
                .replace(/^\s*((?:[-•*])|(?:\d+[\.)]))\s+/, '') // bullet/number prefix
                .replace(/^\s*#{1,6}\s+/, '')                    // heading markers
                .replace(/\*\*(.*?)\*\*/g, '$1')               // bold
                .replace(/\*(.*?)\*/g, '$1')                     // italics
                .replace(/_(.*?)_/g, '$1')                         // underscore italics
                .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '$1')    // links
                .replace(/\*/g, '');                              // stray asterisks

        cleaned = cleaned.trim();
        if (!cleaned) return;
        const li = document.createElement('li');
        li.textContent = cleaned;
        listEl.appendChild(li);
    });

    return listEl.childElementCount ? listEl : null;
}

function appendMessage(role, text) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${role}`;
    
    // Create message content wrapper
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    const roleLabel = document.createElement('strong');
    roleLabel.textContent = role === 'user' ? 'أنت: ' : 
                           role === 'assistant' ? 'AskTech: ' : 
                           'النظام: ';
    
    // For assistant replies, render as list (bullets or numbers) when multi-line
    const maybeList = role === 'assistant' ? createListFromText(text, currentLanguage) : null;
    if (maybeList) {
        contentDiv.appendChild(roleLabel);
        contentDiv.appendChild(maybeList);
    } else {
        const textSpan = document.createElement('span');
        // Sanitize visible text to remove '*' and '#' markdown symbols
        textSpan.textContent = role === 'assistant' ? sanitizeForDisplay(text) : text;
        contentDiv.appendChild(roleLabel);
        contentDiv.appendChild(textSpan);
    }
    msgDiv.appendChild(contentDiv);
    
    // Add speaker button for assistant messages
    if (role === 'assistant') {
        const speakerBtn = document.createElement('button');
        speakerBtn.className = 'speaker-btn';
        speakerBtn.textContent = '🔊';
        speakerBtn.title = 'استماع للرد';
        speakerBtn.onclick = () => speakText(text, currentLanguage);
        msgDiv.appendChild(speakerBtn);
    }
    
    historyEl.appendChild(msgDiv);
    
    // Scroll to bottom
    historyEl.scrollTop = historyEl.scrollHeight;
    
    // Auto-speak assistant messages if Arabic is selected
    if (role === 'assistant' && currentLanguage.startsWith('ar')) {
        speakText(text, currentLanguage);
    }
}

// Send message
async function sendMessage() {
    const message = messageEl.value.trim();
    if (!message) {
        return;
    }

    // Check token
    const token = localStorage.getItem('access_token');
    if (!token) {
        window.location.href = '/login';
        return;
    }

    // Disable input while processing
    messageEl.disabled = true;
    sendBtn.disabled = true;
    sendBtn.textContent = 'Sending...';

    // Show user message immediately
    appendMessage('user', message);
    messageEl.value = '';

    try {
        console.log('📤 Sending message to /api/chat...');
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ message })
        });

        console.log('📥 Response status:', response.status);

        if (response.status === 401 || response.status === 403) {
            // Token expired or invalid
            console.warn('❌ Authentication failed');
            localStorage.removeItem('access_token');
            localStorage.removeItem('user');
            window.location.href = '/login';
            return;
        }

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
            console.error('❌ Server error:', errorData);
            throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        console.log('✅ Response data:', data);
        
        // Show assistant response
        if (data.messages && data.messages.length > 0) {
            data.messages.forEach(msg => {
                appendMessage(msg.role, msg.text);
            });
        } else {
            console.warn('⚠️ No messages in response');
            appendMessage('system', '⚠️ No response received from server');
        }
    } catch (error) {
        console.error('Error sending message:', error);
        
        // Better error message
        let errorMsg = error.message;
        if (errorMsg.includes('401')) {
            errorMsg = currentLanguage === 'ar-SA' ? 
                'انتهت صلاحية الجلسة. جاري إعادة التوجيه للدخول...' : 
                'Session expired. Redirecting to login...';
            setTimeout(() => {
                localStorage.removeItem('access_token');
                localStorage.removeItem('user');
                window.location.href = '/login';
            }, 2000);
        }
        
        appendMessage('system', '❌ ' + (currentLanguage === 'ar-SA' ? 'خطأ: ' : 'Error: ') + errorMsg);
    } finally {
        // Re-enable input
        messageEl.disabled = false;
        sendBtn.disabled = false;
        sendBtn.textContent = 'Send';
        messageEl.focus();
    }
}

// Initialize application when DOM is loaded
// Force scroll to top before anything else
if (window.history.scrollRestoration) {
    window.history.scrollRestoration = 'manual';
}
window.scrollTo(0, 0);
document.documentElement.scrollTop = 0;

window.addEventListener('DOMContentLoaded', async () => {
    // Prevent multiple executions
    if (isAuthChecked) {
        console.log('⚠️ Auth already checked, skipping...');
        return;
    }
    isAuthChecked = true;
    
    console.log('🚀 Starting app initialization...');
    
    // Set page zoom to 75%
    document.body.style.zoom = "75%";
    
    // Force scroll to top multiple times
    const forceScrollTop = () => {
        window.scrollTo(0, 0);
        window.scrollTo({top: 0, left: 0, behavior: 'instant'});
        document.documentElement.scrollTop = 0;
        document.body.scrollTop = 0;
    };
    
    forceScrollTop();
    
    // Check if we should scroll to top (coming from service pages or login)
    if (sessionStorage.getItem('scrollToTop') === 'true') {
        sessionStorage.removeItem('scrollToTop');
        // Force scroll multiple times with delays
        setTimeout(forceScrollTop, 50);
        setTimeout(forceScrollTop, 150);
        setTimeout(forceScrollTop, 300);
        console.log('✅ Scrolled to top of main page');
    }
    console.log('✅ Page zoom set to 75%');
    
    // Check authentication first
    const token = localStorage.getItem('access_token');
    console.log('🔑 Token check:', token ? 'Found' : 'Not found');

    if (!token) {
        console.log('❌ No token, redirecting to welcome page...');
        localStorage.clear(); // Clear everything
        window.location.replace('/'); // Redirect to welcome page
        return;
    }

    // Validate token with server
    console.log('🔍 Validating token with server...');
    try {
        const response = await fetch('/api/auth/me', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (!response.ok) {
            console.log('❌ Token invalid (status: ' + response.status + ')');
            localStorage.clear();
            window.location.replace('/login');
            return;
        }
        
        const userData = await response.json();
        console.log('✅ User authenticated:', userData.username);
        
        // Update username in navbar
        const usernameEl = document.getElementById('username');
        if (usernameEl) {
            usernameEl.textContent = userData.username;
            console.log('✅ Username updated in UI');
        }
    } catch (error) {
        console.error('❌ Auth check failed:', error);
        localStorage.clear();
        window.location.replace('/login');
        return;
    }

    // Clear server history without reload
    console.log('🗑️ Clearing server history...');
    try {
        await fetch('/api/history', {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${token}` }
        });
        console.log('✅ History cleared');
    } catch (error) {
        console.error('⚠️ Error clearing history:', error);
    }
    
    console.log('✅ Initializing app components...');
    
    // Initialize DOM elements
    historyEl = document.getElementById('history');
    messageEl = document.getElementById('message');
    sendBtn = document.getElementById('send');
    speechBtn = document.getElementById('speech');
    languageSelect = document.getElementById('language');
    logoutBtn = document.getElementById('logoutBtn');
    // Menu items
    const menuInterview = document.getElementById('menuInterview');
    const menuRequirements = document.getElementById('menuRequirements');
    const menuTopJobs = document.getElementById('menuTopJobs');
    
    // Initialize speech recognition
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = currentLanguage;

        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            messageEl.value = transcript;
            speechBtn.textContent = '🎤';
        };

        recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            speechBtn.textContent = '🎤';
            alert('خطأ في التعرف على الصوت: ' + event.error);
        };

        recognition.onend = () => {
            speechBtn.textContent = '🎤';
        };
    } else if (speechBtn) {
        speechBtn.disabled = true;
        speechBtn.title = 'التعرف على الصوت غير مدعوم في هذا المتصفح';
    }
    
    // Event listeners
    if (sendBtn) {
        sendBtn.addEventListener('click', sendMessage);
    }

    if (messageEl) {
        messageEl.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    }

    if (speechBtn) {
        speechBtn.addEventListener('click', () => {
            if (!recognition) {
                alert('التعرف على الصوت غير مدعوم في هذا المتصفح');
                return;
            }

            if (speechBtn.textContent === '🎤') {
                try {
                    recognition.start();
                    speechBtn.textContent = '🔴';
                } catch (error) {
                    console.error('Error starting speech recognition:', error);
                    alert('خطأ في بدء التعرف على الصوت: ' + error.message);
                }
            } else {
                recognition.stop();
                speechBtn.textContent = '🎤';
            }
        });
    }

    // Menu actions: redirect to dedicated pages
    const menuCareerPath = document.getElementById('menuCareerPath');
    const menuSkillsGap = document.getElementById('menuSkillsGap');
    const menuMockInterview = document.getElementById('menuMockInterview');
    const menuResumeBuilder = document.getElementById('menuResumeBuilder');
    
    if (menuCareerPath) {
        menuCareerPath.addEventListener('click', () => {
            window.location.href = '/career-path';
        });
    }
    if (menuSkillsGap) {
        menuSkillsGap.addEventListener('click', () => {
            window.location.href = '/skills-gap';
        });
    }
    if (menuMockInterview) {
        menuMockInterview.addEventListener('click', async () => {
            console.log('🎭 Mock Interview button clicked - opening video modal');
            const success = await openVideoModal();
            if (success) {
                console.log('✅ Video modal opened, auto-starting interview...');
                // Auto-start the interview after a brief delay
                setTimeout(() => {
                    if (startInterviewBtn) {
                        console.log('🎬 Auto-starting mock interview');
                        startInterviewBtn.click();
                    } else {
                        console.error('❌ Start interview button not found');
                    }
                }, 500);
            }
        });
    }
    if (menuResumeBuilder) {
        menuResumeBuilder.addEventListener('click', () => {
            window.location.href = '/resume-builder';
        });
    }
    if (menuInterview) {
        menuInterview.addEventListener('click', () => {
            window.location.href = '/interview';
        });
    }
    if (menuRequirements) {
        menuRequirements.addEventListener('click', () => {
            window.location.href = '/requirements';
        });
    }
    if (menuTopJobs) {
        menuTopJobs.addEventListener('click', () => {
            window.location.href = '/top-jobs';
        });
    }
    
    // Language change handler
    if (languageSelect) {
        languageSelect.addEventListener('change', (e) => {
            currentLanguage = e.target.value;
            if (recognition) {
                recognition.lang = currentLanguage;
            }
            
            // Update HTML direction for RTL/LTR
            const html = document.documentElement;
            const welcomeText = document.getElementById('welcomeText');
            const user = JSON.parse(localStorage.getItem('user') || '{}');
            
            if (currentLanguage.startsWith('ar')) {
                html.setAttribute('dir', 'rtl');
                html.setAttribute('lang', 'ar');
                messageEl.placeholder = 'اسألني عن المهارات، الوظائف، أو التحضير للمقابلات...';
                sendBtn.textContent = 'إرسال';
                speechBtn.title = 'إدخال صوتي';
                if (logoutBtn) {
                    logoutBtn.textContent = '🚪 خروج';
                    logoutBtn.title = 'تسجيل الخروج';
                }
                if (welcomeText && user.username) {
                    welcomeText.innerHTML = `مرحباً، <strong id="username">${user.username}</strong>`;
                }
            } else {
                html.setAttribute('dir', 'ltr');
                html.setAttribute('lang', 'en');
                messageEl.placeholder = 'Ask me about skills, job roles, or interview preparation...';
                sendBtn.textContent = 'Send';
                speechBtn.title = 'Speech input';
                if (logoutBtn) {
                    logoutBtn.textContent = '🚪 Logout';
                    logoutBtn.title = 'Logout';
                }
                if (welcomeText && user.username) {
                    welcomeText.innerHTML = `Welcome, <strong id="username">${user.username}</strong>`;
                }
            }
            
            console.log('Language changed to:', currentLanguage);
        });
    }
    
    // Display user info
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    const usernameEl = document.getElementById('username');
    if (user.username && usernameEl) {
        usernameEl.textContent = user.username;
    } else {
        console.warn('No user info found in localStorage');
    }
    
    // Setup logout handler
    if (logoutBtn) {
        logoutBtn.addEventListener('click', async () => {
            const confirmed = confirm(currentLanguage === 'ar-SA' ? 
                'هل تريد تسجيل الخروج؟' : 
                'Are you sure you want to logout?'
            );
            if (confirmed) {
                // Clear chat history on server
                await clearServerHistory();
                
                // Clear chat history from UI
                if (historyEl) {
                    historyEl.innerHTML = '';
                }
                
                // Remove authentication tokens
                localStorage.removeItem('access_token');
                localStorage.removeItem('user');
                
                // Redirect to login
                window.location.href = '/login';
            }
        });
    }
    
    // Clear old chat on fresh page load (new session)
    const sessionKey = 'chat_session_loaded';
    const sessionLoaded = sessionStorage.getItem(sessionKey);
    
    if (!sessionLoaded) {
        // First load in this session - clear both client and server chat
        console.log('🆕 New session detected - clearing old chat');
        if (historyEl) {
            historyEl.innerHTML = '';
        }
        // Clear server-side history
        clearServerHistory().then(() => {
            console.log('✅ Chat cleared for new session');
            // Load fresh history (should be empty)
            loadHistory();
        });
        // Mark session as loaded
        sessionStorage.setItem(sessionKey, 'true');
    } else {
        // Existing session - just load history
        loadHistory();
    }
    
    // Focus on message input
    if (messageEl) {
        messageEl.focus();
    }
    
    // Load voices for speech synthesis
    if ('speechSynthesis' in window) {
        // Trigger voice loading
        window.speechSynthesis.getVoices();
        
        window.speechSynthesis.onvoiceschanged = () => {
            const voices = window.speechSynthesis.getVoices();
            const arabicVoices = voices.filter(v => v.lang.startsWith('ar'));
            console.log('🎤 Available Arabic voices:', arabicVoices.length);
            arabicVoices.forEach(v => console.log(`  - ${v.name} (${v.lang})`));
            
            if (arabicVoices.length === 0) {
                console.warn('⚠️ No Arabic voices found. Speech output may not work correctly.');
            }
        };
        
        // Trigger the event
        window.speechSynthesis.getVoices();
    }

    // ==============================================
    // VIDEO INTERVIEW FEATURE
    // ==============================================
    const videoInterviewBtn = document.getElementById('startVideoInterview');
    const videoModal = document.getElementById('videoModal');
    const userVideo = document.getElementById('userVideo');
    const startInterviewBtn = document.getElementById('startInterview');
    const nextQuestionBtn = document.getElementById('nextQuestion');
    const endInterviewBtn = document.getElementById('endInterview');
    const interviewQuestion = document.getElementById('interviewQuestion');
    const interviewerVideo = document.getElementById('interviewerVideo');
    const interviewerPhoto = document.getElementById('interviewerPhoto');

    console.log('🔍 Video interview elements:', {
        btn: videoInterviewBtn,
        modal: videoModal,
        video: userVideo,
        start: startInterviewBtn,
        next: nextQuestionBtn,
        end: endInterviewBtn,
        question: interviewQuestion,
        avatarVideo: interviewerVideo,
        avatarImg: interviewerPhoto
    });

    // Interview state variables (redeclared cleanly after patch fix)
    let mediaStream = null;
    let currentQuestionIndex = 0;
    let interviewActive = false;
    // 'idle' | 'followups' | 'evaluation' | 'done'
    let interviewPhase = 'idle';
    let skillsAnswer = '';
    let jobTitleAnswer = '';
    let followUpQuestions = [];
    let followUpAnswers = [];
    let currentFollowUpIndex = 0;
    let followUpAwaitTimer = null;
    let followUpAwaitAttempts = 0;

    // Start interview directly with evaluation questions
    if (startInterviewBtn) {
        startInterviewBtn.addEventListener('click', async () => {
            console.log('🎬 Starting interview (skills question first)...');
            interviewActive = true;
            interviewPhase = 'skills';
            skillsAnswer = '';
            followUpQuestions = [];
            followUpAnswers = [];
            currentFollowUpIndex = 0;
            startInterviewBtn.style.display = 'none';
            if (nextQuestionBtn) nextQuestionBtn.style.display = 'none';

            interviewQuestion.textContent = '💬 السؤال الأول: المهارات والوظيفة الحالية';
            const firstQuestion = 'في البداية، أرجو منكِ التكرُّم بعرض مهاراتكِ الأساسية ووظيفتكِ الحالية، أو المُسمّى الوظيفي الذي تطمحين للحصول عليه. ما هو المجال المهني الذي تعملين فيه؟';
            appendTranscript('assistant', firstQuestion);

            // Ensure clean audio state
            if (recognition) { try { recognition.stop(); } catch {} }
            if (window.speechSynthesis) { try { window.speechSynthesis.cancel(); } catch {} }

            // Speak the first skills question and start listening
            if ('speechSynthesis' in window) {
                const utterance = new SpeechSynthesisUtterance(firstQuestion);
                utterance.lang = currentLanguage;
                utterance.rate = 0.9;
                
                let voices = window.speechSynthesis.getVoices();
                if (currentLanguage.startsWith('ar')) {
                    const arV = voices.find(v => v.lang.startsWith('ar'));
                    if (arV) utterance.voice = arV;
                }
                
                utterance.onstart = () => { 
                    isSpeaking = true; 
                    setSpeakingState(true); 
                };
                
                utterance.onend = () => {
                    isSpeaking = false;
                    setSpeakingState(false);
                    setTimeout(() => { 
                        if (interviewActive) startLiveListening(); 
                    }, 800);
                };
                
                utterance.onerror = () => {
                    isSpeaking = false;
                    setSpeakingState(false);
                    setTimeout(() => { 
                        if (interviewActive) startLiveListening(); 
                    }, 800);
                };
                
                window.speechSynthesis.speak(utterance);
            }
        });
    }

    // Helper function to open video modal with camera
    async function openVideoModal() {
        console.log('🎥 Opening video interview modal...');
        
        // Stop any existing recognition
        if (recognition) {
            try { recognition.stop(); } catch {}
        }
        
        try {
            // Request camera access
            mediaStream = await navigator.mediaDevices.getUserMedia({ 
                video: true, 
                audio: false // use Web Speech API for mic; avoid device busy conflicts
            });
            
            // Display user's video
            userVideo.srcObject = mediaStream;
            
            // Show modal
            videoModal.classList.add('active');

            // Attempt to load a looping avatar animation video if provided later
            if (interviewerVideo) {
                // Placeholder: you can replace with a hosted looping mp4/webm clip
                // For now we keep it hidden unless a source is dynamically set
                if (!interviewerVideo.src) {
                    // Future: interviewerVideo.src = '/static/interviewer_loop.mp4';
                }
                interviewerVideo.addEventListener('error', () => {
                    interviewerVideo.hidden = true;
                    if (interviewerPhoto) interviewerPhoto.hidden = false;
                });
            }
            
            // Reset interview state completely
            currentQuestionIndex = 0;
            interviewActive = false;
            isSpeaking = false;
            
            // Reset UI
            interviewQuestion.textContent = 'مرحباً! أنا أى تى أى 👋 اضغط "ابدأ المقابلة" للبدء. قل "exit" أو "إيقاف" لإيقاف الحديث.';
            startInterviewBtn.style.display = 'inline-block';
            if (nextQuestionBtn) nextQuestionBtn.style.display = 'none';
            setSpeakingState(false);
            
            // Clear transcript except system message
            if (transcriptEl) {
                transcriptEl.innerHTML = '<div class="t-row system">💬 سيظهر هنا نص المحادثة. يمكنك قول "exit" أو "إيقاف" لإيقاف الحديث في أي وقت.</div>';
            }
            
            console.log('✅ Camera access granted, modal ready');
            return true;
        } catch (error) {
            console.error('❌ Camera access denied:', error);
            alert('يرجى السماح بالوصول إلى الكاميرا والميكروفون لبدء المقابلة\n\nPlease allow camera and microphone access to start the interview');
            return false;
        }
    }

    // Open video modal and request camera (regular interview)
    if (videoInterviewBtn) {
        // No event listener needed for videoInterviewBtn; now opens a new page via anchor link
    }

    // Open video modal and start evaluation directly
    const startEvaluationBtn = document.getElementById('startEvaluationInterview');
    console.log('🔍 Evaluation button found:', startEvaluationBtn);
    if (startEvaluationBtn) {
        startEvaluationBtn.addEventListener('click', async () => {
            console.log('⭐ Evaluation button clicked!');
            const success = await openVideoModal();
            if (success) {
                console.log('✅ Modal opened, auto-starting interview...');
                // Auto-click the start interview button to begin evaluation
                setTimeout(() => {
                    if (startInterviewBtn) {
                        console.log('🎬 Clicking start interview button');
                        startInterviewBtn.click();
                    } else {
                        console.error('❌ Start interview button not found');
                    }
                }, 500);
            }
        });
    } else {
        console.error('❌ Evaluation button not found in DOM');
    }



    // Next question (hidden in live mode, kept for future)
    if (nextQuestionBtn) {
        nextQuestionBtn.addEventListener('click', () => {
            // no-op in live mode
        });
    }

    // End interview and close modal
    if (endInterviewBtn) {
        endInterviewBtn.addEventListener('click', () => {
            closeVideoInterview();
        });
    }

    // Close modal button (X button)
    const closeModalBtn = document.getElementById('closeModalBtn');
    if (closeModalBtn) {
        closeModalBtn.addEventListener('click', () => {
            closeVideoInterview();
        });
    }

    // Live listening helpers
    const transcriptEl = document.getElementById('interviewTranscript');

    function appendTranscript(role, text) {
        if (!transcriptEl) return;
        const row = document.createElement('div');
        row.className = `t-row ${role}`;
        // Prefer list rendering for assistant
        if (role === 'assistant') {
            const maybeList = createListFromText(text, currentLanguage);
            if (maybeList) {
                row.appendChild(maybeList);
            } else {
                row.textContent = sanitizeForDisplay(text);
            }
        } else {
            row.textContent = text;
        }
        transcriptEl.appendChild(row);
        transcriptEl.scrollTop = transcriptEl.scrollHeight;
    }

    function setSpeakingState(on) {
        const avatar = document.getElementById('interviewerAvatar');
        if (!avatar) return;
        if (on) {
            avatar.classList.add('speaking');
        } else {
            avatar.classList.remove('speaking');
        }
    }

    function startLiveListening() {
        console.log('🎤 startLiveListening called');
        if (!recognition) {
            console.error('❌ No recognition object available');
            alert('التعرف على الصوت غير مدعوم في هذا المتصفح');
            return;
        }
        
        // Stop any existing recognition first
        try { 
            recognition.stop(); 
            console.log('🛑 Stopped existing recognition');
        } catch (e) {
            console.log('ℹ️ No recognition to stop');
        }
        
        // Wait a moment then start fresh
        setTimeout(() => {
            try {
                recognition.continuous = false; // Only listen once per question
                recognition.interimResults = false;
                recognition.lang = currentLanguage;
                recognition.start();
                console.log('🎧 ✅ Listening started for one answer (single mode)');
                interviewQuestion.textContent = '🎙️ أنا في حالة استماع، تفضّلي بالحديث.';
            } catch (e) {
                console.error('❌ Error starting recognition:', e);
                interviewQuestion.textContent = '❌ خطأ تقني في بدء الاستماع: ' + e.message;
            }
        }, 500); // Increased delay to 500ms
        // Start interview: app leads by asking for domain/category first
        if (startInterviewBtn) {
            startInterviewBtn.addEventListener('click', async () => {
                console.log('🎬 Starting interview (domain/category first)...');
                interviewActive = true;
                interviewPhase = 'domain';
                skillsAnswer = '';
                jobTitleAnswer = '';
                followUpQuestions = [];
                followUpAnswers = [];
                currentFollowUpIndex = 0;
                startInterviewBtn.style.display = 'none';
                if (nextQuestionBtn) nextQuestionBtn.style.display = 'none';

                interviewQuestion.textContent = '💬 السؤال الأول: ما هو المجال أو التخصص الذي ترغب في إجراء المقابلة حوله؟';
                const firstQuestion = 'في البداية، ما هو المجال أو التخصص الذي ترغب في إجراء المقابلة حوله؟';
                appendTranscript('assistant', firstQuestion);

                // Ensure clean audio state
                if (recognition) { try { recognition.stop(); } catch {} }
                if (window.speechSynthesis) { try { window.speechSynthesis.cancel(); } catch {} }

                // Speak the first domain question and start listening
                if ('speechSynthesis' in window) {
                    const utterance = new SpeechSynthesisUtterance(firstQuestion);
                    utterance.lang = currentLanguage;
                    utterance.rate = 0.9;
                    let voices = window.speechSynthesis.getVoices();
                    if (currentLanguage.startsWith('ar')) {
                        const arV = voices.find(v => v.lang.startsWith('ar'));
                        if (arV) utterance.voice = arV;
                    }
                    utterance.onstart = () => { 
                        isSpeaking = true; 
                        setSpeakingState(true); 
                    };
                    utterance.onend = () => {
                        isSpeaking = false;
                        setSpeakingState(false);
                        setTimeout(() => { 
                            if (interviewActive) startLiveListening(); 
                        }, 800);
                    };
                    utterance.onerror = () => {
                        isSpeaking = false;
                        setSpeakingState(false);
                        setTimeout(() => { 
                            if (interviewActive) startLiveListening(); 
                        }, 800);
                    };
                    window.speechSynthesis.speak(utterance);
                }
            });
        }
    }

    async function handleInterviewUtterance(text) {
        const spoken = text.trim();
        if (!spoken) return;
        
    // Global commands
    // Check for exit command - stop speech and restart listening
        if (spoken.toLowerCase() === 'exit' || spoken === 'إيقاف' || spoken === 'توقف') {
            console.log('🛑 Exit command detected, stopping speech');
            
            // Stop any ongoing speech immediately
            if (window.speechSynthesis) {
                window.speechSynthesis.cancel();
            }
            
            // Reset speaking state
            isSpeaking = false;
            setSpeakingState(false);
            
            // Show message and restart listening
            appendTranscript('system', '⏸️ تم إيقاف الحديث. جاهزة للاستماع مرة أخرى.');
            interviewQuestion.textContent = '🎙️ أنا في حالة استماع، تفضّلي بالحديث.';
            
            setTimeout(() => {
                if (interviewActive) {
                    startLiveListening();
                }
            }, 500);
            return;
        }

        // Allow user to force evaluation when in follow-ups
        const evalNow = ['ابدأ التقييم','التقييم','قيّم الآن','ابدئي التقييم','evaluate now','start evaluation'];
        if (evalNow.some(k => spoken.toLowerCase() === k || spoken.includes(k))) {
            if (interviewPhase === 'followups' && followUpAnswers.length > 0) {
                appendTranscript('system', '🔎 بدء التقييم بناءً على الإجابات الحالية.');
                interviewPhase = 'evaluation';
                interviewQuestion.textContent = '⏳ جاري تقييم الإجابات...';
                try {
                    await evaluateFollowUpAnswers();
                    interviewPhase = 'done';
                } catch (e) {
                    console.error('Evaluation error (manual):', e);
                    appendTranscript('system', '❌ حدث خطأ أثناء التقييم.');
                    interviewPhase = 'idle';
                }
            } else {
                appendTranscript('system', 'ℹ️ لا توجد إجابات كافية للتقييم بعد.');
            }
            return;
        }
        
        // Prevent processing if already speaking, except allow follow-up answers so we don't miss them
        if (isSpeaking && interviewPhase !== 'followups') {
            console.log('⚠️ Still speaking, ignoring new input (non-followups phase)');
            return;
        }
        // If we're in follow-ups and TTS is still going, stop TTS to prioritize the user's answer
        if (interviewPhase === 'followups' && isSpeaking) {
            try {
                if (window.speechSynthesis) window.speechSynthesis.cancel();
            } catch {}
            isSpeaking = false;
            setSpeakingState(false);
        }

        // Phase-specific routing
        if (interviewPhase === 'domain') {
            appendTranscript('user', spoken);
            const domain = spoken;
            interviewQuestion.textContent = '⏳ جارٍ إعداد أسئلة المقابلة بناءً على المجال...';
            try {
                // Generate the first question for this domain
                const qs = await generateFollowUpQuestions(domain, '');
                followUpQuestions = qs.slice(0, 5);
                currentFollowUpIndex = 0;
                followUpAnswers = [];
                interviewPhase = 'followups';
                if (!followUpQuestions.length) {
                    appendTranscript('system', '⚠️ لم أتمكن من إعداد أسئلة للمجال المحدد. سنواصل المحادثة المفتوحة.');
                    interviewPhase = 'idle';
                } else {
                    await askFollowUpQuestion(currentFollowUpIndex);
                }
            } catch (e) {
                console.error('Domain-based question generation error:', e);
                appendTranscript('system', '❌ حدث خطأ أثناء إعداد الأسئلة بناءً على المجال. سنواصل المحادثة المفتوحة.');
                interviewPhase = 'idle';
            }
            return;
        }

        if (interviewPhase === 'jobtitle') {
            appendTranscript('user', spoken);
            jobTitleAnswer = spoken;
            interviewQuestion.textContent = '⏳ جاري تحليل الإجابة وتحضير أسئلة تقييم...';
            try {
                const qs = await generateFollowUpQuestions(skillsAnswer, jobTitleAnswer);
                followUpQuestions = qs.slice(0, 5);
                currentFollowUpIndex = 0;
                followUpAnswers = [];
                interviewPhase = 'followups';
                if (!followUpQuestions.length) {
                    appendTranscript('system', '⚠️ لم أتمكن من توليد أسئلة تقييم كافية. سنستمر في محادثة حرة.');
                    interviewPhase = 'idle';
                } else {
                    await askFollowUpQuestion(currentFollowUpIndex);
                }
            } catch (e) {
                console.error('Follow-up generation error:', e);
                appendTranscript('system', '❌ حدث خطأ أثناء توليد أسئلة التقييم. سنستمر في محادثة حرة.');
                interviewPhase = 'idle';
            }
            return;
        }

        if (interviewPhase === 'followups') {
            appendTranscript('user', spoken);
            followUpAnswers.push(spoken);
            // Keep index in sync with answers length (defensive against duplicate callbacks)
            currentFollowUpIndex = followUpAnswers.length;
            console.log(`📝 Collected follow-up answer ${currentFollowUpIndex}/${followUpQuestions.length}`);
            interviewQuestion.textContent = `✅ تم تلقّي الإجابة رقم ${currentFollowUpIndex} من ${followUpQuestions.length}`;
            if (followUpAnswers.length < followUpQuestions.length) {
                await askFollowUpQuestion(currentFollowUpIndex);
            } else {
                // Move to evaluation
                interviewPhase = 'evaluation';
                interviewQuestion.textContent = '⏳ جارٍ تقييم إجاباتكِ وإعداد النتائج...';
                console.log('🔍 Triggering evaluation with payload counts:', {
                    questions: followUpQuestions.length,
                    answers: followUpAnswers.length
                });
                try {
                    await evaluateFollowUpAnswers();
                    interviewPhase = 'done';
                } catch (e) {
                    console.error('Evaluation error:', e);
                    appendTranscript('system', '❌ نعتذر عن حدوث خطأ تقني أثناء عملية التقييم.');
                    interviewPhase = 'idle';
                }
            }
            return;
        }
        
    // Default free chat behavior
    appendTranscript('user', spoken);
    interviewQuestion.textContent = '⏳ جارٍ معالجة استفساركِ وإعداد الرد المناسب...';

        const token = localStorage.getItem('access_token');
        if (!token) {
            window.location.href = '/login';
            return;
        }
    const prefixAr = 'محادثة رسمية: يُرجى تقديم إجابة باللغة العربية الفُصحى بأسلوب مهني محترم، على ألا تتجاوز ثلاث جُمل، مع الحفاظ على الطابع الرسمي. الاستفسار:\n\n';
        const prefixEn = 'Live chat: reply in max 3 short sentences, direct and casual. Question:\n\n';
        const payload = currentLanguage.startsWith('ar') ? (prefixAr + spoken) : (prefixEn + spoken);

        try {
            const resp = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ message: payload })
            });

            if (!resp.ok) {
                const err = await resp.json().catch(() => ({}));
                throw new Error(err.detail || ('HTTP ' + resp.status));
            }
            const data = await resp.json();
            if (data.messages && data.messages.length) {
                const assistantText = data.messages[0].text || '';
                appendTranscript('assistant', assistantText);
                
                    // Speak the response and restart listening when done
                    setSpeakingState(true);
                    isSpeaking = true;
                
                    // Stop recognition while speaking
                    if (recognition) {
                        try { recognition.stop(); } catch {}
                    }
                
                    // Create speech with custom callback to restart listening
                    const cleanText = assistantText.replace(/\*\*(.*?)\*\*/g, '$1').replace(/\*(.*?)\*/g, '$1');
                    if ('speechSynthesis' in window) {
                        window.speechSynthesis.cancel();
                    
                        const utterance = new SpeechSynthesisUtterance(cleanText);
                        utterance.lang = currentLanguage;
                        utterance.rate = 0.85;
                        utterance.pitch = 1;
                        utterance.volume = 1;
                    
                        // Load Arabic voice
                        let voices = window.speechSynthesis.getVoices();
                        if (currentLanguage.startsWith('ar')) {
                            const arabicVoice = voices.find(v => v.lang.startsWith('ar'));
                            if (arabicVoice) utterance.voice = arabicVoice;
                        }
                    
                        utterance.onstart = () => {
                            isSpeaking = true;
                            setSpeakingState(true);
                            console.log('🗣️ AI speaking...');
                        };
                    
                        utterance.onend = () => {
                            console.log('✅ AI finished speaking');
                            isSpeaking = false;
                            setSpeakingState(false);
                            
                            // Restart listening after a short delay
                            setTimeout(() => {
                                console.log('🔄 Attempting to restart listening... interviewActive:', interviewActive);
                                if (interviewActive) {
                                    console.log('📢 Calling startLiveListening()');
                                    startLiveListening();
                                } else {
                                    console.log('⚠️ Interview not active, skipping restart');
                                }
                            }, 1000); // Increased delay to 1 second
                        };
                    
                        utterance.onerror = (event) => {
                            console.error('❌ Speech error:', event.error);
                            isSpeaking = false;
                            setSpeakingState(false);
                            
                            // Always try to restart on error
                            setTimeout(() => {
                                console.log('🔄 Restarting after speech error...');
                                if (interviewActive) {
                                    startLiveListening();
                                }
                            }, 1000);
                        };
                    
                        window.speechSynthesis.speak(utterance);
                        interviewQuestion.textContent = '🗣️ جارٍ إلقاء الرد...';
                        
                        // Safety fallback: restart listening after 20 seconds if utterance callbacks don't fire
                        setTimeout(() => {
                            if (isSpeaking && interviewActive) {
                                console.warn('⚠️ Safety timeout: TTS took too long, forcing restart');
                                isSpeaking = false;
                                setSpeakingState(false);
                                startLiveListening();
                            }
                        }, 20000);
                    }
            } else {
                appendTranscript('system', '⚠️ لم يتم استلام رد من الخادم');
                console.log('⚠️ No response from server, restarting listening...');
                // No response, restart listening
                setTimeout(() => {
                    if (interviewActive) {
                        startLiveListening();
                    }
                }, 1000);
            }
        } catch (err) {
            console.error('Interview chat error:', err);
            appendTranscript('system', '❌ خطأ: ' + err.message);
            interviewQuestion.textContent = '🎙️ حاول مرة أخرى.';
        }
    }

    // Function to close video interview
    function closeVideoInterview() {
        console.log('🛑 Closing video interview...');
        
        // Stop camera stream
        if (mediaStream) {
            mediaStream.getTracks().forEach(track => track.stop());
            mediaStream = null;
        }
        
        // Stop speech recognition
        if (recognition) {
            try { recognition.stop(); } catch {}
        }
        
        // Stop any ongoing speech
        if (window.speechSynthesis) {
            window.speechSynthesis.cancel();
        }
        
        // Hide modal
        videoModal.classList.remove('active');
        
        // Reset all state
        interviewActive = false;
        currentQuestionIndex = 0;
        isSpeaking = false;
        setSpeakingState(false);
        
        // Reset UI
        if (startInterviewBtn) startInterviewBtn.style.display = 'inline-block';
        
        console.log('✅ Video interview closed and reset');
    }

    // Close modal when clicking outside
    if (videoModal) {
        videoModal.addEventListener('click', (e) => {
            if (e.target === videoModal) {
                closeVideoInterview();
            }
        });
    }

    // Hook into global speech recognition callbacks for live mode
    if (recognition) {
        const originalOnResult = recognition.onresult;
        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            if (interviewActive && videoModal && videoModal.classList.contains('active')) {
                // In live mode: stop recognition to avoid duplicate triggers, then process
                try { recognition.stop(); } catch {}
                handleInterviewUtterance(transcript);
            } else {
                // Fallback to original behavior (fill message box)
                if (messageEl) messageEl.value = transcript;
                if (speechBtn) speechBtn.textContent = '🎤';
                if (typeof originalOnResult === 'function') {
                    try { originalOnResult(event); } catch {}
                }
            }
        };

        const originalOnEnd = recognition.onend;
        recognition.onend = () => {
            console.log('🔚 recognition.onend fired. interviewActive:', interviewActive, 'isSpeaking:', isSpeaking);
            
            if (interviewActive && videoModal && videoModal.classList.contains('active')) {
                // Auto-restart listening when not currently speaking (covers silence timeouts)
                setTimeout(() => {
                    console.log('⏱️ onend timeout fired. Checking conditions...');
                    console.log('   interviewActive:', interviewActive);
                    console.log('   isSpeaking:', isSpeaking);
                    
                    if (interviewActive && !isSpeaking) {
                        console.log('🔄 Conditions met, restarting recognition...');
                        try {
                            recognition.continuous = true;
                            recognition.interimResults = false;
                            recognition.lang = currentLanguage;
                            recognition.start();
                            console.log('✅ Recognition restarted from onend');
                            if (interviewQuestion) interviewQuestion.textContent = '🎙️ أنا في حالة استماع، تفضّلي بالحديث.';
                        } catch (e) {
                            console.error('❌ Failed to restart recognition:', e);
                            if (interviewQuestion) interviewQuestion.textContent = '❌ خطأ تقني في إعادة تشغيل الاستماع: ' + e.message;
                        }
                    } else {
                        console.log('⏸️ Not restarting - speaking:', isSpeaking, 'or interview inactive:', !interviewActive);
                    }
                }, 800); // Increased delay
            } else {
                if (speechBtn) speechBtn.textContent = '🎤';
                if (typeof originalOnEnd === 'function') {
                    try { originalOnEnd(); } catch {}
                }
            }
        };

        // Add error handler
        recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            if (interviewActive && videoModal && videoModal.classList.contains('active')) {
                if (event.error === 'no-speech') {
                    console.log('No speech detected, continuing...');
                    interviewQuestion.textContent = '🎙️ لم يتم التقاط أي صوت، يُرجى المحاولة مرة أخرى.';
                } else if (event.error === 'aborted') {
                    console.log('Recognition aborted');
                } else {
                    interviewQuestion.textContent = '⚠️ خطأ: ' + event.error;
                }
            }
        };
    }

    console.log('✨ Video interview initialized');
});

// =====================
// Interview helpers
// =====================

async function generateFollowUpQuestions(skillsText, jobTitleText) {
    const token = localStorage.getItem('access_token');
    if (!token) throw new Error('No token');

    const systemAr = `أنتَ مُقيِّم مُحترف للمقابلات الوظيفية. استناداً إلى المعلومات المُقدَّمة من المُرشّحة:

المهارات والخبرات:
"""
${skillsText}
"""

المُسمّى الوظيفي المُستهدَف:
"""
${jobTitleText}
"""

في حالة عدم ذكر المُسمّى الوظيفي أو كان فارغاً، يُرجى استنتاج المُسمّى الوظيفي المناسب من المهارات والخبرات المذكورة أعلاه.

مَهمّتك: قم بإعداد خمسة أسئلة تقييم دقيقة ومُحكَمة تقيس مدى مُلاءمة المُرشّحة للمُسمّى الوظيفي المُستهدَف. يُرجى التركيز على:
• الخبرة العملية الفعلية والإنجازات
• التطبيق الميداني للمهارات
• المواقف السلوكية المهنية
• القدرة على حل المشكلات
• التعامل مع التحديات الواقعية

يُرجى صياغة الأسئلة باللغة العربية الفُصحى بأسلوب رسمي ومهني راقٍ.

يُرجى إرجاع النتيجة بصيغة JSON حصرياً، دون أي نصوص توضيحية إضافية، على النحو التالي:
{"questions": ["سؤال 1","سؤال 2","سؤال 3","سؤال 4","سؤال 5"]}`;

    const resp = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ message: systemAr })
    });
    if (!resp.ok) throw new Error('HTTP ' + resp.status);
    const data = await resp.json();
    const text = (data.messages && data.messages[0] && data.messages[0].text) || '';
    try {
        const parsed = JSON.parse(extractJson(text));
        if (parsed && Array.isArray(parsed.questions)) return parsed.questions;
    } catch (e) {
        console.warn('JSON parse failed for follow-ups, attempting line extraction');
        const lines = text.split(/\r?\n/).map(s => s.replace(/^[-*•\d\.)\s]+/, '').trim()).filter(Boolean);
        return lines.slice(0, 5);
    }
    return [];
}

async function askFollowUpQuestion(index) {
    if (!Array.isArray(followUpQuestions) || index >= followUpQuestions.length) return;
    const q = followUpQuestions[index];
    appendTranscript('assistant', q);
    interviewQuestion.textContent = '💬 سؤال التقييم رقم (' + (index + 1) + '/' + followUpQuestions.length + ')';

    // Clear any existing wait timer
    if (followUpAwaitTimer) {
        clearTimeout(followUpAwaitTimer);
        followUpAwaitTimer = null;
    }
    followUpAwaitAttempts = 0;

    // Set a watchdog timer: if no new answer arrives in 60s, re-ask
    followUpAwaitTimer = setTimeout(() => {
        if (interviewPhase === 'followups' && followUpAnswers.length === index) {
            followUpAwaitAttempts += 1;
            const retryMsg = '🔁 لم يتم تلقّي إجابة، سأُعيد طرح السؤال: ' + q;
            appendTranscript('system', retryMsg);
            console.log('⏰ Follow-up watchdog fired. attempt=', followUpAwaitAttempts);
            // Re-speak question
            if ('speechSynthesis' in window) {
                window.speechSynthesis.cancel();
                const utter = new SpeechSynthesisUtterance(q);
                utter.lang = currentLanguage;
                utter.onend = () => { setTimeout(() => { if (interviewActive) startLiveListening(); }, 500); };
                utter.onerror = () => { setTimeout(() => { if (interviewActive) startLiveListening(); }, 500); };
                window.speechSynthesis.speak(utter);
            }
        }
    }, 60000);

    // Speak and resume listening using the same TTS pipeline used for assistant
    if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(q);
        utterance.lang = currentLanguage;
        utterance.rate = 0.9;
        utterance.pitch = 1;
        let voices = window.speechSynthesis.getVoices();
        if (currentLanguage.startsWith('ar')) {
            const arV = voices.find(v => v.lang.startsWith('ar'));
            if (arV) utterance.voice = arV;
        }
        utterance.onstart = () => { isSpeaking = true; setSpeakingState(true); };
        utterance.onend = () => {
            isSpeaking = false; setSpeakingState(false);
            setTimeout(() => { if (interviewActive) startLiveListening(); }, 800);
        };
        utterance.onerror = () => {
            isSpeaking = false; setSpeakingState(false);
            setTimeout(() => { if (interviewActive) startLiveListening(); }, 800);
        };
        window.speechSynthesis.speak(utterance);
    }
}

async function evaluateFollowUpAnswers() {
    const token = localStorage.getItem('access_token');
    if (!token) throw new Error('No token');

    const payload = {
        questions: followUpQuestions,
        answers: followUpAnswers
    };
    const instrAr = `أنت مُقيِّم مقابلات. قيِّم مدى مُلاءمة كل إجابة لسؤالها (تشابه المعنى والدقة المهنية) بدرجة من 1 إلى 10، حيث 1 = تشابه ضعيف جداً، 10 = تشابه عالٍ جداً.
أرجِع JSON فقط بالشكل:
{"scores":[{"question":"...","answer":"...","score":7,"justification":"سبب مختصر"},...],"average":7.2}`;

    const message = instrAr + '\n\nالبيانات المطلوب تقييمها:\n' + JSON.stringify(payload, null, 2);
    const resp = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ message })
    });
    if (!resp.ok) throw new Error('HTTP ' + resp.status);
    const data = await resp.json();
    const text = (data.messages && data.messages[0] && data.messages[0].text) || '';
    let result = null;
    try {
        result = JSON.parse(extractJson(text));
    } catch (e) {
        console.warn('Evaluation JSON parse failed, raw text shown');
        appendTranscript('system', 'نتيجة التقييم (نص خام):\n' + text);
        return;
    }

    if (!result || !Array.isArray(result.scores)) {
        appendTranscript('system', '⚠️ تعذر تفسير نتيجة التقييم.');
        return;
    }

    // Render detailed scores for each question-answer pair
    let detailedResults = '📊 نتائج التقييم التفصيلية:\n\n';
    result.scores.forEach((s, i) => {
        detailedResults += `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n`;
        detailedResults += `السؤال ${i+1}: ${sanitizeForDisplay(s.question || followUpQuestions[i] || '')}\n\n`;
        detailedResults += `إجابتك: ${sanitizeForDisplay(s.answer || followUpAnswers[i] || '')}\n\n`;
        detailedResults += `⭐ الدرجة المُحرَزة: ${s.score}/10\n`;
        detailedResults += `💡 التقييم: ${sanitizeForDisplay(s.justification || 'لا يوجد تعليق')}\n\n`;
    });
    appendTranscript('assistant', detailedResults);

    // Calculate and display final summary
    const avg = typeof result.average === 'number' ? result.average : (result.scores.reduce((a, s) => a + (s.score || 0), 0) / result.scores.length);
    const totalPoints = result.scores.reduce((a, s) => a + (s.score || 0), 0);
    const maxPoints = result.scores.length * 10;
    
    let performanceLevel = '';
    if (avg >= 9) performanceLevel = 'ممتاز جداً 🌟';
    else if (avg >= 8) performanceLevel = 'ممتاز 👏';
    else if (avg >= 7) performanceLevel = 'جيد جداً ✨';
    else if (avg >= 6) performanceLevel = 'جيد 👍';
    else if (avg >= 5) performanceLevel = 'مقبول ⚡';
    else performanceLevel = 'يحتاج إلى تحسين 💪';
    
    const summary = `
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 التقييم النهائي:

📈 المجموع الكلي: ${totalPoints} من ${maxPoints} نقطة
📊 المعدل العام: ${avg.toFixed(1)}/10
🏆 مستوى الأداء: ${performanceLevel}

${avg >= 7 ? '✅ أداء متميز! نُهنئكِ على مستواكِ المهني الراقي.' : '💡 نوصي بالتركيز على تطوير المهارات في الجوانب التي حصلتِ فيها على درجات أقل.'}

شكراً لإكمالكِ التقييم الذاتي! 🙏
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`;
    
    appendTranscript('assistant', summary);

    // Speak comprehensive summary
    setSpeakingState(true);
    const spokenSummary = `انتهى التقييم. حصلتِ على معدل ${avg.toFixed(1)} من 10 نقاط. ${avg >= 7 ? 'أداء متميز! نُهنئكِ على مستواكِ المهني.' : 'نوصي بتطوير المهارات في الجوانب التي حصلتِ فيها على درجات أقل.'} شكراً لإكمالكِ التقييم.`;
    
    if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(spokenSummary);
        utterance.lang = currentLanguage;
        let voices = window.speechSynthesis.getVoices();
        if (currentLanguage.startsWith('ar')) {
            const arV = voices.find(v => v.lang.startsWith('ar'));
            if (arV) utterance.voice = arV;
        }
        utterance.onstart = () => { isSpeaking = true; setSpeakingState(true); };
        utterance.onend = () => { isSpeaking = false; setSpeakingState(false); setTimeout(() => { if (interviewActive) startLiveListening(); }, 800); };
        utterance.onerror = () => { isSpeaking = false; setSpeakingState(false); setTimeout(() => { if (interviewActive) startLiveListening(); }, 800); };
        window.speechSynthesis.speak(utterance);
    }
}

// Safely extract first JSON block from a text that may contain prose
function extractJson(text) {
    const start = text.indexOf('{');
    const end = text.lastIndexOf('}');
    if (start !== -1 && end !== -1 && end > start) {
        return text.slice(start, end + 1);
    }
    return text; // fallback
}

// Add window load event to ensure scroll after everything is loaded
window.addEventListener('load', () => {
    const forceScrollTop = () => {
        window.scrollTo(0, 0);
        window.scrollTo({top: 0, left: 0, behavior: 'instant'});
        document.documentElement.scrollTop = 0;
        document.body.scrollTop = 0;
    };
    
    // Force scroll on load
    forceScrollTop();
    
    // Extra scroll if coming from login or service pages
    if (sessionStorage.getItem('scrollToTop') === 'true') {
        setTimeout(forceScrollTop, 100);
        setTimeout(forceScrollTop, 300);
    }
});
