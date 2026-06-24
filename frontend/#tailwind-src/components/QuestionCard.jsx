import { useStore } from "../store/useStore";

export default function QuestionCard() {
  const {
    banks,
    currentBankId,
    currentIndex,
    selectAnswer,
    answers,
    nextQuestion,
  } = useStore();

  const bank = banks.find(b => b.id === currentBankId);

  // ⭐ 关键：防止 undefined 崩溃
  if (!bank || !bank.questions || bank.questions.length === 0) {
    return (
      <div className="text-gray-500 text-center mt-10">
        暂无题目 👉 请先上传内容生成题目
      </div>
    );
  }

  const question = bank.questions[currentIndex];

  if (!question) {
    return (
      <div className="text-gray-500 text-center mt-10">
        已做完所有题目 🎉
      </div>
    );
  }

  const userAnswer = answers[question.id];

  return (
    <div className="p-6 bg-white rounded shadow w-full max-w-xl">
      <h2 className="text-lg mb-4">{question.question}</h2>

      {question.options.map((opt, i) => {
        const letter = opt[0];

        const isCorrect = letter === question.answer;
        const isSelected = userAnswer === letter;

        let color = "bg-gray-100";

        if (userAnswer) {
          if (isCorrect) color = "bg-green-200";
          else if (isSelected) color = "bg-red-200";
        }

        return (
          <div
            key={i}
            onClick={() => selectAnswer(question.id, letter)}
            className={`p-2 my-2 rounded cursor-pointer ${color}`}
          >
            {opt}
          </div>
        );
      })}

      <button
        onClick={nextQuestion}
        className="mt-4 bg-blue-500 text-white px-4 py-2 rounded"
      >
        下一题 →
      </button>
    </div>
  );
}