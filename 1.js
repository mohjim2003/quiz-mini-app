async function loadQuestions() {
  try {
    const response = await fetch("/questions");
    const questions = await response.json();

    const container = document.getElementById("quiz");
    container.innerHTML = "";

    questions.forEach((q, index) => {
      const div = document.createElement("div");
      div.classList.add("question-block");

      div.innerHTML = `
        <h3>${index + 1}. ${q.question}</h3>
        <ul>
          ${q.options.map(opt => `<li><button onclick="checkAnswer('${opt}', '${q.answer}')">${opt}</button></li>`).join("")}
        </ul>
      `;
      container.appendChild(div);
    });
  } catch (err) {
    console.error("Kunde inte ladda frågor:", err);
  }
}

function checkAnswer(selected, correct) {
  if (selected === correct) {
    alert("Rätt svar! 🎉");
  } else {
    alert(`Fel svar 😢 Rätt svar är: ${correct}`);
  }
}

window.onload = loadQuestions;
