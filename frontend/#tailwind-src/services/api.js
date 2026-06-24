export const fetchQuestions = async (bankId) => {
  const res = await axios.get(
    `http://127.0.0.1:8000/questions?user_id=demo_user&bank_id=${bankId}`
  );
  return res.data.questions || [];
};