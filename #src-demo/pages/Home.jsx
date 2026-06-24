import { useEffect, useState } from "react";
import { fetchQuestions } from "../api/client";
import { useStore } from "../store/useStore";
import QuestionCard from "../components/QuestionCard";

export default function Home() {
  const { setQuestions, libraries, currentLibId } = useStore();
  const [index, setIndex] = useState(0);

  const currentLib = libraries.find(l => l.id === currentLibId);

  useEffect(() => {
    fetchQuestions("demo_user").then((res) => {
      setQuestions(res.data.questions);
    });
  }, []);

  if (!currentLib || currentLib.questions.length === 0)
    return <div className="p-6">暂无题目</div>;

  const q = currentLib.questions[index];

  return (
    <div className="flex-1 p-6">
      <QuestionCard question={q} />

      <button
        onClick={() => setIndex(index + 1)}
        className="mt-4 bg-green-500 text-white px-4 py-2"
      >
        下一题 →
      </button>
    </div>
  );
}