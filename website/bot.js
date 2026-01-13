// Bot WhatsApp Test Interface
const API_BASE = 'http://localhost:8000';

let chatHistory = [];

function sendMessage() {
    const input = document.getElementById('user-message');
    const message = input.value.trim();
    
    if (!message) return;
    
    // Adicionar mensagem do usuário
    addMessage(message, 'user');
    input.value = '';
    
    // Mostrar "digitando..."
    showTyping();
    
    // Enviar para API
    fetch(`${API_BASE}/api/bot/message`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            message: message,
            context: {
                empresa: 'Assyntrax',
                setor: 'tecnologia'
            }
        })
    })
    .then(response => response.json())
    .then(data => {
        hideTyping();
        if (data.success !== false) {
            addMessage(data.response, 'bot', data.confidence);
            chatHistory.push({
                user: message,
                bot: data.response,
                timestamp: new Date().toISOString()
            });
        } else {
            addMessage('Desculpe, ocorreu um erro. Tente novamente.', 'bot', 0);
        }
    })
    .catch(error => {
        hideTyping();
        addMessage('Erro ao conectar com a API. Certifique-se de que o servidor está rodando em ' + API_BASE, 'bot', 0);
        console.error('Error:', error);
    });
}

function sendSuggestion(text) {
    document.getElementById('user-message').value = text;
    sendMessage();
}

function handleKeyPress(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
}

function addMessage(text, sender, confidence = 1) {
    const messagesContainer = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${sender}-message`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = text;
    
    const timeDiv = document.createElement('div');
    timeDiv.className = 'message-time';
    timeDiv.textContent = 'Agora';
    
    if (sender === 'bot' && confidence < 0.7) {
        const confidenceBadge = document.createElement('span');
        confidenceBadge.className = 'confidence-badge';
        confidenceBadge.textContent = 'Confiança: ' + (confidence * 100).toFixed(0) + '%';
        contentDiv.appendChild(confidenceBadge);
    }
    
    messageDiv.appendChild(contentDiv);
    messageDiv.appendChild(timeDiv);
    messagesContainer.appendChild(messageDiv);
    
    // Scroll para baixo
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function showTyping() {
    const messagesContainer = document.getElementById('chat-messages');
    const typingDiv = document.createElement('div');
    typingDiv.className = 'chat-message bot-message typing';
    typingDiv.id = 'typing-indicator';
    typingDiv.innerHTML = `
        <div class="message-content">
            <span class="typing-dots">
                <span>.</span><span>.</span><span>.</span>
            </span>
        </div>
    `;
    messagesContainer.appendChild(typingDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function hideTyping() {
    const typing = document.getElementById('typing-indicator');
    if (typing) {
        typing.remove();
    }
}

// Verificar conexão com API ao carregar
window.addEventListener('load', async () => {
    try {
        const response = await fetch(`${API_BASE}/api/health`);
        const data = await response.json();
        console.log('✅ API conectada:', data);
    } catch (error) {
        console.warn('⚠️ API não está disponível. Certifique-se de que o servidor está rodando.');
        addMessage('⚠️ API não está disponível. Certifique-se de que o servidor está rodando em ' + API_BASE, 'bot', 0);
    }
});
