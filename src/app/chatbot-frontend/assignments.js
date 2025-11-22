document.addEventListener('DOMContentLoaded', () => {
    const assignmentsList = document.getElementById('assignments-list');
    const API_BASE_URL = 'http://localhost:8000';

    const AUTH_TOKEN = localStorage.getItem('accessToken');

    async function loadAssignments() {
        if (!AUTH_TOKEN) {
            assignmentsList.innerHTML = '<p>You must be logged in to view assignments. <a href="login.html">Login here</a>.</p>';
            return;
        }

        try {
            const response = await fetch(`${API_BASE_URL}/assignments`, {
                headers: { 'Authorization': `Bearer ${AUTH_TOKEN}` }
            });

            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

            const assignments = await response.json();
            assignmentsList.innerHTML = '';
            assignments.forEach(assignment => {
                const assignmentDiv = document.createElement('div');
                assignmentDiv.classList.add('assignment-item'); // You can style this class
                assignmentDiv.innerHTML = `
                    <h3>${assignment.title}</h3>
                    <p><strong>Task:</strong> ${assignment.task}</p>
                    <p><strong>Author:</strong> ${assignment.author}</p>
                    <p><strong>Created:</strong> ${new Date(assignment.timestamp).toLocaleDateString()}</p>
                    <button class="start-assignment-button" data-assignment-id="${assignment.timestamp}">Start Assignment</button>
                `;
                assignmentsList.appendChild(assignmentDiv);
            });

            document.querySelectorAll('.start-assignment-button').forEach(button => {
                button.addEventListener('click', (e) => {
                    const assignmentId = e.target.dataset.assignmentId;
                    window.location.href = `assignment-view.html?id=${assignmentId}`;
                });
            });

        } catch (error) {
            console.error('Error loading assignments:', error);
            assignmentsList.innerHTML = '<p>Error loading assignments.</p>';
        }
    }

    loadAssignments();
});
