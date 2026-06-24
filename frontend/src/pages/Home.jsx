import { useEffect, useMemo, useState } from "react";
import "../styles/main.css";

const DEFAULT_BANKS = [
  {
    id: "bank-default",
    name: "默认题库",
    questions: []
  }
];

const DISTRACTORS = [
  "只看结论，不做练习",
  "临时突击，不做复盘",
  "机械背诵，不理解原理",
  "只收藏资料，不主动输出",
  "跳过错题，不做纠正",
  "只听讲解，不动手验证"
];



function makeId(prefix) {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

function shuffleBySeed(items, seed) {
  const list = [...items];
  for (let i = list.length - 1; i > 0; i -= 1) {
    const mixed = seed.charCodeAt(i % seed.length) + i * 17;
    const j = mixed % (i + 1);
    [list[i], list[j]] = [list[j], list[i]];
  }
  return list;
}

function pickDistractors(correct, seed) {
  const pool = DISTRACTORS.filter((text) => text !== correct);
  return shuffleBySeed(pool, seed).slice(0, 3);
}

function createQuestionFromPoint(point, index, mode) {
  const cleanPoint = point.replace(/\s+/g, " ").trim();
  const shortPoint =
    cleanPoint.length > 24 ? `${cleanPoint.slice(0, 24)}...` : cleanPoint;

  // 🔥 两种模式模板
  const examTemplates = [
    () => {
      const correct = cleanPoint;
      return {
        stem: `以下关于「${shortPoint}」的描述，哪一项是正确的？`,
        correct,
        explanation: "直接来源于原始学习内容。"
      };
    },
    () => {
      const correct = cleanPoint;
      return {
        stem: `下列哪项最符合「${shortPoint}」？`,
        correct,
        explanation: "考察对原文知识点的理解。"
      };
    }
  ];

  const expandTemplates = [
    () => {
      const correct = "主动回忆 + 间隔复习";
      return {
        stem: `针对「${shortPoint}」，哪种学习策略更利于长期记忆？`,
        correct,
        explanation: "主动回忆 + 间隔复习是认知科学推荐策略。"
      };
    },
    () => {
      const correct = `理解“${shortPoint}”并能应用`;
      return {
        stem: `学习「${shortPoint}」的最佳目标是？`,
        correct,
        explanation: "强调迁移能力。"
      };
    }
  ];

  const templates = mode === "exam" ? examTemplates : expandTemplates;
  const template = templates[index % templates.length]();

  const options = shuffleBySeed(
    [template.correct, ...pickDistractors(template.correct, shortPoint)],
    shortPoint
  );

  return {
    id: makeId("q"),
    source: shortPoint,
    stem: template.stem,
    options,
    answer: template.correct,
    explanation: template.explanation
  };
}

function createQuestionsFromText(rawText, mode) {
  const lines = rawText
    .split(/[\n。！？.!?；;]+/)
    .map((item) => item.trim())
    .filter((item) => item.length > 2);

  const uniqueLines = [...new Set(lines)];
  const focusPoints = (uniqueLines.length ? uniqueLines : [rawText.trim()]).slice(0, 6);

  return focusPoints.map((point, index) =>
    createQuestionFromPoint(point, index, mode)
  );
}

function getNextQuestionId(bank, attempts, currentQuestionId) {
  if (!bank || bank.questions.length === 0) {
    return null;
  }

  const unanswered = bank.questions.find((q) => !attempts[q.id]);
  if (unanswered) {
    return unanswered.id;
  }

  const currentIndex = bank.questions.findIndex((q) => q.id === currentQuestionId);
  const nextIndex = currentIndex >= 0 ? (currentIndex + 1) % bank.questions.length : 0;
  return bank.questions[nextIndex].id;
}

export default function Home() {
  const [banks, setBanks] = useState(DEFAULT_BANKS);
  const [currentBankId, setCurrentBankId] = useState(DEFAULT_BANKS[0].id);
  const [learningInput, setLearningInput] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [selectedOption, setSelectedOption] = useState("");
  const [activeQuestionByBank, setActiveQuestionByBank] = useState({});
  const [attempts, setAttempts] = useState({});
  const [mode, setMode] = useState("exam"); 
// exam = 严格模式 / expand = 拓展模式
  const [feed, setFeed] = useState([
    {
      id: makeId("feed"),
      role: "ai",
      text: "欢迎回来，输入学习内容后我会帮你生成题目并推荐练习。"
    }
  ]);

  const currentBank = useMemo(
    () => banks.find((bank) => bank.id === currentBankId) || banks[0],
    [banks, currentBankId]
  );

  const activeQuestion = useMemo(() => {
    if (!currentBank) {
      return null;
    }

    const activeId =
      activeQuestionByBank[currentBank.id] ||
      getNextQuestionId(currentBank, attempts, null);

    return currentBank.questions.find((question) => question.id === activeId) || null;
  }, [activeQuestionByBank, attempts, currentBank]);

  const currentAttempt = activeQuestion ? attempts[activeQuestion.id] : null;
  const totalCount = currentBank?.questions.length || 0;
  const answeredCount =
    currentBank?.questions.filter((question) => Boolean(attempts[question.id])).length || 0;
  const correctCount =
    currentBank?.questions.filter((question) => attempts[question.id]?.isCorrect).length || 0;
  const progress = totalCount ? Math.round((answeredCount / totalCount) * 100) : 0;

  useEffect(() => {
    if (!activeQuestion) {
      setSelectedOption("");
      return;
    }
    setSelectedOption(attempts[activeQuestion.id]?.choice || "");
  }, [activeQuestion, attempts]);

  const handleCreateBank = () => {
    const newBank = {
      id: makeId("bank"),
      name: `题库 ${banks.length + 1}`,
      questions: []
    };

    setBanks((prev) => [...prev, newBank]);
    setCurrentBankId(newBank.id);
    setActiveQuestionByBank((prev) => ({ ...prev, [newBank.id]: null }));
    setFeed((prev) => [
      ...prev,
      { id: makeId("feed"), role: "ai", text: `已创建新题库「${newBank.name}」。` }
    ]);
  };


const handleGenerateQuestions = async () => {
  const trimmed = learningInput.trim();
  if (!trimmed || !currentBank) return;

  setIsGenerating(true);

  try {
    const res = await fetch("http://127.0.0.1:8000/ai/generate", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ text: trimmed, mode: mode }),
    });

    const data = await res.json();

    console.log("🔥 AI返回：", data);

    const newQuestions = data.questions || [];

    setBanks((prev) =>
      prev.map((bank) =>
        bank.id === currentBank.id
          ? { ...bank, questions: [...bank.questions, ...newQuestions] }
          : bank
      )
    );

    setActiveQuestionByBank((prev) => ({
      ...prev,
      [currentBank.id]: prev[currentBank.id] || newQuestions[0]?.id || null,
    }));

    setFeed((prev) => [
      ...prev,
      {
        id: makeId("feed"),
        role: "ai",
        text: `AI已生成 ${newQuestions.length} 道题`,
      },
    ]);

  } catch (err) {
    console.error("❌ 出题失败", err);

    setFeed((prev) => [
      ...prev,
      {
        id: makeId("feed"),
        role: "ai",
        text: "出题失败，请检查后端或API配置",
      },
    ]);
  }

  setIsGenerating(false);
};

  

  const handleSubmitAnswer = () => {
    if (!activeQuestion || !selectedOption) {
      return;
    }

    const isCorrect = selectedOption === activeQuestion.answer;
    setAttempts((prev) => ({
      ...prev,
      [activeQuestion.id]: {
        bankId: currentBank.id,
        choice: selectedOption,
        isCorrect
      }
    }));
    setFeed((prev) => [
      ...prev,
      {
        id: makeId("feed"),
        role: "ai",
        text: isCorrect
          ? "回答正确，已记录到学习进度。"
          : "已收到你的答案，建议看看解析后再继续下一题。"
      }
    ]);
  };

  const handleNextRecommendation = () => {
    if (!currentBank) {
      return;
    }

    const nextId = getNextQuestionId(currentBank, attempts, activeQuestion?.id || null);
    setActiveQuestionByBank((prev) => ({ ...prev, [currentBank.id]: nextId }));
  };

  return (
    <div className="home-layout">
      <aside className="library-panel">
        <div className="panel-head">
          <p className="panel-kicker">Question Banks</p>
          <h1>题库中心</h1>
        </div>

        <div className="bank-list">
          {banks.map((bank) => (
            <button
              key={bank.id}
              className={`bank-item ${bank.id === currentBankId ? "is-active" : ""}`}
              onClick={() => setCurrentBankId(bank.id)}
            >
              <span>{bank.name}</span>
              <small>{bank.questions.length} 题</small>
            </button>
          ))}
        </div>

        <button className="create-bank-btn" onClick={handleCreateBank}>
          + 新建题库
        </button>
      </aside>

      <main className="workspace-panel">
        <section className="hero-card">
          <div>
            <p className="hero-kicker">AI Learning Assistant</p>
            <h2>输入学习内容，自动生成题目并逐题推荐</h2>
          </div>
          <div className="stats-grid">
            <article>
              <span>总题数</span>
              <strong>{totalCount}</strong>
            </article>
            <article>
              <span>已作答</span>
              <strong>{answeredCount}</strong>
            </article>
            <article>
              <span>正确数</span>
              <strong>{correctCount}</strong>
            </article>
            <article>
              <span>进度</span>
              <strong>{progress}%</strong>
            </article>
          </div>
        </section>

        <section className="compose-card">
          <div className="compose-title">
            <h3>学习内容输入</h3>
            <p>当前题库：{currentBank?.name || "未选择"}</p>
          </div>
          <div style={{ marginBottom: "10px" }}>
  <button
    onClick={() => setMode("exam")}
    style={{
      marginRight: "8px",
      background: mode === "exam" ? "#4f46e5" : "#ddd",
      color: mode === "exam" ? "#fff" : "#000"
    }}
  >
    考试模式
  </button>

  <button
    onClick={() => setMode("expand")}
    style={{
      background: mode === "expand" ? "#4f46e5" : "#ddd",
      color: mode === "expand" ? "#fff" : "#000"
    }}
  >
    拓展模式
  </button>
</div>
          <textarea
            value={learningInput}
            onChange={(event) => setLearningInput(event.target.value)}
            placeholder="例如：二分查找的原理、时间复杂度、边界条件与常见错误..."
          />
          <button
            className="generate-btn"
            onClick={handleGenerateQuestions}
            disabled={isGenerating || !learningInput.trim()}
          >
            {isGenerating ? "AI 正在出题..." : "生成题目"}
          </button>
        </section>

        <section className="practice-card">
          <div className="practice-head">
            <h3>AI 推荐题</h3>
            <button className="next-btn" onClick={handleNextRecommendation}>
              下一题推荐
            </button>
          </div>

          {!activeQuestion ? (
            <div className="empty-state">
              当前题库还没有题目，先在上方输入学习内容并点击“生成题目”。
            </div>
          ) : (
            <div className="question-content">
              <p className="question-source">主题：{activeQuestion.source}</p>
              <h4>{activeQuestion.stem}</h4>
              <div className="option-list">
                {activeQuestion.options.map((option) => {
                  const isSelected = selectedOption === option;
                  const isAnswer = currentAttempt && option === activeQuestion.answer;
                  const isWrongSelected =
                    currentAttempt && option === currentAttempt.choice && !currentAttempt.isCorrect;

                  return (
                    <button
                      key={option}
                      className={`option-btn ${isSelected ? "is-selected" : ""} ${
                        isAnswer ? "is-answer" : ""
                      } ${isWrongSelected ? "is-wrong" : ""}`}
                      onClick={() => setSelectedOption(option)}
                      disabled={Boolean(currentAttempt)}
                    >
                      {option}
                    </button>
                  );
                })}
              </div>

              <div className="question-actions">
                <button
                  className="submit-btn"
                  onClick={handleSubmitAnswer}
                  disabled={!selectedOption || Boolean(currentAttempt)}
                >
                  提交答案
                </button>
              </div>

              {currentAttempt && (
                <div className={`analysis-box ${currentAttempt.isCorrect ? "ok" : "bad"}`}>
                  <p>{currentAttempt.isCorrect ? "回答正确" : "回答错误"}</p>
                  <p>解析：{activeQuestion.explanation}</p>
                </div>
              )}
            </div>
          )}
        </section>

        <section className="feed-card">
          <h3>学习动态</h3>
          <div className="feed-list">
            {feed.slice(-6).map((item) => (
              <div key={item.id} className={`feed-item ${item.role}`}>
                {item.text}
              </div>
            ))}
          </div>
        </section>
      </main>
    </div>
  );

}