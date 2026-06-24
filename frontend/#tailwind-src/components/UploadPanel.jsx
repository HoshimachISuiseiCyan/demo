import { useState } from "react";
import { uploadText, fetchQuestions } from "../api/client";
import { useStore } from "../store/useStore";

export default function UploadPanel() {
  const [text, setText] = useState("");
  const setQuestions = useStore(state => state.setQuestions);

  const handleUpload = async () => {
    await uploadText(text);
    const res = await fetchQuestions("demo_user");
    setQuestions(res.data.questions);
  };

  return (
    <div className="p-4">
      <textarea
        className="w-full border p-2"
        rows={5}
        value={text}
        onChange={e => setText(e.target.value)}
        placeholder="粘贴学习内容..."
      />

      <button
        onClick={handleUpload}
        className="mt-2 bg-green-500 text-white px-4 py-2 rounded"
      >
        生成题目
      </button>
    </div>
  );
}