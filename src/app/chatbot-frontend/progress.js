document.addEventListener('DOMContentLoaded', () => {
    const progressTableBody = document.querySelector('#progress-table tbody');
    const analyticsSummary = document.getElementById('analytics-summary');
    const interactionsTimeline = document.getElementById('interactions-timeline');
    const categoryUsage = document.getElementById('category-usage');
    const API_BASE_URL = 'http://localhost:8000';

    // IMPORTANT: In a real application, the token should be stored securely.
    const AUTH_TOKEN = localStorage.getItem('accessToken');

    async function loadProgressData() {
        if (!AUTH_TOKEN) {
            analyticsSummary.innerHTML = '<p>You must be logged in to view progress. <a href="login.html">Login here</a>.</p>';
            return;
        }

        try {
            const response = await fetch(`${API_BASE_URL}/progress`, {
                headers: {
                    'Authorization': `Bearer ${AUTH_TOKEN}`
                }
            });

            if (response.status === 401) {
                analyticsSummary.innerHTML = '<p>Unauthorized. Please check your token.</p>';
                return;
            }

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            const { analytics, logs } = data;

            // Display analytics
            if (analytics && Object.keys(analytics).length > 0) {
                analyticsSummary.innerHTML = `
                    <h3>Summary</h3>
                    <p><strong>Total Interactions:</strong> ${analytics.num_interactions}</p>
                    <p><strong>Unique Words Used:</strong> ${analytics.num_unique_words}</p>
                    <p><strong>Average Words per Interaction:</strong> ${analytics.avg_words_per_interaction}</p>
                `;

                if (analytics.interactions_per_day) {
                    let timelineHTML = '<h3>Interactions per Day</h3><ul>';
                    for (const [date, count] of Object.entries(analytics.interactions_per_day)) {
                        timelineHTML += `<li><strong>${date}:</strong> ${count} interactions</li>`;
                    }
                    timelineHTML += '</ul>';
                    interactionsTimeline.innerHTML = timelineHTML;
                }

                if (analytics.most_common_categories) {
                    let categoryHTML = '<h3>Most Common Categories</h3><ul>';
                    analytics.most_common_categories.forEach(item => {
                        categoryHTML += `<li>${item[0]}: ${item[1]} times</li>`;
                    });
                    categoryHTML += '</ul>';
                    categoryUsage.innerHTML = categoryHTML;
                }

            } else {
                analyticsSummary.innerHTML = '<p>No analytics data available.</p>';
            }

            // Display logs
            progressTableBody.innerHTML = ''; // Clear previous data
            if (logs.length === 0) {
                progressTableBody.innerHTML = '<tr><td colspan="3">No progress data found.</td></tr>';
                return;
            }

            logs.forEach(log => {
                const row = document.createElement('tr');

                const timestampCell = document.createElement('td');
                timestampCell.textContent = new Date(log.timestamp).toLocaleString();
                row.appendChild(timestampCell);

                const sentenceCell = document.createElement('td');
                sentenceCell.textContent = log.sentence;
                row.appendChild(sentenceCell);

                const responseCell = document.createElement('td');
                const botResponseText = log.processed_sentence.map(item => item.word).join(' ');
                const pictogramsHTML = log.processed_sentence.map(item => {
                    if (item.pictogram) {
                        return `<img src="${API_BASE_URL}/pictogram/${item.pictogram}" alt="pictogram" style="width: 30px; height: 30px; margin: 2px;">`;
                    }
                    return '';
                }).join('');
                
                responseCell.innerHTML = `${botResponseText}<br>${pictogramsHTML}`;
                row.appendChild(responseCell);

                progressTableBody.appendChild(row);
            });

        } catch (error) {
            console.error('Error loading progress data:', error);
            analyticsSummary.innerHTML = '<p>Error loading data.</p>';
        }
    }

    loadProgressData();
});
