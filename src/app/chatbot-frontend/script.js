document.addEventListener('DOMContentLoaded', () => {
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const micButton = document.getElementById('mic-button');
    const chatHistory = document.getElementById('chat-history');
    const pictogramImages = document.getElementById('pictogram-images');
    const categorySelect = document.getElementById('category-select');
    const playGameButton = document.getElementById('play-game-button');
    const logoutButton = document.getElementById('logout-button');
    const progressLink = document.getElementById('progress-link');
    const notificationsLink = document.getElementById('notifications-link');
    const guidedSessionLink = document.getElementById('guided-session-link');
    const notesLink = document.getElementById('notes-link');
    const loginLink = document.querySelector('a[href="login.html"]');

    const API_BASE_URL = 'http://localhost:8000';

    // --- Authentication Handling ---
    function handleAuth() {
        const token = localStorage.getItem('accessToken');
        if (token) {
            try {
                const decodedToken = jwt_decode(token);
                const userRole = decodedToken.role;

                if(loginLink) loginLink.style.display = 'none';
                if(logoutButton) logoutButton.style.display = 'inline-block';

                if (userRole === 'teacher' || userRole === 'parent') {
                    if(progressLink) progressLink.style.display = 'inline-block';
                    if(notificationsLink) notificationsLink.style.display = 'inline-block';
                    if(notesLink) notesLink.style.display = 'inline-block';
                }
                if (userRole === 'therapist') {
                    if(progressLink) progressLink.style.display = 'inline-block';
                    if(notificationsLink) notificationsLink.style.display = 'inline-block';
                    if(guidedSessionLink) guidedSessionLink.style.display = 'inline-block';
                    if(notesLink) notesLink.style.display = 'inline-block';
                }
            } catch (error) {
                console.error('Error decoding token:', error);
                localStorage.removeItem('accessToken');
            }
        }
    }

    if(logoutButton) {
        logoutButton.addEventListener('click', async () => {
            const token = localStorage.getItem('accessToken');
            if (token) {
                try {
                    await fetch(`${API_BASE_URL}/logout`, {
                        method: 'POST',
                        headers: {
                            'Authorization': `Bearer ${token}`
                        }
                    });
                } catch (error) {
                    console.error('Error during logout:', error);
                }
            }
            localStorage.removeItem('accessToken');
            window.location.reload();
        });
    }

    // --- Speech Recognition ---
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    let recognition;
    if (SpeechRecognition) {
        recognition = new SpeechRecognition();
        // ... (rest of speech recognition setup as before)
    }

    // --- API and UI Functions ---
    async function sendMessage(text) {
        if (!text || text.trim() === '') return;
        addMessageToChat(text, 'user');
        userInput.value = '';
        showTypingIndicator();

        const token = localStorage.getItem('accessToken');
        const headers = { 'Content-Type': 'application/json' };
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        } else {
            addMessageToChat('You must be logged in to chat.', 'bot');
            hideTypingIndicator();
            return;
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
                return;
            }
            
            const data = await response.json();
            const processedSentence = data.processed_sentence;
            const pictogramPaths = processedSentence.map(item => item.pictogram).filter(p => p);
            const botTextResponse = processedSentence.map(item => item.word).join(' ');
            
            addMessageToChat(botTextResponse, 'bot', pictogramPaths);
        } catch (error) {
            console.error('Error sending message:', error);
            addMessageToChat('Lo siento, algo salió mal.', 'bot');
        } finally {
            hideTypingIndicator();
        }
    }
    
    function addMessageToChat(message, sender, pictograms = []) {
        const messageContainer = document.createElement('div');
        messageContainer.classList.add('message-container', sender);
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message');
        
        let content = `<span>${message}</span>`;
        
        if (pictograms.length > 0) {
            const pictogramWrapper = document.createElement('div');
            pictogramWrapper.classList.add('pictogram-wrapper');
            pictograms.forEach(p => {
                if (p) {
                    const img = document.createElement('img');
                    img.src = `${API_BASE_URL}/pictogram/${p}`;
                    img.alt = 'pictogram';
                    pictogramWrapper.appendChild(img);
                }
            });
            messageDiv.innerHTML = content;
            messageDiv.appendChild(pictogramWrapper);
        } else {
             messageDiv.innerHTML = content;
        }
        
        messageContainer.appendChild(messageDiv);
        chatHistory.appendChild(messageContainer);
        chatHistory.scrollTop = chatHistory.scrollHeight;

        if (sender === 'bot') {
            const utterance = new SpeechSynthesisUtterance(message);
            utterance.lang = 'es-ES';
            speechSynthesis.speak(utterance);
        }
    }

    function showTypingIndicator() { /* ... */ }
    function hideTypingIndicator() { /* ... */ }

    async function loadCategories() {
        try {
            const response = await fetch(`${API_BASE_URL}/categories`);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const categories = await response.json();
            categories.forEach(category => {
                const option = document.createElement('option');
                option.value = category;
                option.textContent = category;
                if(categorySelect) categorySelect.appendChild(option);
            });
        } catch (error) {
            console.error('Error loading categories:', error);
        }
    }

    async function loadPictogramGallery() {
        try {
            const response = await fetch(`${API_BASE_URL}/pictograms`);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const pictograms = await response.json();
            pictograms.forEach(p => {
                if (p.path && p.keywords && p.keywords.length > 0) {
                    const img = document.createElement('img');
                    img.src = `${API_BASE_URL}/pictogram/${p.path}`;
                    img.alt = p.keywords[0].keyword;
                    img.title = p.keywords[0].keyword;
                    img.addEventListener('click', () => {
                        userInput.value += ` ${p.keywords[0].keyword} `;
                    });
                    if(pictogramImages) pictogramImages.appendChild(img);
                }
            });
        } catch (error) {
            console.error('Error loading pictogram gallery:', error);
        }
    }

    // --- Event Listeners ---
    if(sendButton) {
        sendButton.addEventListener('click', () => sendMessage(userInput.value));
    }
    if(userInput) {
        userInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage(userInput.value);
        });
    }
    if(playGameButton) {
        playGameButton.addEventListener('click', () => {
            const selectedCategory = categorySelect.value;
            sendMessage(selectedCategory ? `jugar a ${selectedCategory}` : 'jugar');
        });
    }

    // --- Initial Load ---
    handleAuth();
    loadCategories();
    loadPictogramGallery();
    addMessageToChat('¡Hola! Soy ChatBot-IA. ¿En qué puedo ayudarte?', 'bot');
});