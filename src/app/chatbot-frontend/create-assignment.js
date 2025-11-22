document.addEventListener('DOMContentLoaded', () => {
    const assignmentTitle = document.getElementById('assignment-title');
    const assignmentWords = document.getElementById('assignment-words');
    const assignmentTask = document.getElementById('assignment-task');
    const createAssignmentButton = document.getElementById('create-assignment-button');
    const API_BASE_URL = 'http://localhost:8000';

    createAssignmentButton.addEventListener('click', async () => {
        const AUTH_TOKEN = localStorage.getItem('accessToken');
        if (!AUTH_TOKEN) {
            alert('You must be logged in to create an assignment.');
            return;
        }

        const title = assignmentTitle.value.trim();
        const words = assignmentWords.value.split(',').map(word => word.trim()).filter(word => word);
        const task = assignmentTask.value.trim();

        if (!title || words.length === 0 || !task) {
            alert('Please fill out all fields.');
            return;
        }

        try {
            const response = await fetch(`${API_BASE_URL}/assignments`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${AUTH_TOKEN}`
                },
                body: JSON.stringify({
                    title: title,
                    words: words,
                    task: task
                }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            alert('Assignment created successfully!');
            window.location.href = 'index.html'; // Redirect to home page
        } catch (error) {
            console.error('Error creating assignment:', error);
            alert('Error creating assignment.');
        }
    });
});
