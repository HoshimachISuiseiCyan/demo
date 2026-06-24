import { create } from "zustand";
import { v4 as uuid } from "uuid";

export const useStore = create((set, get) => ({
  banks: [
  {
    id: "default",
    name: "默认题库",
    questions: [
      {
        id: 1,
        question: "测试题：1+1等于？",
        options: ["A.1", "B.2", "C.3", "D.4"],
        answer: "B"
      }
    ]
  }
],

  setQuestions: (questions) => {
    const { currentBankId, banks } = get();
    const updated = banks.map(b =>
      b.id === currentBankId ? { ...b, questions } : b
    );
    set({ banks: updated, currentIndex: 0, answers: {} });
  },

  selectAnswer: (qid, answer) => {
    set(state => ({
      answers: { ...state.answers, [qid]: answer }
    }));
  },

  nextQuestion: () => {
    set(state => ({
      currentIndex: state.currentIndex + 1
    }));
  },

  addBank: () => {
    const id = uuid();
    set(state => ({
      banks: [...state.banks, { id, name: "新题库", questions: [] }],
      currentBankId: id,
      currentIndex: 0,
    }));
  },

  switchBank: (id) => {
    set({
      currentBankId: id,
      currentIndex: 0,
      answers: {}
    });
  }
}));



