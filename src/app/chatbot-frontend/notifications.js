document.addEventListener('DOMContentLoaded', () => {
    const notificationSummary = document.getElementById('notification-summary');
    const API_BASE_URL = 'http://localhost:8000';

    // IMPORTANT: In a real application, the token should be stored securely.
    const AUTH_TOKEN = 'your_jwt_token_here'; 

    async function loadNotifications() {
        if (AUTH_TOKEN === 'your_jwt_token_here') {
            notificationSummary.innerHTML = '<p>Please replace "your_jwt_token_here" with a valid token in notifications.js</p>';
            return;
        }

        try {
            const response = await fetch(`${API_BASE_URL}/notifications`, {
                headers: {
                    'Authorization': `Bearer ${AUTH_TOKEN}`
                }
            });

            if (response.status === 401) {
                notificationSummary.innerHTML = '<p>Unauthorized. Please check your token.</p>';
                return;
            }

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            if (data.message) {
                notificationSummary.innerHTML = `<p>${data.message}</p>`;
                return;
            }

            const summaryHTML = `
                <p><strong>Date:</strong> ${data.date}</p>
                <p><strong>Number of Interactions:</strong> ${data.num_interactions}</p>
                <p><strong>First Interaction:</strong> ${new Date(data.first_interaction).toLocaleTimeString()}</p>
                <p><strong>Last Interaction:</strong> ${new Date(data.last_interaction).toLocaleTimeString()}</p>
                <h3>Most Common Words:</h3>
                <ul>
                    ${data.most_common_words.map(item => `<li>${item[0]}: ${item[1]} times</li>`).join('')}
                </ul>
            `;
            notificationSummary.innerHTML = summaryHTML;

        } catch (error) {
            console.error('Error loading notifications:', error);
            notificationSummary.innerHTML = '<p>Error loading notifications.</p>';
        }
    }

    loadNotifications();
});
