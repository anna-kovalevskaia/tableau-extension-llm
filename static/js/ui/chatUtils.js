export function addMessage(text, type) {
    const chatBox = document.getElementById('chatBox');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    messageDiv.innerHTML = text;
    chatBox.appendChild(messageDiv);

    chatBox.scrollTop = chatBox.scrollHeight;
}

export function handleEnter(event, callback) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        callback();
    }
}