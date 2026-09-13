import { useState } from "react";
import "./App.css";

function App() {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);

  const handleFileChange = (event) => {
    const selectedFile = event.target.files[0];

    if (selectedFile) {
      setFile(selectedFile);
      setResult(null);
      setErrorMsg(null);
    }
  };

  const uploadResume = async () => {
    if (!file) {
      alert("Please select a PDF resume first.");
      return;
    }

    setLoading(true);
    setResult(null);
    setErrorMsg(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch(
  "https://ai-resume-analyzer-08ag.onrender.com/upload-resume",
        {
          method: "POST",
          body: formData,
        }
      );

      // Check status BEFORE trying to parse JSON
      if (!response.ok) {
        let detail = "";
        try {
          const errData = await response.json();
          detail = errData.detail || JSON.stringify(errData);
        } catch {
          detail = await response.text();
        }
        throw new Error(
          `Server error (${response.status}): ${detail}`
        );
      }

      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error("Upload error:", error);

      if (error.message === "Failed to fetch") {
        setErrorMsg(
          "Could not reach the backend. Make sure the FastAPI server " +
          "is running on http://127.0.0.1:8000 and CORS is enabled."
        );
      } else {
        setErrorMsg(error.message);
      }
    }

    setLoading(false);
  };

  return (
    <div className="container">

      <div className="hero">

        <h1>
          AI Resume <span>Analyzer</span>
        </h1>

        <p>
          Analyze your resume, match it with jobs, and improve your chances
          of getting shortlisted.
        </p>

        <div className="upload-box">

          <h2>Analyze Your Resume</h2>

          <p>
            Upload your PDF resume and let AI analyze your skills,
            projects and experience.
          </p>

          <input
            type="file"
            accept=".pdf"
            id="resume-upload"
            onChange={handleFileChange}
            hidden
          />

          <label htmlFor="resume-upload" className="upload-btn">
            Choose Resume
          </label>

          {file && (
            <p className="file-name">
              Selected: {file.name}
            </p>
          )}

          {file && (
            <button
              className="analyze-btn"
              onClick={uploadResume}
              disabled={loading}
            >
              {loading ? "Analyzing..." : "Analyze Resume"}
            </button>
          )}

          {errorMsg && (
            <p style={{ color: "red", marginTop: "15px" }}>
              {errorMsg}
            </p>
          )}

        </div>

        {result && (
          <div className="results">

            <h2>Resume Information</h2>

            <div className="score-card">
              <h3>ATS-Style Resume Score</h3>
              <div className="score">
                {result.score}/100
              </div>
              <p>
                This is an ATS-style score based on resume content and structure.
              </p>
            </div>

            <div className="info-card">
              <p>
                <strong>Email:</strong> {result.email}
              </p>

              <p>
                <strong>Phone:</strong> {result.phone}
              </p>

              <div className="skills-section">
                <strong>Skills:</strong>

                <div className="skills-list">
                  {result.skills && result.skills.length > 0 ? (
                    result.skills.map((skill) => (
                      <span className="skill-badge" key={skill}>
                        {skill}
                      </span>
                    ))
                  ) : (
                    <span>No skills detected</span>
                  )}
                </div>
              </div>

              <p>
                <strong>File:</strong> {result.filename}
              </p>
            </div>

            <div className="text-card">
              <h3>Extracted Resume Text</h3>

              <pre>{result.text}</pre>
            </div>

          </div>
        )}

      </div>

      <div className="features">

        <div className="feature">
          <h3>📄 Resume Analysis</h3>
          <p>
            Extract and analyze important information from your resume.
          </p>
        </div>

        <div className="feature">
          <h3>🎯 Job Matching</h3>
          <p>
            Compare your resume with a job description and find missing skills.
          </p>
        </div>

        <div className="feature">
          <h3>🤖 AI Suggestions</h3>
          <p>
            Get intelligent recommendations to improve your resume.
          </p>
        </div>

      </div>

    </div>
  );
}

export default App;