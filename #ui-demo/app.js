const API = "http://127.0.0.1:8000";

let currentQuestions = [];
let currentIndex = 0;

// 上传文本 → 生成题目
document.getElementById("uploadBtn").onclick = async () => {
    const text = document.getElementById("inputText").value;

    await fetch(API + "/upload", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({text})
    });

    loadQuestions();
};

// 获取题目
async function loadQuestions() {
    const res = await fetch(API + "/questions?user_id=demo_user");
    const data = await res.json();

    currentQuestions = data.questions;
    currentIndex = 0;

    showQuestion();
}

// 显示单题
function showQuestion() {
    const q = currentQuestions[currentIndex];
    const box = document.getElementById("questionBox");

    box.classList.remove("hidden");

    box.innerHTML = `
        <h3>${q.question}</h3>
        ${q.options.map(opt => `
            <div class="option" onclick="selectAnswer('${opt[0]}')">
                ${opt}
            </div>
        `).join("")}
        <button onclick="nextQuestion()">下一题</button>
    `;
}

// 选答案
function selectAnswer(ans) {
    const q = currentQuestions[currentIndex];

    if (ans === q.answer) {
        alert("✅ 正确");
    } else {
        alert("❌ 错误，正确答案是 " + q.answer);
    }
}

// 下一题
function nextQuestion() {
    currentIndex++;
    if (currentIndex < currentQuestions.length) {
        showQuestion();
    } else {
        alert("做完啦！");
    }
}