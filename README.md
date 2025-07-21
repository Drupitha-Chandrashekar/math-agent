# math-agent
# 🧠 Agentic AI Math Tutor

An intelligent, LLM-powered math tutoring system that uses **Agentic RAG**, **LangChain**, and **Gemini** to generate step-by-step solutions to math problems with explainability and web fallback. It integrates **semantic search**, **web search APIs**, and a **feedback loop** for continuous improvement.

---

## 🚀 Features

- 📚 **Semantic Search over Knowledge Base** using `Qdrant` + `SentenceTransformers`
- 🤖 **LangChain-style Agent Orchestration** for tool routing and context switching
- 🧠 **Gemini 1.5 Flash** LLM for detailed step-by-step solution generation
- 🔐 **Input/Output Guardrails** to ensure safe, math-only and student-friendly answers
- 🌍 **Web Search Fallback** using `Tavily` and `Serper` APIs
- 🗣 **Human-in-the-Loop Feedback System** to capture and use user feedback effectively

---

## 🧰 Tech Stack

| Tool | Purpose |
|------|---------|
| `Python` | Core logic |
| `LangChain` | Agent routing and orchestration |
| `Qdrant` | Vector store for semantic KB |
| `SentenceTransformers` | Embedding generation |
| `Gemini 1.5 Flash` | Step-by-step LLM reasoning |
| `Tavily`, `Serper` | Web search integration |
| `Streamlit` | Frontend UI |
| `FeedbackHandler` | Human feedback integration |

---


## 📸 Screenshots

_Add screenshots of your UI or console output here_

---

## 👨‍💻 Author

**Drupitha Chandrashekar**  
[GitHub](https://github.com/Drupitha-Chandrashekar) | [LinkedIn](https://www.linkedin.com/in/drupitha-chandrashekar-47511a25b/)

---

## 📄 License

This project is under the MIT License.
