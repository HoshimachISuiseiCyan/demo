import axios from "axios";

const api = axios.create({
  baseURL: "http://127.0.0.1:8000",
});

export const fetchQuestions = (userId) =>
  api.get(`/questions?user_id=${userId}`);

export const submitAnswer = (data) =>
  api.post("/answer", data);

export const uploadText = (data) =>
  api.post("/upload", data);

export default api;