document.addEventListener('DOMContentLoaded', () => {
    const assignmentsList = document.getElementById('assignments-list');
    const API_BASE_URL = 'http://localhost:8000';

    function parseJwt (token) {
        try {
            const base64Url = token.split('.')[1];
            const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
            const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
                return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
            }).join(''));
            return JSON.parse(jsonPayload);
        } catch (e) {
            return null;
        }
    }

    async function loadAssignments() {
        const AUTH_TOKEN = localStorage.getItem('accessToken');
        if (!AUTH_TOKEN) {
            assignmentsList.innerHTML = '<p>You must be logged in to view assignments. <a href="login.html">Login here</a>.</p>';
            return;
        }

        const decoded = parseJwt(AUTH_TOKEN) || {};
        const userRole = decoded.role;
        const username = decoded.sub;

        try {
            const response = await fetch(`${API_BASE_URL}/assignments`, {
                headers: { 'Authorization': `Bearer ${AUTH_TOKEN}` }
            });

            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

            const assignments = await response.json();
            assignmentsList.innerHTML = '';

            // If user is a teacher/parent/therapist show only assignments they created
            const visibleAssignments = (userRole === 'teacher' || userRole === 'parent' || userRole === 'therapist')
                ? assignments.filter(a => a.author === username)
                : assignments;

            visibleAssignments.forEach(assignment => {
                const assignmentDiv = document.createElement('div');
                assignmentDiv.classList.add('assignment-item'); // You can style this class
                const isStudent = (userRole === 'student' || userRole === 'child');
                const buttonLabel = isStudent ? 'Start Assignment' : 'View Assignment';
                assignmentDiv.innerHTML = `
                    <h3>${assignment.title} ${assignment.type === 'guided_session' ? '(Guided Session)' : ''}</h3>
                    <p><strong>Task:</strong> ${assignment.task}</p>
                    <p><strong>Author:</strong> ${assignment.author}</p>
                    <p><strong>Created:</strong> ${new Date(assignment.timestamp).toLocaleDateString()}</p>
                    <button class="start-assignment-button" data-assignment-id="${assignment.timestamp}">${buttonLabel}</button>
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
