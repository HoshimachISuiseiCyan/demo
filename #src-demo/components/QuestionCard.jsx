import { useState } from "react";
import { submitAnswer } from "../api/client";

export default function QuestionCard({ question }) {
  const [selected, setSelected] = useState(null);
  const [result, setResult] = useState(null);

  const handleSubmit = async () => {
    const res = await submitAnswer({
      question_id: question.id,
      answer: selected,
      user_id: "demo_user",
    });

    setResult(res.data.correct);
  };

  return (
    <div className="bg-white p-6 rounded shadow">
      <h2 className="text-lg mb-4">{question.question}</h2>

      {question.options.map((opt, i) => (
        <div
          key={i}
          onClick={() => setSelected(opt[0])}
          className={`p-2 border rounded mb-2 cursor-pointer ${
            selected === opt[0] ? "bg-blue-200" : ""
          }`}
        >
          {opt}
        </div>
      ))}

      <button
        onClick={handleSubmit}
        className="bg-blue-500 text-white px-4 py-2 mt-4"
      >
        提交
      </button>

      {result !== null && (
        <div className="mt-2">
          {result ? "✅ 正确" : "❌ 错误"}
        </div>
      )}
    </div>
  );
}