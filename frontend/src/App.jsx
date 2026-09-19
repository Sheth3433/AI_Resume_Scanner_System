import { useMemo, useState } from 'react'
import './App.css'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'

function App() {
  const [resumeFile, setResumeFile] = useState(null)
  const [jobDescription, setJobDescription] = useState('')
  const [status, setStatus] = useState('Ready')
  const [result, setResult] = useState(null)

  const scoreCards = useMemo(
    () => result ? [
      { label: 'Compatibility', value: result.scores.compatibility },
      { label: 'Semantic Match', value: result.scores.semantic_match },
      { label: 'Skill Match', value: result.scores.skill_match },
      { label: 'Keyword Coverage', value: result.scores.keyword_match },
    ] : [],
    [result],
  )

  const handleFileChange = (event) => {
    const file = event.target.files?.[0]
    setResumeFile(file || null)
    setStatus(file ? 'File ready for upload' : 'Ready')
  }

  const handleAnalyze = async () => {
    if (!resumeFile) {
      setStatus('Choose a resume first')
      return
    }

    setStatus('Analyzing resume...')
    const formData = new FormData()
    formData.append('file', resumeFile)
    formData.append('job_description', jobDescription)

    try {
      const response = await fetch(`${API_BASE_URL}/resume/analyze`, {
        method: 'POST',
        body: formData,
      })
      const payload = await response.json()
      if (!response.ok) {
        throw new Error(payload.detail || 'Resume analysis failed.')
      }
      setResult(payload)
      setStatus('Results ready')
    } catch (error) {
      setStatus(error.message || 'Backend unavailable')
    }
  }

  return (
    <div className="page-shell">
      <header className="topbar">
        <div className="brand-wrap">
          <div className="brand-badge">AI</div>
          <div>
            <p className="eyebrow">Resume Intelligence</p>
            <h1>AI Resume Scanner & Job Matcher</h1>
          </div>
        </div>
        <nav className="topnav">
          <a href="#scanner">Scanner</a>
          <a href="#dashboard">Dashboard</a>
          <a href="#privacy">Privacy</a>
        </nav>
      </header>

      <main className="content-grid" id="scanner">
        <section className="panel upload-panel">
          <div className="panel-header">
            <span className="pill">Upload Resume</span>
            <span className="status">{status}</span>
          </div>

          <div className="dropzone">
            <input type="file" accept=".pdf,.doc,.docx" onChange={handleFileChange} />
            <div className="dropzone-text">
              <strong>Drag & drop your resume</strong>
              <span>PDF, DOCX, or DOC • Max 10MB</span>
            </div>
          </div>

          {resumeFile ? (
            <div className="file-meta">
              <div>
                <label>Filename</label>
                <p>{resumeFile.name}</p>
              </div>
              <div>
                <label>Type</label>
                <p>{resumeFile.type || 'Unknown'}</p>
              </div>
              <div>
                <label>Size</label>
                <p>{(resumeFile.size / 1024 / 1024).toFixed(2)} MB</p>
              </div>
            </div>
          ) : null}

          <label className="field-label">Job Description (optional)</label>
          <textarea
            value={jobDescription}
            onChange={(event) => setJobDescription(event.target.value)}
            placeholder="Paste the job description here to compare skills, experience, and education requirements..."
          />

          <div className="actions">
            <button className="primary" onClick={handleAnalyze}>Scan Resume</button>
            <button className="secondary" type="button">View Privacy</button>
          </div>

          <p className="privacy-note">
            Privacy notice: Resume data is processed locally in the application layer and is not sent to third-party APIs unless explicitly configured.
          </p>
        </section>

        <section className="panel job-panel">
          <div className="panel-header">
            <span className="pill alt">Processing Pipeline</span>
          </div>

          <ul className="process-list">
            <li>1. Read document</li>
            <li>2. Extract contact and skills</li>
            <li>3. Detect resume sections</li>
            <li>4. Compare job requirements</li>
          </ul>
        </section>
      </main>

      <section className="dashboard" id="dashboard">
        {!result ? <div className="empty-state">Upload a resume and click Scan Resume to see results.</div> : null}
        {result ? <>
        <div className="score-overview">
          {scoreCards.map((card) => (
            <div className="score-card" key={card.label}>
              <span>{card.label}</span>
              <strong>{card.value}</strong>
            </div>
          ))}
        </div>

        <div className="analysis-grid">
          <div className="panel">
            <h2>Matched Skills</h2>
            <div className="tag-list">
              {result.matched_skills.map((skill) => (
                <span key={skill} className="tag success">{skill}</span>
              ))}
            </div>
          </div>

          <div className="panel">
            <h2>Missing Skills</h2>
            <div className="tag-list">
              {result.missing_skills.map((skill) => (
                <span key={skill} className="tag warning">{skill}</span>
              ))}
            </div>
          </div>

          <div className="panel">
            <h2>Resume Information</h2>
            <dl className="meta-list">
              <div><dt>Name</dt><dd>{result.resume.name}</dd></div>
              <div><dt>Email</dt><dd>{result.resume.email}</dd></div>
              <div><dt>Sections</dt><dd>{result.resume.sections_detected.join(', ')}</dd></div>
            </dl>
          </div>

          <div className="panel">
            <h2>Recommendations</h2>
            <ul className="recommendation-list">
              {result.recommendations.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>

          <div className="panel full-width">
            <h2>Detected Resume Summary</h2>
            <p className="summary-text">{result.summary}</p>
            {result.issues.length ? <ul className="recommendation-list">{result.issues.map((item) => <li key={item}>{item}</li>)}</ul> : null}
          </div>
        </div>
        </> : null}
      </section>
    </div>
  )
}

export default App
