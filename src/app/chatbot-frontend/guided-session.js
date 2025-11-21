document.addEventListener('DOMContentLoaded', () => {
    const sessionWords = document.getElementById('session-words');
    const startSessionButton = document.getElementById('start-session-button');
    const sessionStatus = document.getElementById('session-status');
    const API_BASE_URL = 'http://localhost:8000';

    // IMPORTANT: In a real application, the token should be stored securely.
    const AUTH_TOKEN = localStorage.getItem('accessToken');

    startSessionButton.addEventListener('click', async () => {
        const words = sessionWords.value.split(',').map(word => word.trim()).filter(word => word);
        
        if (words.length === 0) {
            sessionStatus.textContent = 'Please enter at least one word.';
            return;
        }

        if (!AUTH_TOKEN) {
            sessionStatus.textContent = 'You must be logged in to start a session. <a href="login.html">Login here</a>.';
            return;
        }

        try {
            const response = await fetch(`${API_BASE_URL}/start-guided-session`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${AUTH_TOKEN}`
                },
                body: JSON.stringify({ words: words }),
            });

            if (response.status === 401) {
                sessionStatus.textContent = 'Unauthorized. Please check your token.';
                return;
            }

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            sessionStatus.textContent = data.message;

        } catch (error) {
            console.error('Error starting guided session:', error);
            sessionStatus.textContent = 'Error starting the session.';
        }
    });
});
