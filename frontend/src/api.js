// src/api.js
import axios from "axios";

export const api = axios.create({
  baseURL: "http://127.0.0.1:8000"
});

await api.post("/generate", {
  bank_id: currentBank.id,
  text: learningInput
});

const res = await api.get("/questions", {
  params: { bank_id: currentBank.id }
});
setQuestions(res.data);

await api.post("/answer", {
  question_id: q.id,
  is_correct: selected === q.answer
});