document.addEventListener('DOMContentLoaded', () => {
    const memoryGrid = document.getElementById('memory-grid');
    const restartGameButton = document.getElementById('restart-game-button');
    const API_BASE_URL = 'http://localhost:8000';

    let cards = [];
    let flippedCards = [];
    let matchedPairs = 0;

    async function initializeGame() {
        memoryGrid.innerHTML = '';
        cards = [];
        flippedCards = [];
        matchedPairs = 0;

        try {
            const response = await fetch(`${API_BASE_URL}/pictograms`);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const allPictograms = await response.json();

            // Get 8 unique pictograms for the game
            const gamePictograms = allPictograms.sort(() => 0.5 - Math.random()).slice(0, 8);
            const gameCards = [...gamePictograms, ...gamePictograms]; // Create pairs

            // Shuffle the cards
            gameCards.sort(() => 0.5 - Math.random());

            gameCards.forEach(pictogram => {
                const card = createCard(pictogram);
                memoryGrid.appendChild(card);
                cards.push(card);
            });

        } catch (error) {
            console.error('Error initializing game:', error);
            memoryGrid.innerHTML = '<p>Error loading game. Please try again.</p>';
        }
    }

    function createCard(pictogram) {
        const card = document.createElement('div');
        card.classList.add('card');
        card.dataset.pictogramPath = pictogram.path;

        card.innerHTML = `
            <div class="front">?</div>
            <div class="back"><img src="${API_BASE_URL}/pictogram/${pictogram.path}" alt="${pictogram.keywords[0].keyword}"></div>
        `;

        card.addEventListener('click', onCardClick);
        return card;
    }

    function onCardClick(e) {
        const clickedCard = e.currentTarget;

        if (flippedCards.length < 2 && !clickedCard.classList.contains('flipped')) {
            flipCard(clickedCard);
            flippedCards.push(clickedCard);

            if (flippedCards.length === 2) {
                setTimeout(checkForMatch, 1000);
            }
        }
    }

    function flipCard(card) {
        card.classList.add('flipped');
    }

    function unflipCards() {
        flippedCards.forEach(card => card.classList.remove('flipped'));
        flippedCards = [];
    }

    function checkForMatch() {
        const [card1, card2] = flippedCards;
        if (card1.dataset.pictogramPath === card2.dataset.pictogramPath) {
            card1.classList.add('matched');
            card2.classList.add('matched');
            matchedPairs++;
            flippedCards = [];
            if (matchedPairs === 8) {
                setTimeout(() => alert('You won!'), 500);
            }
        } else {
            unflipCards();
        }
    }

    restartGameButton.addEventListener('click', initializeGame);

    initializeGame();
});
