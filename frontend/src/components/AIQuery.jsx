import { useState } from "react";
import { askAI } from "../services/api";

function AIQuery() {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();

    setLoading(true);

    try {
      const data = await askAI(question);
      setResult(data);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <h2>Ask AI</h2>

      <form onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="Ex: Which hospitals have a rating of 5?"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
        />

        <button type="submit" disabled={loading || !question}>
          {loading ? "Retrieving..." : "Ask"}
        </button>
      </form>

      {result && (
        <div>
          <h3>Explanation</h3>
          <p>{result.explanation}</p>

          <h3>Results</h3>

          {result && result.results && result.results.map((row, index) => (
            <pre key={index}>
              {JSON.stringify(row, null, 2)}
            </pre>
          ))}
        </div>
      )}
    </div>
  );
}

export default AIQuery;