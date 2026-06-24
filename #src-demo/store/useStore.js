import { create } from "zustand";
import { v4 as uuidv4 } from "uuid";

export const useStore = create((set, get) => ({
  libraries: [
    { id: "default", name: "默认题库", questions: [] }
  ],
  currentLibId: "default",

  // 切换题库
  setCurrentLib: (id) => set({ currentLibId: id }),

  // 新建题库
  addLibrary: () =>
    set((state) => ({
      libraries: [
        ...state.libraries,
        { id: uuidv4(), name: "新题库", questions: [] },
      ],
    })),

  // 删除题库
  deleteLibrary: (id) =>
    set((state) => ({
      libraries: state.libraries.filter((l) => l.id !== id),
    })),

  // 重命名
  renameLibrary: (id, name) =>
    set((state) => ({
      libraries: state.libraries.map((l) =>
        l.id === id ? { ...l, name } : l
      ),
    })),

  // 设置题目
  setQuestions: (questions) => {
    const { libraries, currentLibId } = get();
    set({
      libraries: libraries.map((l) =>
        l.id === currentLibId ? { ...l, questions } : l
      ),
    });
  },
}));