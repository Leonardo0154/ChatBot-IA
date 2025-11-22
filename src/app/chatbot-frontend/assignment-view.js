document.addEventListener('DOMContentLoaded', () => {
    const assignmentTitle = document.getElementById('assignment-title');
    const assignmentTask = document.getElementById('assignment-task');
    const assignmentWords = document.getElementById('assignment-words');
    const studentAnswer = document.getElementById('student-answer');
    const submitAnswerButton = document.getElementById('submit-answer-button');
    const feedbackArea = document.getElementById('feedback-area');

    const API_BASE_URL = 'http://localhost:8000';
    const AUTH_TOKEN = localStorage.getItem('accessToken');

    let currentWordIndex = 0;
    let assignment = null;
    let userAnswers = [];

    const urlParams = new URLSearchParams(window.location.search);
    const assignmentId = urlParams.get('id');

    async function loadAssignment() {
        if (!AUTH_TOKEN || !assignmentId) {
            window.location.href = 'assignments.html';
            return;
        }

        try {
            // This endpoint doesn't exist yet, I will create it.
            const response = await fetch(`${API_BASE_URL}/assignment/${assignmentId}`, {
                headers: { 'Authorization': `Bearer ${AUTH_TOKEN}` }
            });

            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

            assignment = await response.json();
            
            assignmentTitle.textContent = assignment.title;
            assignmentTask.textContent = assignment.task;

            displayCurrentWord();

        } catch (error) {
            console.error('Error loading assignment:', error);
            assignmentTitle.textContent = 'Error loading assignment.';
        }
    }

    function displayCurrentWord() {
        if (currentWordIndex < assignment.words.length) {
            assignmentWords.innerHTML = `<p>Word ${currentWordIndex + 1} of ${assignment.words.length}: <strong>${assignment.words[currentWordIndex]}</strong></p>`;
        } else {
            // Assignment finished
            assignmentWords.innerHTML = '<p>Assignment complete!</p>';
            studentAnswer.style.display = 'none';
            submitAnswerButton.style.display = 'none';
            saveResults();
        }
    }

    submitAnswerButton.addEventListener('click', () => {
        const answer = studentAnswer.value.trim();
        if (!answer) return;

        userAnswers.push({
            word: assignment.words[currentWordIndex],
            answer: answer
        });

        // Simple feedback for now
        if (answer.toLowerCase() === assignment.words[currentWordIndex].toLowerCase()) {
            feedbackArea.innerHTML = '<p style="color: green;">Correct!</p>';
        } else {
            feedbackArea.innerHTML = `<p style="color: red;">Incorrect. The correct answer is: ${assignment.words[currentWordIndex]}</p>`;
        }

        studentAnswer.value = '';
        currentWordIndex++;
        
        setTimeout(() => {
            feedbackArea.innerHTML = '';
            displayCurrentWord();
        }, 2000); // Clear feedback after 2 seconds
    });

    async function saveResults() {
        try {
            // This endpoint doesn't exist yet, I will create it.
            await fetch(`${API_BASE_URL}/assignment-results`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${AUTH_TOKEN}`
                },
                body: JSON.stringify({
                    assignment_id: assignmentId,
                    answers: userAnswers
                }),
            });
        } catch (error) {
            console.error('Error saving assignment results:', error);
        }
    }

    loadAssignment();
});
