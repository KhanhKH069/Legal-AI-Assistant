const chatForm = document.getElementById('chatForm');
const chatInput = document.getElementById('chatInput');
const chatContainer = document.getElementById('chatContainer');
const typingIndicator = document.getElementById('typingIndicator');
const btnUpload = document.getElementById('btnUpload');
const cvUpload = document.getElementById('cvUpload');
const uploadStatus = document.getElementById('uploadStatus');

// Generate random session ID for chat
const sessionId = 'guest_' + Math.random().toString(36).substring(2, 10);

// Convert markdown to basic HTML (bold, breaks)
function parseMarkdown(text) {
    let parsed = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    parsed = parsed.replace(/\n/g, '<br>');
    return parsed;
}

function scrollToBottom() {
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function showTyping() {
    typingIndicator.style.display = 'block';
    scrollToBottom();
}

function hideTyping() {
    typingIndicator.style.display = 'none';
}

function appendUserMessage(text) {
    const wrapper = document.createElement('div');
    wrapper.className = 'message-wrapper user-message-wrapper';
    wrapper.innerHTML = `
        <div class="avatar user-avatar"><i class="ph ph-user"></i></div>
        <div class="message user-message"><p>${text}</p></div>
    `;
    chatContainer.appendChild(wrapper);
    scrollToBottom();
}

function createAiMessageContainer() {
    const wrapper = document.createElement('div');
    wrapper.className = 'message-wrapper ai-message-wrapper';

    const avatar = document.createElement('div');
    avatar.className = 'avatar ai-avatar';
    avatar.innerHTML = '<i class="ph ph-sparkle"></i>';

    const msgDiv = document.createElement('div');
    msgDiv.className = 'message ai-message';
    const p = document.createElement('p');
    msgDiv.appendChild(p);

    wrapper.appendChild(avatar);
    wrapper.appendChild(msgDiv);
    chatContainer.appendChild(wrapper);

    return p;
}

async function sendChatRequest(messageText) {
    appendUserMessage(messageText);
    chatInput.value = '';

    showTyping();

    try {
        const response = await fetch('/chat/guest/stream', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: messageText,
                session_id: sessionId
            })
        });

        hideTyping();

        const reader = response.body.getReader();
        const decoder = new TextDecoder('utf-8');
        let aiTextElement = null;
        let fullText = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value);
            const lines = chunk.split('\n\n');

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const dataStr = line.substring(6);
                    try {
                        const data = JSON.parse(dataStr);
                        if (data.done) {
                            break;
                        }

                        if (!aiTextElement) {
                            aiTextElement = createAiMessageContainer();
                        }

                        fullText += data.token;
                        aiTextElement.innerHTML = parseMarkdown(fullText);
                        scrollToBottom();
                    } catch (e) {
                        console.error('Error parsing SSE data:', e);
                    }
                }
            }
        }

    } catch (error) {
        console.error('Error sending message:', error);
        hideTyping();
        const aiTextElement = createAiMessageContainer();
        aiTextElement.innerText = "Lỗi kết nối. Vui lòng thử lại sau.";
    }
}

// Event Listeners
chatForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const text = chatInput.value.trim();
    if (text) {
        sendChatRequest(text);
    }
});

btnUpload.addEventListener('click', () => {
    cvUpload.click();
});

cvUpload.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    if (file.type !== 'application/pdf') {
        uploadStatus.innerText = 'Vui lòng chọn file PDF!';
        uploadStatus.style.color = '#ef4444';
        setTimeout(() => uploadStatus.innerText = '', 3000);
        return;
    }

    uploadStatus.innerText = 'Đang tải lên...';
    uploadStatus.style.color = '#3b82f6';

    const formData = new FormData();
    formData.append('file', file);

    try {
        const res = await fetch('/upload_cv', {
            method: 'POST',
            body: formData
        });

        const data = await res.json();
        if (data.status === 'success') {
            uploadStatus.innerText = 'Tải file thành công!';
            uploadStatus.style.color = '#10b981';
            setTimeout(() => uploadStatus.innerText = '', 3000);

            // Automatically send a message on behalf of the user saying they uploaded a CV
            const msg = `Mình đã tải lên CV tại đường dẫn: ${data.file_path}. Nhờ HR phân tích giúp mình nhé.`;

            // Add a system-like message
            const sysMsg = document.createElement('div');
            sysMsg.className = 'system-msg';
            sysMsg.innerHTML = `<i class="ph ph-check-circle"></i> Đã đính kèm file: ${data.filename}`;
            chatContainer.appendChild(sysMsg);

            sendChatRequest(msg);
        } else {
            uploadStatus.innerText = 'Lỗi tải file!';
            uploadStatus.style.color = '#ef4444';
        }
    } catch (err) {
        uploadStatus.innerText = 'Lỗi mạng khi tải file!';
        uploadStatus.style.color = '#ef4444';
    }

    // Reset file input
    cvUpload.value = '';
});
