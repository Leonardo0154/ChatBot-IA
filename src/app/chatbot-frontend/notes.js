document.addEventListener('DOMContentLoaded', () => {
    const noteText = document.getElementById('note-text');
    const addNoteButton = document.getElementById('add-note-button');
    const notesList = document.getElementById('notes-list');
    const API_BASE_URL = 'http://localhost:8000';

    // IMPORTANT: In a real application, the token should be stored securely.
    const AUTH_TOKEN = localStorage.getItem('accessToken');

    async function loadNotes() {
        if (!AUTH_TOKEN) {
            notesList.innerHTML = '<p>You must be logged in to view and add notes. <a href="login.html">Login here</a>.</p>';
            return;
        }

        try {
            const response = await fetch(`${API_BASE_URL}/notes`, {
                headers: { 'Authorization': `Bearer ${AUTH_TOKEN}` }
            });

            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

            const notes = await response.json();
            notesList.innerHTML = '';
            notes.forEach(note => {
                const noteDiv = document.createElement('div');
                noteDiv.classList.add('note');
                noteDiv.innerHTML = `
                    <p><strong>${note.author}</strong> (${new Date(note.timestamp).toLocaleString()}):</p>
                    <p>${note.text}</p>
                `;
                notesList.appendChild(noteDiv);
            });
        } catch (error) {
            console.error('Error loading notes:', error);
        }
    }

    addNoteButton.addEventListener('click', async () => {
        const text = noteText.value.trim();
        if (!text) return;

        try {
            const response = await fetch(`${API_BASE_URL}/notes`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${AUTH_TOKEN}`
                },
                body: JSON.stringify({ text: text }),
            });

            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

            noteText.value = '';
            loadNotes();
        } catch (error) {
            console.error('Error adding note:', error);
        }
    });

    loadNotes();
});
