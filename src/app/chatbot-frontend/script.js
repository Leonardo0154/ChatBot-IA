document.addEventListener('DOMContentLoaded', () => {
    // ... (existing element selections)
    const logoutButton = document.getElementById('logout-button');
    const progressLink = document.getElementById('progress-link');
    const notificationsLink = document.getElementById('notifications-link');
    const guidedSessionLink = document.getElementById('guided-session-link');
    const notesLink = document.getElementById('notes-link');
    const loginLink = document.querySelector('a[href="login.html"]');

    function handleAuth() {
        const token = localStorage.getItem('accessToken');
        if (token) {
            try {
                const decodedToken = jwt_decode(token);
                const userRole = decodedToken.role;

                loginLink.style.display = 'none';
                logoutButton.style.display = 'inline-block';

                if (userRole === 'teacher' || userRole === 'parent') {
                    progressLink.style.display = 'inline-block';
                    notificationsLink.style.display = 'inline-block';
                    notesLink.style.display = 'inline-block';
                }
                if (userRole === 'therapist') {
                    progressLink.style.display = 'inline-block';
                    notificationsLink.style.display = 'inline-block';
                    guidedSessionLink.style.display = 'inline-block';
                    notesLink.style.display = 'inline-block';
                }

            } catch (error) {
                console.error('Error decoding token:', error);
                localStorage.removeItem('accessToken');
            }
        }
    }

    logoutButton.addEventListener('click', () => {
        localStorage.removeItem('accessToken');
        window.location.reload();
    });

    async function sendMessage(text) {
        if (!text || text.trim() === '') return;

        addMessageToChat(text, 'user');
        userInput.value = '';
        showTypingIndicator();

        const token = localStorage.getItem('accessToken');
        const headers = { 'Content-Type': 'application/json' };
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        try {
            const response = await fetch(`${API_BASE_URL}/process`, {
                method: 'POST',
                headers: headers,
                body: JSON.stringify({ text: text }),
            });

            if (!response.ok) {
                 if (response.status === 401) {
                    addMessageToChat('Your session has expired. Please log in again.', 'bot');
                    localStorage.removeItem('accessToken');
                    handleAuth();
                 } else {
                    throw new Error(`HTTP error! status: ${response.status}`);
                 }
            } else {
                const data = await response.json();
                const processedSentence = data.processed_sentence;
                const pictogramPaths = processedSentence.map(item => item.pictogram).filter(p => p);
                const botTextResponse = processedSentence.map(item => item.word).join(' ');

                hideTypingIndicator();
                addMessageToChat(botTextResponse, 'bot', pictogramPaths);
            }
        } catch (error) {
            console.error('Error sending message:', error);
            hideTypingIndicator();
            addMessageToChat('Lo siento, algo salió mal.', 'bot');
        }
    }

    // Initial Load
    handleAuth();
    loadCategories();
    loadPictogramGallery();
    addMessageToChat('¡Hola! Soy ChatBot-IA. ¿En qué puedo ayudarte?', 'bot');
});

