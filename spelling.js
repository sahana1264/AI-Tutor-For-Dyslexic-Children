const submitBtn = document.getElementById('submit-btn');
const retryBtn = document.getElementById('retry-button');
const feedbackDiv = document.getElementById('feedback');
const wordDiv = document.getElementById('word');
const spellingInput = document.getElementById('spelling-input');

const wordsToPractice = ['apple', 'banana', 'grape', 'orange', 'peach'];
let currentWord = '';
let score = 0;

// Shuffle the words to practice
function shuffle(array) {
  return array.sort(() => Math.random() - 0.5);
}

let shuffledWords = shuffle(wordsToPractice);
let currentIndex = 0;

// Load the next word to spell
function loadNextWord() {
  if (currentIndex >= shuffledWords.length) {
    wordDiv.innerText = '🎉 All Done!';
    feedbackDiv.innerText = `Your final score: ${score}`;
    submitBtn.style.display = 'none';
    retryBtn.style.display = 'none';
    return;
  }

  currentWord = shuffledWords[currentIndex];
  wordDiv.innerText = currentWord;
  spellingInput.value = '';
  feedbackDiv.innerText = '';
  retryBtn.style.display = 'none';
  submitBtn.style.display = 'inline-block';
}

// Check spelling and provide feedback
function checkSpelling() {
  const userInput = spellingInput.value.trim().toLowerCase();

  if (userInput === currentWord) {
    feedbackDiv.innerText = '✅ Correct!';
    feedbackDiv.style.color = 'green';
    score++;
  } else {
    feedbackDiv.innerText = `❌ Incorrect! The correct spelling is "${currentWord}".`;
    feedbackDiv.style.color = 'red';
    retryBtn.style.display = 'inline-block';
    submitBtn.style.display = 'none';
  }

  currentIndex++;
  setTimeout(loadNextWord, 1000);
}

// Retry the spelling
function retrySpelling() {
  feedbackDiv.innerText = '';
  spellingInput.value = '';
  submitBtn.style.display = 'inline-block';
  retryBtn.style.display = 'none';
}

submitBtn.addEventListener('click', checkSpelling);
retryBtn.addEventListener('click', retrySpelling);

// Load the first word
loadNextWord();
