const chatForm = document.getElementById('chat-form');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const chatMessages = document.getElementById('chat-messages');
const clearBtn = document.getElementById('clear-btn');

function appendMessage(sender, text) {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', sender);

    const iconClass = sender === 'user' ? 'fa-user' : 'fa-robot';
    let formattedContent = typeof text === 'string' ? text : (text.output || text.answer || JSON.stringify(text));

    if (typeof marked !== 'undefined' && sender === 'bot') {
        formattedContent = marked.parse(formattedContent);
    } else {
        formattedContent = `<p>${formattedContent.replace(/\n/g, '<br>')}</p>`;
    }

    const tagHtml = sender === 'bot' ? '<div class="author-tag">ASISTENTE OFICIAL UCSS</div>' : '';

    messageDiv.innerHTML = `
        <div class="avatar"><i class="fa-solid ${iconClass}"></i></div>
        <div class="message-content">
            ${tagHtml}
            ${formattedContent}
        </div>
    `;

    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const query = userInput.value.trim();
    if (!query) return;

    // Deshabilitar input y botón durante el procesamiento
    userInput.disabled = true;
    sendBtn.disabled = true;

    appendMessage('user', query);
    userInput.value = '';

    // Indicador de carga
    const loadingDiv = document.createElement('div');
    loadingDiv.classList.add('message', 'bot');
    loadingDiv.id = 'loading-indicator';
    loadingDiv.innerHTML = `
        <div class="avatar"><i class="fa-solid fa-robot"></i></div>
        <div class="message-content">
            <div class="author-tag">CONSULTANDO BASE DE DATOS</div>
            <p><i class="fa-solid fa-circle-notch fa-spin"></i> Obteniendo información oficial UCSS...</p>
        </div>
    `;
    chatMessages.appendChild(loadingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question: query })
        });

        const data = await response.json();
        
        const loadingElem = document.getElementById('loading-indicator');
        if (loadingElem) loadingElem.remove();

        const botAnswer = data.answer || "No se recibió una respuesta válida del servidor.";
        appendMessage('bot', botAnswer);

    } catch (error) {
        const loadingElem = document.getElementById('loading-indicator');
        if (loadingElem) loadingElem.remove();
        appendMessage('bot', 'Error de conexión con el servidor. Por favor, intenta de nuevo.');
    } finally {
        userInput.disabled = false;
        sendBtn.disabled = false;
        userInput.focus();
    }
});

function insertQuery(text) {
    userInput.value = text;
    chatForm.dispatchEvent(new Event('submit'));
}

clearBtn.addEventListener('click', () => {
    chatMessages.innerHTML = `
        <div class="message bot">
            <div class="avatar"><i class="fa-solid fa-robot"></i></div>
            <div class="message-content">
                <div class="author-tag">SISTEMA REINICIADO</div>
                <p>Chat reiniciado con éxito. ¿En qué más puedo ayudarte hoy?</p>
            </div>
        </div>
    `;
});