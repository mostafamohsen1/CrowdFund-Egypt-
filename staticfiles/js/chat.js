/* --------------------------------------------------------------------------
 * CrowdFund Egypt - Generative AI Chatbot Controller
 * -------------------------------------------------------------------------- */

document.addEventListener('DOMContentLoaded', function () {
    const launcherBtn = document.getElementById('cf-chat-toggle-btn');
    const chatWindow = document.getElementById('cf-chat-window');
    const closeBtn = document.getElementById('cf-chat-close-btn');
    const clearBtn = document.getElementById('cf-chat-clear-btn');
    const chatForm = document.getElementById('cf-chat-form');
    const chatInput = document.getElementById('cf-chat-input');
    const messagesContainer = document.getElementById('cf-chat-messages');
    const typingIndicator = document.getElementById('cf-typing-indicator');
    const chipsContainer = document.getElementById('cf-chat-chips');

    if (!launcherBtn || !chatWindow || !chatForm || !chatInput) {
        return; // Chat widget not present on this page
    }

    // In-memory conversation history for multi-turn context
    let conversationHistory = [];
    let isSending = false;

    // 1. Toggle Chat Window
    launcherBtn.addEventListener('click', function () {
        const isHidden = chatWindow.classList.contains('d-none');
        if (isHidden) {
            chatWindow.classList.remove('d-none');
            launcherBtn.classList.add('d-none');
            chatInput.focus();
            scrollToBottom();
        }
    });

    closeBtn.addEventListener('click', function () {
        chatWindow.classList.add('d-none');
        launcherBtn.classList.remove('d-none');
    });

    // 2. Clear Conversation
    clearBtn.addEventListener('click', function () {
        conversationHistory = [];
        messagesContainer.innerHTML = `
            <div class="cf-message cf-msg-ai">
                <div class="cf-msg-avatar"><i class="bi bi-robot"></i></div>
                <div class="cf-msg-content">
                    <p class="mb-1"><strong>Conversation reset.</strong></p>
                    <p class="mb-0">How else can I help you with CrowdFund Egypt campaigns today?</p>
                </div>
            </div>
        `;
        if (chipsContainer) {
            chipsContainer.classList.remove('d-none');
        }
        chatInput.focus();
    });

    // 3. Quick Chips Handlers
    const chipButtons = document.querySelectorAll('.cf-chip-btn');
    chipButtons.forEach(btn => {
        btn.addEventListener('click', function () {
            const prompt = this.getAttribute('data-prompt');
            if (prompt && !isSending) {
                sendMessage(prompt);
            }
        });
    });

    // 4. Form Submit
    chatForm.addEventListener('submit', function (e) {
        e.preventDefault();
        const message = chatInput.value.trim();
        if (message && !isSending) {
            sendMessage(message);
        }
    });

    // 5. Send Message Function
    async function sendMessage(text) {
        if (!text || isSending) return;

        isSending = true;
        chatInput.value = '';
        chatInput.disabled = true;

        // Hide chips after first message
        if (chipsContainer) {
            chipsContainer.classList.add('d-none');
        }

        // Render User Message
        appendMessage('user', text);
        scrollToBottom();

        // Show Typing Indicator
        showTyping(true);
        scrollToBottom();

        // Get CSRF Token
        const csrfToken = getCsrfToken();

        try {
            const response = await fetch('/api/chat/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    message: text,
                    history: conversationHistory
                })
            });

            const data = await response.json();
            showTyping(false);

            if (response.ok && data.status === 'success') {
                const aiText = data.response;
                appendMessage('ai', aiText);
                
                // Track in conversation history
                conversationHistory.push({ role: 'user', content: text });
                conversationHistory.push({ role: 'assistant', content: aiText });
                
                // Keep history trimmed to last 8 turns
                if (conversationHistory.length > 8) {
                    conversationHistory = conversationHistory.slice(-8);
                }
            } else {
                const errMsg = data.error || 'Sorry, something went wrong while processing your request. Please try again.';
                appendMessage('ai', `⚠️ ${errMsg}`);
            }

        } catch (err) {
            console.error('Chat error:', err);
            showTyping(false);
            appendMessage('ai', '⚠️ Network error: Could not reach the server. Please check your connection.');
        } finally {
            isSending = false;
            chatInput.disabled = false;
            chatInput.focus();
            scrollToBottom();
        }
    }

    // 6. UI Helpers
    function appendMessage(role, text) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `cf-message ${role === 'user' ? 'cf-msg-user' : 'cf-msg-ai'}`;

        const avatarDiv = document.createElement('div');
        avatarDiv.className = 'cf-msg-avatar';
        avatarDiv.innerHTML = role === 'user' ? '<i class="bi bi-person-fill"></i>' : '<i class="bi bi-robot"></i>';

        const contentDiv = document.createElement('div');
        contentDiv.className = 'cf-msg-content';
        contentDiv.innerHTML = formatMessageContent(text, role);

        msgDiv.appendChild(avatarDiv);
        msgDiv.appendChild(contentDiv);
        messagesContainer.appendChild(msgDiv);
    }

    function formatMessageContent(text, role) {
        if (role === 'user') {
            return `<p class="mb-0">${escapeHtml(text)}</p>`;
        }

        // Basic Markdown Parsing for AI messages
        let html = escapeHtml(text);

        // Bold: **text**
        html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        
        // Italic: *text*
        html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');

        // Markdown links: [title](url)
        html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2">$1</a>');

        // Headers: ### Title
        html = html.replace(/^### (.*$)/gim, '<h6 class="fw-bold mt-2 mb-1">$1</h6>');
        html = html.replace(/^## (.*$)/gim, '<h5 class="fw-bold mt-2 mb-1">$1</h5>');

        // Linebreaks & bullet points
        const lines = html.split('\n');
        let formatted = '';
        let inList = false;

        lines.forEach(line => {
            const trimmed = line.trim();
            if (trimmed.startsWith('• ') || trimmed.startsWith('- ')) {
                if (!inList) {
                    formatted += '<ul class="mb-2 ps-3">';
                    inList = true;
                }
                formatted += `<li>${trimmed.substring(2)}</li>`;
            } else {
                if (inList) {
                    formatted += '</ul>';
                    inList = false;
                }
                if (trimmed) {
                    formatted += `<p class="mb-1">${trimmed}</p>`;
                }
            }
        });

        if (inList) {
            formatted += '</ul>';
        }

        return formatted || `<p class="mb-0">${html}</p>`;
    }

    function escapeHtml(str) {
        return (str || '')
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    function showTyping(show) {
        if (show) {
            typingIndicator.classList.remove('d-none');
        } else {
            typingIndicator.classList.add('d-none');
        }
    }

    function scrollToBottom() {
        setTimeout(() => {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }, 50);
    }

    function getCsrfToken() {
        const tokenInput = document.querySelector('[name=csrfmiddlewaretoken]');
        if (tokenInput) return tokenInput.value;

        // Fallback to cookie
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, 10) === 'csrftoken=') {
                    cookieValue = decodeURIComponent(cookie.substring(10));
                    break;
                }
            }
        }
        return cookieValue || '';
    }
});
