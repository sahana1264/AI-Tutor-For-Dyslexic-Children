// // const flashcard = document.getElementById('flashcard');
// // const feedback = document.getElementById('feedback');
// // const scoreBoard = document.getElementById('score');

// // let score = 0;
// // let total = 0;

// // const flashcards = [
// //   { letter: 'b', correct: 'b' },
// //   { letter: 'd', correct: 'd' },
// //   { letter: 'b', correct: 'b' },
// //   { letter: 'd', correct: 'd' },
// //   { letter: 'b', correct: 'b' },
// //   { letter: 'd', correct: 'd' }
// // ];

// // // Shuffle the cards
// // function shuffle(array) {
// //   return array.sort(() => Math.random() - 0.5);
// // }

// // let shuffled = shuffle(flashcards);
// // let current = 0;

// // function loadCard() {
// //   if (current >= shuffled.length) {
// //     flashcard.innerText = '✅ Done!';
// //     feedback.innerText = '';
// //     scoreBoard.innerText = `Final Score: ${score}/${total}`;
// //     return;
// //   }

// //   flashcard.innerText = shuffled[current].letter;
// //   feedback.innerText = '';
// //   scoreBoard.innerText = `Score: ${score}/${total}`;
// // }

// // function checkAnswer(answer) {
// //   total++;

// //   if (shuffled[current].correct === answer) {
// //     feedback.innerText = '✅ Correct!';
// //     feedback.style.color = 'green';
// //     score++;
// //   } else {
// //     feedback.innerText = '❌ Try Again!';
// //     feedback.style.color = 'red';
// //   }

// //   current++;
// //   setTimeout(loadCard, 1000);
// // }

// // loadCard();
const flashcard = document.getElementById('flashcard');
const feedback = document.getElementById('feedback');
const scoreBoard = document.getElementById('score');
const buttonContainer = document.getElementById('buttons');

let score = 0;
let total = 0;

const mirrorPairs = [
  { letter: 'b', options: ['b', 'd'], correct: 'b' },
  { letter: 'd', options: ['b', 'd'], correct: 'd' },
  { letter: 'p', options: ['p', 'q'], correct: 'p' },
  { letter: 'q', options: ['p', 'q'], correct: 'q' },
  { letter: 'm', options: ['m', 'w'], correct: 'm' },
  { letter: 'w', options: ['m', 'w'], correct: 'w' },
  { letter: 'n', options: ['n', 'u'], correct: 'n' },
  { letter: 'u', options: ['n', 'u'], correct: 'u' }
];

// Shuffle the flashcards
function shuffle(array) {
  return array.sort(() => Math.random() - 0.5);
}

let shuffled = shuffle([...mirrorPairs, ...mirrorPairs]); // double up for practice
let current = 0;

function loadCard() {
  if (current >= shuffled.length) {
    flashcard.innerText = '🎉 All Done!';
    buttonContainer.innerHTML = '';
    feedback.innerText = '';
    scoreBoard.innerText = `Final Score: ${score}/${total}`;
    return;
  }

  const card = shuffled[current];
  flashcard.innerText = card.letter;
  buttonContainer.innerHTML = '';

  // Create buttons for options
  card.options.forEach(option => {
    const btn = document.createElement('button');
    btn.innerText = option;
    btn.className = 'option-button';
    btn.onclick = () => checkAnswer(option);
    buttonContainer.appendChild(btn);
  });

  feedback.innerText = '';
  scoreBoard.innerText = `Score: ${score}/${total}`;
}

function checkAnswer(answer) {
  total++;

  if (shuffled[current].correct === answer) {
    feedback.innerText = '✅ Correct!';
    feedback.style.color = 'green';
    score++;
  } else {
    feedback.innerText = `❌ Incorrect! It's "${shuffled[current].correct}"`;
    feedback.style.color = 'red';
  }

  current++;
  setTimeout(loadCard, 1000);
}

loadCard();
// const flashcard = document.getElementById('flashcard');
// const feedback = document.getElementById('feedback');
// const scoreBoard = document.getElementById('score');
// const buttonContainer = document.getElementById('buttons');

// let score = 0;
// let total = 0;
// let errorLog = []; // This will store the mistake pairs like b→d, p→q

// const mirrorPairs = [
//   { letter: 'b', options: ['b', 'd'], correct: 'b' },
//   { letter: 'd', options: ['b', 'd'], correct: 'd' },
//   { letter: 'p', options: ['p', 'q'], correct: 'p' },
//   { letter: 'q', options: ['p', 'q'], correct: 'q' },
//   { letter: 'm', options: ['m', 'w'], correct: 'm' },
//   { letter: 'w', options: ['m', 'w'], correct: 'w' },
//   { letter: 'n', options: ['n', 'u'], correct: 'n' },
//   { letter: 'u', options: ['n', 'u'], correct: 'u' }
// ];

// // Shuffle the flashcards
// function shuffle(array) {
//   return array.sort(() => Math.random() - 0.5);
// }

// let shuffled = shuffle([...mirrorPairs, ...mirrorPairs]); // double up for practice
// let current = 0;

// // Function to load the next card
// function loadCard() {
//   if (current >= shuffled.length) {
//     flashcard.innerText = '🎉 All Done!';
//     buttonContainer.innerHTML = '';
//     feedback.innerText = '';
//     scoreBoard.innerText = `Final Score: ${score}/${total}`;
    
//     // Display the log of mistakes (for tracking)
//     console.log('Mistake Log:', errorLog);

//     return;
//   }

//   const card = shuffled[current];
//   flashcard.innerText = card.letter;
//   buttonContainer.innerHTML = '';

//   // Create buttons for options (b/d, p/q, etc.)
//   card.options.forEach(option => {
//     const btn = document.createElement('button');
//     btn.innerText = option;
//     btn.className = 'option-button';
//     btn.onclick = () => checkAnswer(option, card);
//     buttonContainer.appendChild(btn);
//   });

//   feedback.innerText = '';
//   scoreBoard.innerText = `Score: ${score}/${total}`;
// }

// // Function to check the answer
// function checkAnswer(answer, card) {
//   total++;

//   if (card.correct === answer) {
//     feedback.innerText = '✅ Correct!';
//     feedback.style.color = 'green';
//     score++;
//   } else {
//     feedback.innerText = `❌ Incorrect! It's "${card.correct}"`;
//     feedback.style.color = 'red';

//     // Log the mistake (e.g., "b→d")
//     const mistake = `${card.letter}→${card.correct}`;
//     errorLog.push(mistake);
//   }

//   current++;
//   setTimeout(loadCard, 1000);
// }

// // Start the flashcards
// loadCard();
