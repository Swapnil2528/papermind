import { useEffect, useState } from "react";

const API = "http://127.0.0.1:8000";

function App() {
  const [file, setFile] = useState(null);
  const [message, setMessage] = useState("");
  const [repeated, setRepeated] = useState([]);

  async function loadRepeated() {
    try {
      const res = await fetch(`${API}/repeated`);
      const data = await res.json();
      setRepeated(data);
    } catch (err) {
      setMessage("Could not reach the backend. Is it running?");
    }
  }

  useEffect(() => {
    loadRepeated();
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
      await loadRepeated();
    } catch (err) {
      setMessage("Could not reach the backend. Is it running?");
    }
  }

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
    </div>
  );
}

export default App;