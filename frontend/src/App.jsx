import { useEffect, useState } from "react";

const API = "http://127.0.0.1:8000";

function App() {
  const [file, setFile] = useState(null);
  const [message, setMessage] = useState("");
  const [repeated, setRepeated] = useState([]);
  const [questions, setQuestions] = useState([]);

  async function loadData() {
    try {
      const repRes = await fetch(`${API}/repeated`);
      setRepeated(await repRes.json());

      const qRes = await fetch(`${API}/questions`);
      setQuestions(await qRes.json());
    } catch (err) {
      setMessage("Could not reach the backend. Is it running?");
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  async function handleUpload() {
    if (!file) {
      setMessage("Please choose a PDF first.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);
    setMessage("Uploading...");

    try {
      const res = await fetch(`${API}/upload`, {
        method: "POST",
        body: formData,
      });
      const data = await res.json();

      if (data.total_questions === undefined) {
        setMessage(data.message || "Something went wrong.");
      } else {
        setMessage(
          `Saved ${data.total_questions} questions. Repeated from earlier papers: ${data.repeated_from_earlier_papers}`
        );
      }
      await loadData();
    } catch (err) {
      setMessage("Could not reach the backend. Is it running?");
    }
  }

  // group_id -> किती वेगवेगळ्या पेपरमध्ये आला
  const papersPerGroup = {};
  questions.forEach((q) => {
    if (!papersPerGroup[q.group_id]) {
      papersPerGroup[q.group_id] = new Set();
    }
    papersPerGroup[q.group_id].add(q.paper_id);
  });

  // paper_id -> त्या पेपरचे प्रश्न
  const byPaper = {};
  questions.forEach((q) => {
    if (!byPaper[q.paper_id]) {
      byPaper[q.paper_id] = [];
    }
    byPaper[q.paper_id].push(q);
  });

  const badgeStyle = {
    background: "#fde68a",
    color: "#7c2d12",
    borderRadius: 12,
    padding: "2px 10px",
    fontSize: 13,
    marginLeft: 8,
  };

  return (
    <div style={{ maxWidth: 800, margin: "0 auto", padding: 24, textAlign: "left" }}>
      <h1>PaperMind</h1>
      <p>Upload an SPPU question paper (PDF with typed text).</p>

      <input
        type="file"
        accept="application/pdf"
        onChange={(e) => setFile(e.target.files[0])}
      />
      <button onClick={handleUpload} style={{ marginLeft: 12 }}>
        Upload
      </button>

      <p>{message}</p>

      <h2>Repeated questions</h2>
      {repeated.length === 0 && <p>No repeated questions yet.</p>}
      <ul>
        {repeated.map((item) => (
          <li key={item.group_id} style={{ marginBottom: 12 }}>
            <strong>Repeated {item.times_repeated} times</strong>
            <br />
            {item.question}
          </li>
        ))}
      </ul>

      <h2>All papers</h2>
      {questions.length === 0 && <p>No papers uploaded yet.</p>}
      {Object.keys(byPaper).map((paperId) => (
        <div key={paperId} style={{ marginBottom: 24 }}>
          <h3>Paper {paperId}</h3>
          <ul>
            {byPaper[paperId].map((q) => {
              const count = papersPerGroup[q.group_id].size;
              return (
                <li key={q.id} style={{ marginBottom: 8 }}>
                  <strong>
                    {q.question_no}
                    {q.part})
                  </strong>{" "}
                  {q.text}
                  {count > 1 && (
                    <span style={badgeStyle}>Seen in {count} papers</span>
                  )}
                </li>
              );
            })}
          </ul>
        </div>
      ))}
    </div>
  );
}

export default App;