import { useEffect, useMemo, useState } from 'react'
import './App.css'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'
const MAX_FILE_SIZE = 10 * 1024 * 1024
const SESSION_KEY = 'resumeScannerToken'
const ANALYSIS_STAGES = [
  'Reading document',
  'Extracting resume information',
  'Detecting skills and sections',
  'Comparing job requirements',
  'Preparing recommendations',
]

function validateFile(file) {
  const extension = file.name.split('.').pop()?.toLowerCase()
  if (!['pdf', 'docx'].includes(extension)) return 'Choose a PDF or DOCX file.'
  if (file.size === 0) return 'This file is empty. Choose another document.'
  if (file.size > MAX_FILE_SIZE) return 'The maximum file size is 10 MB.'
  return ''
}

async function authenticatedFetch(path, options = {}) {
  const headers = new Headers(options.headers || {})
  const token = window.sessionStorage.getItem(SESSION_KEY)
  if (token) headers.set('Authorization', `Bearer ${token}`)
  const response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers })
  if (response.status === 401 && token) {
    window.sessionStorage.removeItem(SESSION_KEY)
    window.dispatchEvent(new Event('resume-scanner-session-expired'))
  }
  return response
}

function App() {
  const [authToken, setAuthToken] = useState(() => window.sessionStorage.getItem(SESSION_KEY) || '')
  const [authMode, setAuthMode] = useState('login')
  const [authEmail, setAuthEmail] = useState('')
  const [authPassword, setAuthPassword] = useState('')
  const [authError, setAuthError] = useState('')
  const [isAuthenticating, setIsAuthenticating] = useState(false)
  const [resumeFile, setResumeFile] = useState(null)
  const [jobDescription, setJobDescription] = useState('')
  const [targetRole, setTargetRole] = useState('')
  const [availableRoles, setAvailableRoles] = useState([])
  const [error, setError] = useState('')
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [stageIndex, setStageIndex] = useState(0)
  const [result, setResult] = useState(null)
  const [history, setHistory] = useState([])
  const [historyError, setHistoryError] = useState('')
  const [selectedHistoryIds, setSelectedHistoryIds] = useState([])
  const [comparison, setComparison] = useState(null)
  const [isHistoryLoading, setIsHistoryLoading] = useState(true)
  const [improvementKind, setImprovementKind] = useState('summary')
  const [improvementInput, setImprovementInput] = useState('')
  const [improvementResult, setImprovementResult] = useState(null)
  const [isImproving, setIsImproving] = useState(false)
  const [improvementError, setImprovementError] = useState('')
  const [settings, setSettings] = useState(null)
  const [settingsError, setSettingsError] = useState('')
  const [isClearingHistory, setIsClearingHistory] = useState(false)

  useEffect(() => {
    const expireSession = () => {
      setAuthToken('')
      setHistory([])
      setResult(null)
      setAuthError('Your session expired. Sign in again.')
    }
    window.addEventListener('resume-scanner-session-expired', expireSession)
    return () => window.removeEventListener('resume-scanner-session-expired', expireSession)
  }, [])

  const scoreCards = useMemo(
    () => result ? [
      { label: 'Job compatibility', value: result.scores.compatibility, note: result.job.skills?.length || result.role_analysis ? 'Weighted match to the selected job target' : 'Resume completeness heuristic; no job target' },
      { label: result.ats_analysis?.label || 'Estimated ATS', value: result.scores.ats_compatibility, note: result.ats_analysis?.score_basis === 'job_targeted' ? '60% semantic + 40% exact skill coverage' : 'Document structure and content checks' },
      { label: 'Semantic match', value: result.scores.semantic_match, note: result.semantic_match_source === 'sentence-transformers' ? 'Sentence-transformer similarity' : result.semantic_match_source },
      { label: 'Skill match', value: result.scores.skill_match, note: result.job.skills?.length ? 'Required skills weighted above preferred' : result.role_analysis ? 'Alternative skill groups covered' : result.ats_analysis?.score_basis === 'job_targeted' ? 'No known skill terms; exact-skill factor is neutral' : 'Add a job target to calculate' },
      { label: 'Keyword overlap', value: result.scores.keyword_match, note: 'Token-count cosine similarity' },
    ] : [],
    [result],
  )

  useEffect(() => {
    if (!isAnalyzing) return undefined
    const timer = window.setInterval(() => {
      setStageIndex((index) => (index + 1) % ANALYSIS_STAGES.length)
    }, 1200)
    return () => window.clearInterval(timer)
  }, [isAnalyzing])

  const chooseFile = (file) => {
    if (!file) return
    const validationError = validateFile(file)
    setError(validationError)
    setResumeFile(validationError ? null : file)
    setResult(null)
  }

  const loadHistory = async () => {
    setIsHistoryLoading(true)
    setHistoryError('')
    try {
      const response = await authenticatedFetch('/resumes/history')
      const payload = await response.json().catch(() => [])
      if (!response.ok) throw new Error(payload.detail || 'Could not load saved analyses.')
      setHistory(payload)
    } catch (loadError) {
      setHistoryError(loadError.message || 'Could not reach the analysis service.')
    } finally {
      setIsHistoryLoading(false)
    }
  }

  useEffect(() => {
    if (!authToken) return undefined
    let isActive = true
    const fetchInitialHistory = async () => {
      try {
        const response = await authenticatedFetch('/resumes/history')
        const payload = await response.json().catch(() => [])
        if (!response.ok) throw new Error(payload.detail || 'Could not load saved analyses.')
        if (isActive) setHistory(payload)
      } catch (loadError) {
        if (isActive) setHistoryError(loadError.message || 'Could not reach the analysis service.')
      } finally {
        if (isActive) setIsHistoryLoading(false)
      }
    }
    void fetchInitialHistory()
    return () => { isActive = false }
  }, [authToken])

  useEffect(() => {
    if (!authToken) return undefined
    let isActive = true
    const fetchSettings = async () => {
      try {
        const response = await authenticatedFetch('/settings')
        const payload = await response.json().catch(() => ({}))
        if (!response.ok) throw new Error(payload.detail || 'Could not load settings status.')
        if (isActive) setSettings(payload)
      } catch (loadError) {
        if (isActive) setSettingsError(loadError.message || 'Could not reach the analysis service.')
      }
    }
    void fetchSettings()
    const fetchRoles = async () => {
      try {
        const response = await authenticatedFetch('/roles')
        const payload = await response.json().catch(() => [])
        if (response.ok && isActive) setAvailableRoles(payload)
      } catch {
        if (isActive) setAvailableRoles([])
      }
    }
    void fetchRoles()
    return () => { isActive = false }
  }, [authToken])

  const openHistoryItem = async (analysisId) => {
    try {
      const response = await authenticatedFetch(`/resume/${analysisId}`)
      const payload = await response.json().catch(() => ({}))
      if (!response.ok) throw new Error(payload.detail || 'Could not open this analysis.')
      setResult(payload)
      document.getElementById('results')?.scrollIntoView({ behavior: 'smooth' })
    } catch (openError) {
      setHistoryError(openError.message || 'Could not open this analysis.')
    }
  }

  const deleteHistoryItem = async (analysisId) => {
    try {
      const response = await authenticatedFetch(`/resume/${analysisId}`, { method: 'DELETE' })
      const payload = await response.json().catch(() => ({}))
      if (!response.ok) throw new Error(payload.detail || 'Could not delete this analysis.')
      setHistory((items) => items.filter((item) => item.analysis_id !== analysisId))
      setSelectedHistoryIds((ids) => ids.filter((id) => id !== analysisId))
    } catch (deleteError) {
      setHistoryError(deleteError.message || 'Could not delete this analysis.')
    }
  }

  const downloadReport = async (analysisId) => {
    try {
      const response = await authenticatedFetch(`/report/${analysisId}`)
      if (!response.ok) {
        const payload = await response.json().catch(() => ({}))
        throw new Error(payload.detail || 'Could not generate this report.')
      }
      const reportUrl = URL.createObjectURL(await response.blob())
      const downloadLink = document.createElement('a')
      downloadLink.href = reportUrl
      downloadLink.download = `resume-analysis-${analysisId}.pdf`
      downloadLink.click()
      URL.revokeObjectURL(reportUrl)
    } catch (reportError) {
      setHistoryError(reportError.message || 'Could not generate this report.')
    }
  }

  const clearHistory = async () => {
    if (!window.confirm('Delete all saved analysis records? Uploaded files saved separately will not be deleted.')) return
    setIsClearingHistory(true)
    setSettingsError('')
    try {
      const response = await authenticatedFetch('/resumes/history', { method: 'DELETE' })
      const payload = await response.json().catch(() => ({}))
      if (!response.ok) throw new Error(payload.detail || 'Could not clear analysis history.')
      setHistory([])
      setSelectedHistoryIds([])
      setComparison(null)
      setResult((current) => current && !current.analysis_id ? current : null)
    } catch (clearError) {
      setSettingsError(clearError.message || 'Could not clear analysis history.')
    } finally {
      setIsClearingHistory(false)
    }
  }

  const compareHistoryItems = async () => {
    if (selectedHistoryIds.length !== 2) return
    try {
      const response = await authenticatedFetch('/resume/compare', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ first_analysis_id: selectedHistoryIds[0], second_analysis_id: selectedHistoryIds[1] }),
      })
      const payload = await response.json().catch(() => ({}))
      if (!response.ok) throw new Error(payload.detail || 'Could not compare these analyses.')
      setComparison(payload)
    } catch (compareError) {
      setHistoryError(compareError.message || 'Could not compare these analyses.')
    }
  }

  const toggleHistorySelection = (analysisId) => {
    setComparison(null)
    setSelectedHistoryIds((ids) => ids.includes(analysisId)
      ? ids.filter((id) => id !== analysisId)
      : ids.length < 2 ? [...ids, analysisId] : [ids[1], analysisId])
  }

  const handleImprove = async (event) => {
    event.preventDefault()
    if (!improvementInput.trim()) {
      setImprovementError('Enter a summary or bullet point first.')
      return
    }
    setIsImproving(true)
    setImprovementError('')
    setImprovementResult(null)
    try {
      const response = await authenticatedFetch(`/resume/improve-${improvementKind}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: improvementInput }),
      })
      const payload = await response.json().catch(() => ({}))
      if (!response.ok) throw new Error(payload.detail || 'Could not improve this text.')
      setImprovementResult(payload)
    } catch (improveError) {
      setImprovementError(improveError.message || 'Could not reach the analysis service.')
    } finally {
      setIsImproving(false)
    }
  }

  const handleFileChange = (event) => {
    chooseFile(event.target.files?.[0])
    event.target.value = ''
  }

  const handleAnalyze = async () => {
    if (!resumeFile) {
      setError('Choose a PDF or DOCX resume first.')
      return
    }

    setError('')
    setIsAnalyzing(true)
    setStageIndex(0)
    const formData = new FormData()
    formData.append('file', resumeFile)
    formData.append('job_description', jobDescription)
    if (targetRole) formData.append('target_role', targetRole)

    try {
      const response = await authenticatedFetch('/resume/analyze', {
        method: 'POST',
        body: formData,
      })
      const payload = await response.json().catch(() => ({}))
      if (!response.ok) {
        throw new Error(payload.detail || 'Resume analysis failed.')
      }
      setResult(payload)
      void loadHistory()
    } catch (error) {
      setError(error.message || 'Could not reach the analysis service. Check that the backend is running and try again.')
    } finally {
      setIsAnalyzing(false)
    }
  }

  const handleAuthentication = async (event) => {
    event.preventDefault()
    setIsAuthenticating(true)
    setAuthError('')
    try {
      const response = await fetch(`${API_BASE_URL}/auth/${authMode === 'register' ? 'register' : 'login'}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: authEmail, password: authPassword }),
      })
      const payload = await response.json().catch(() => ({}))
      if (!response.ok) throw new Error(payload.detail || 'Could not sign in.')
      window.sessionStorage.setItem(SESSION_KEY, payload.access_token)
      setAuthToken(payload.access_token)
      setAuthPassword('')
    } catch (authenticationError) {
      setAuthError(authenticationError.message || 'Could not reach the account service.')
    } finally {
      setIsAuthenticating(false)
    }
  }

  const handleSignOut = () => {
    window.sessionStorage.removeItem(SESSION_KEY)
    setAuthToken('')
    setResult(null)
    setHistory([])
    setSettings(null)
  }

  const deleteAccount = async () => {
    if (!window.confirm('Delete your account and all saved analysis records? Files retained by the separate upload endpoint will not be deleted.')) return
    setSettingsError('')
    try {
      const response = await authenticatedFetch('/auth/me', { method: 'DELETE' })
      const payload = await response.json().catch(() => ({}))
      if (!response.ok) throw new Error(payload.detail || 'Could not delete this account.')
      window.sessionStorage.removeItem(SESSION_KEY)
      setAuthToken('')
      setAuthMode('login')
      setAuthPassword('')
      setAuthError('Account and saved analysis records deleted. Separately uploaded files are retained.')
      setResult(null)
      setHistory([])
      setSettings(null)
    } catch (deleteError) {
      setSettingsError(deleteError.message || 'Could not delete this account.')
    }
  }

  if (!authToken) {
    return (
      <main className="auth-shell">
        <section className="auth-panel" aria-labelledby="auth-title">
          <div className="brand-wrap auth-brand"><div className="brand-mark" aria-hidden="true">R</div><div><p className="eyebrow">Resume intelligence</p><h1>Resume Scanner</h1></div></div>
          <p className="eyebrow auth-kicker">Private workspace</p>
          <h2 id="auth-title">{authMode === 'register' ? 'Create your account' : 'Welcome back'}</h2>
          <p className="auth-copy">Your saved analyses are available only after signing in to your account.</p>
          <form className="auth-form" onSubmit={handleAuthentication}>
            <label className="field-label" htmlFor="account-email">Email address</label>
            <input id="account-email" type="email" autoComplete="email" required maxLength={320} value={authEmail} onChange={(event) => setAuthEmail(event.target.value)} />
            <label className="field-label" htmlFor="account-password">Password</label>
            <input id="account-password" type="password" autoComplete={authMode === 'register' ? 'new-password' : 'current-password'} required minLength={10} maxLength={128} value={authPassword} onChange={(event) => setAuthPassword(event.target.value)} />
            {authMode === 'register' ? <small>Use at least 10 characters.</small> : null}
            {authError ? <p className="error-message" role="alert">{authError}</p> : null}
            <button className="primary auth-submit" type="submit" disabled={isAuthenticating}>{isAuthenticating ? 'Please wait…' : authMode === 'register' ? 'Create account' : 'Sign in'}<span aria-hidden="true">→</span></button>
          </form>
          <p className="auth-switch">{authMode === 'register' ? 'Already have an account?' : 'New to Resume Scanner?'} <button type="button" onClick={() => { setAuthMode(authMode === 'register' ? 'login' : 'register'); setAuthError('') }}>{authMode === 'register' ? 'Sign in' : 'Create an account'}</button></p>
          <p className="auth-privacy">Passwords are stored as salted scrypt hashes. Sessions expire after 12 hours and are kept in this browser tab session.</p>
        </section>
      </main>
    )
  }

  return (
    <div className="page-shell">
      <header className="topbar">
        <div className="brand-wrap">
          <div className="brand-mark" aria-hidden="true">R</div>
          <div>
            <p className="eyebrow">Resume intelligence</p>
            <h1>Resume Scanner</h1>
          </div>
        </div>
        <nav className="topnav">
          <a href="#scanner" aria-current="page">Analyze</a>
          <a href="#results">Results</a>
          <a href="#history" onClick={loadHistory}>History</a>
          <a href="#improvements">Improve</a>
          <a href="#settings">Settings</a>
          <button className="sign-out-button" type="button" onClick={handleSignOut}>Sign out</button>
        </nav>
      </header>

      <main>
        <section className="intro" aria-labelledby="page-title">
          <div>
            <p className="eyebrow">A clearer view of your next move</p>
            <h2 id="page-title">Understand your resume.<br />Find your job match.</h2>
          </div>
          <p className="intro-copy">Review detected skills, resume structure, and job-specific gaps in one focused analysis.</p>
        </section>

        <section className="content-grid" id="scanner" aria-label="Resume analysis inputs">
          <section className="panel upload-panel">
          <div className="panel-header">
            <div>
              <p className="eyebrow">01 / Resume</p>
              <h2>Start with your resume</h2>
            </div>
          </div>

          <label
            className={`dropzone${resumeFile ? ' has-file' : ''}`}
            htmlFor="resume-file"
            onDragOver={(event) => event.preventDefault()}
            onDrop={(event) => {
              event.preventDefault()
              chooseFile(event.dataTransfer.files?.[0])
            }}
          >
            <input id="resume-file" type="file" accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document" onChange={handleFileChange} />
            <div className="dropzone-text">
              <span className="upload-symbol" aria-hidden="true">↑</span>
              <strong>{resumeFile ? 'Replace selected resume' : 'Drop your resume here or browse'}</strong>
              <span>PDF or DOCX · Up to 10 MB</span>
            </div>
          </label>

          {resumeFile ? (
            <div className="file-meta" aria-label="Selected file details">
              <div>
                <label>Filename</label>
                <p>{resumeFile.name}</p>
              </div>
              <div>
                <label>File type</label>
                <p>{resumeFile.name.split('.').pop()?.toUpperCase() || 'Unknown'}</p>
              </div>
              <div>
                <label>File size</label>
                <p>{(resumeFile.size / 1024 / 1024).toFixed(2)} MB</p>
              </div>
              <button className="text-button" type="button" onClick={() => { setResumeFile(null); setResult(null); setError('') }}>Remove file</button>
            </div>
          ) : null}

          <label className="field-label" htmlFor="job-description">Job description <span>Optional</span></label>
          <textarea
            id="job-description"
            value={jobDescription}
            onChange={(event) => setJobDescription(event.target.value)}
            placeholder="Paste a job description to see detected skill overlap and gaps."
          />

          <label className="field-label role-field-label" htmlFor="target-role">Target IT role <span>Optional</span></label>
          <select id="target-role" value={targetRole} onChange={(event) => setTargetRole(event.target.value)}>
            <option value="">Use job description only</option>
            {availableRoles.map((role) => <option value={role.role} key={role.role}>{role.role}</option>)}
          </select>
          {targetRole ? <p className="role-selection-note">The role profile groups equivalent skills. You only need evidence for one option in each group; suggested stacks are not all required.</p> : null}

          <div className="actions">
            <button className="primary" type="button" onClick={handleAnalyze} disabled={isAnalyzing || !resumeFile}>
              {isAnalyzing ? 'Analyzing…' : 'Analyze resume'}
              <span aria-hidden="true">→</span>
            </button>
          </div>

          {error ? <p className="error-message" role="alert">{error}</p> : null}
          <p className="privacy-note">Analysis is processed by the configured backend. The analysis endpoint removes its temporary file after parsing; do not upload information you do not want processed.</p>
          </section>

          <aside className="panel job-panel">
          <div className="panel-header">
            <div>
              <p className="eyebrow">What gets reviewed</p>
              <h2>From document to direction</h2>
            </div>
          </div>

          <ul className="process-list">
            <li><span>01</span><div><strong>Document structure</strong><small>Contact details and standard sections</small></div></li>
            <li><span>02</span><div><strong>Skills and keywords</strong><small>Evidence found in resume text</small></div></li>
            <li><span>03</span><div><strong>Job comparison</strong><small>Detected skill overlap and gaps</small></div></li>
            <li><span>04</span><div><strong>Next steps</strong><small>Specific recommendations from findings</small></div></li>
          </ul>
          <div className="method-note"><strong>Estimated, not predictive</strong><p>ATS checks use extracted text and cannot assess every parser, visual layout, or proprietary hiring system.</p></div>
          </aside>
        </section>

      <section className="dashboard" id="results" aria-live="polite">
        {isAnalyzing ? (
          <div className="loading-state" role="status">
            <span className="loader" aria-hidden="true" />
            <div><p className="eyebrow">Analysis in progress</p><h2>{ANALYSIS_STAGES[stageIndex]}…</h2><p>Your results will appear here when processing is complete.</p></div>
          </div>
        ) : null}
        {!result && !isAnalyzing ? <div className="empty-state"><span>02 / Results</span><p>Your resume analysis will appear here.</p></div> : null}
        {result ? <>
        <div className="results-heading">
          <div><p className="eyebrow">02 / Analysis</p><h2>Resume overview</h2></div>
          <div className="results-actions">
            <p>{result.resume.name || 'Candidate'}{result.resume.email ? ` · ${result.resume.email}` : ''}</p>
            {result.analysis_id ? <button className="secondary-button" type="button" onClick={() => downloadReport(result.analysis_id)}>Download report</button> : null}
          </div>
        </div>
        <div className="score-overview">
          {scoreCards.map((card) => (
            <div className="score-card" key={card.label}>
              <span className="score-label">{card.label}</span>
              <strong>{card.value}<small>/100</small></strong>
              <p>{card.note}</p>
            </div>
          ))}
        </div>

        <div className="analysis-grid">
          <div className="panel analysis-panel">
            <p className="eyebrow">Job comparison</p><h2>Matched skills</h2>
            {result.matched_skills.length ? <div className="tag-list">{result.matched_skills.map((skill) => <span key={skill} className="tag success">{skill}</span>)}</div> : <p className="muted">{result.job.skills?.length ? 'No shared skills detected from this job description.' : result.role_analysis ? 'No target-role skills were detected in the resume.' : result.job.description?.trim() ? 'No job skills from the current taxonomy were detected.' : 'Add a job description or select a target role.'}</p>}
            {result.matched_skill_details?.length ? <div className="skill-evidence-list">{result.matched_skill_details.map((item) => <div key={item.skill}><strong>{item.skill} · {item.source_section.replaceAll('_', ' ')}</strong><p>{item.evidence}</p></div>)}</div> : null}
            {result.job.skills?.length ? <p className="muted skill-method-note">Required skills weigh more than preferred or unqualified mentions.</p> : null}
          </div>

          <div className="panel analysis-panel">
            <p className="eyebrow">Skill gaps</p><h2>Not detected in resume</h2>
            {result.missing_skill_details?.length ? <div className="tag-list">{result.missing_skill_details.map((item) => <span key={item.skill} className="tag warning">{item.skill}<small>{item.importance}</small></span>)}</div> : result.missing_skills.length ? <div className="tag-list">{result.missing_skills.map((skill) => <span key={skill} className="tag warning">{skill}</span>)}</div> : result.role_analysis?.unmet_groups.length ? <div className="role-gap-list">{result.role_analysis.unmet_groups.map((group) => <div key={group.group}><strong>{group.group}</strong><p>Choose one supported option: {group.skills.join(', ')}</p></div>)}</div> : <p className="muted">{result.job.description?.trim() ? result.job.skills?.length ? 'No missing job skills were detected.' : 'No known IT taxonomy terms were detected in this job description.' : result.role_analysis ? 'All role skill groups have at least one detected match.' : 'Add a job description or select a target role.'}</p>}
            {result.missing_skill_details?.length ? <p className="muted skill-method-note">“Not detected” means no matching evidence was found; it does not prove you lack the skill.</p> : null}
            {result.role_analysis?.unmet_groups.length ? <p className="muted skill-method-note">These are alternatives within each group, not a request to claim or learn every listed skill.</p> : null}
          </div>

          {result.role_analysis ? <div className="panel analysis-panel role-fit-panel">
            <p className="eyebrow">Selected role · {result.role_analysis.role}</p><h2>Role requirements and project evidence</h2>
            <div className="role-fit-summary"><strong>{result.role_analysis.required_groups_met ?? result.role_analysis.skill_groups.filter((group) => group.status === 'met').length}/{result.role_analysis.total_required_groups ?? result.role_analysis.skill_groups.length}</strong><span>skill groups have evidence</span><small>{(result.role_analysis.project_count ?? result.resume.projects?.length ?? 0) ? `${result.role_analysis.related_project_count ?? result.role_analysis.related_projects?.length ?? 0} of ${result.role_analysis.project_count ?? result.resume.projects.length} project lines relate to this role.` : 'No project section detected.'}</small></div>
            <div className="role-groups">{result.role_analysis.skill_groups.map((group) => <article className="role-group" key={group.group}>
              <div><strong>{group.group}</strong><span className={group.status === 'met' ? 'group-met' : 'group-gap'}>{group.status === 'met' ? 'Evidence found' : 'Not detected'}</span></div>
              <p>Any one: {group.skills.join(', ')}</p>
              {group.matched_skills.length ? <small>Matched: {group.matched_skills.join(', ')} · {group.evidence.join(' / ')}</small> : null}
            </article>)}</div>
            {result.role_analysis.related_projects.length ? <div className="role-project-evidence"><strong>Relevant project evidence</strong>{result.role_analysis.related_projects.map((project) => <p key={project.evidence}>{project.evidence}<small>Matched: {project.matched_skills.join(', ')}</small></p>)}</div> : <p className="muted skill-method-note">No project line matching this role profile was detected. Add a real relevant project if you have one.</p>}
            {result.role_analysis.optional_alternatives.length ? <div className="role-optional"><strong>Optional skill alternatives</strong>{result.role_analysis.optional_alternatives.map((alternative) => <p key={alternative.label}>{alternative.label}: {alternative.skills.join(', ')}</p>)}</div> : null}
          </div> : null}

          <div className="panel analysis-panel">
            <p className="eyebrow">Resume skills</p><h2>Detected skills</h2>
            {result.resume.skill_details?.length ? <div className="skill-inventory">{result.resume.skill_details.map((item) => <article className="skill-inventory-item" key={item.skill}>
              <div><strong>{item.skill}</strong></div>
              <small>{item.category} · {item.source_section.replaceAll('_', ' ')}</small>
              <p>{item.evidence}</p>
            </article>)}</div> : <p className="muted">No skills from the current taxonomy were detected.</p>}
          </div>

          <div className="panel analysis-panel">
            <p className="eyebrow">Extracted details</p><h2>Resume information</h2>
            <dl className="meta-list">
              <div><dt>Name</dt><dd>{result.resume.name || 'Not detected'}</dd></div>
              <div><dt>Email</dt><dd>{result.resume.email || 'Not detected'}</dd></div>
              <div><dt>Phone</dt><dd>{result.resume.phone || 'Not detected'}</dd></div>
              <div><dt>Sections</dt><dd>{result.resume.sections_detected.length ? result.resume.sections_detected.join(', ') : 'Not detected'}</dd></div>
            </dl>
          </div>

          <div className="panel analysis-panel">
            <p className="eyebrow">Action plan</p><h2>Recommendations</h2>
            {result.recommendation_details?.length ? <div className="recommendation-cards">{result.recommendation_details.map((item) => <article className="recommendation-item" key={`${item.type}-${item.title}`}>
              <div className="recommendation-title"><strong>{item.title}</strong><span className={`priority-${item.priority}`}>{item.priority} priority</span></div>
              <p className="recommendation-action">{item.action}</p>
              <p className="recommendation-evidence"><strong>Evidence:</strong> {item.evidence}</p>
            </article>)}</div> : result.recommendations.length ? <ul className="recommendation-list">{result.recommendations.map((item) => <li key={item}>{item}</li>)}</ul> : <p className="muted">No recommendations for this analysis.</p>}
          </div>

          <div className="panel analysis-panel">
            <p className="eyebrow">Based on detected skills · suggestions, not scores</p><h2>Role suggestions</h2>
            {result.role_recommendations?.length ? <div className="role-list">{result.role_recommendations.map((role) => <article className="role-item" key={role.role}>
              <div><strong>{role.role}</strong></div>
              <p>Role-related skills detected in your resume: {role.matched_skills.join(', ')}.</p>
              {role.missing_skills.length ? <small>Other possible skills not detected (not all required): {role.missing_skills.join(', ')}</small> : null}
            </article>)}</div> : <p className="muted">Not enough detected skills to suggest roles. Add evidence for your actual skills in the resume.</p>}
          </div>

          <div className="panel analysis-panel">
            <p className="eyebrow">{result.ats_analysis?.label || 'Estimated ATS'}</p><h2>Why this score?</h2>
            {result.ats_analysis?.score_basis === 'job_targeted' ? <div className="ats-formula-breakdown">
              <p><span>Semantic similarity · 60%</span><strong>{result.ats_analysis.semantic_component}%</strong></p>
              <p><span>Weighted exact skill coverage · 40%</span><strong>{result.ats_analysis.exact_skill_component}%</strong></p>
              <p><span>Document readiness (separate checks)</span><strong>{result.ats_analysis.document_readiness_score}%</strong></p>
              <small>{result.ats_analysis.formula}</small>
            </div> : <p className="muted">{result.ats_analysis?.formula}</p>}
            <ul className="check-list">{result.ats_analysis?.checks.map((check) => <li key={check.name} className={`check-${check.status}`}><span aria-hidden="true">{check.status === 'pass' ? '✓' : check.status === 'warning' ? '!' : '–'}</span><div><strong>{check.name}</strong><p>{check.detail}</p></div></li>)}</ul>
            <p className="muted formatting-note">{result.ats_analysis?.formatting_assessment}</p>
            <p className="disclaimer">{result.ats_analysis?.disclaimer}</p>
          </div>

          <div className="panel analysis-panel">
            <p className="eyebrow">Resume text</p><h2>Detected summary</h2>
            <p className="summary-text">{result.summary}</p>
            {result.issues.length ? <ul className="recommendation-list issue-list">{result.issues.map((item) => <li key={item}>{item}</li>)}</ul> : null}
          </div>
        </div>
        </> : null}
      </section>
      <section className="history-section" id="history" aria-labelledby="history-title">
        <div className="history-heading">
          <div><p className="eyebrow">Saved analyses</p><h2 id="history-title">Resume history</h2></div>
          <button className="secondary-button" type="button" onClick={loadHistory} disabled={isHistoryLoading}>{isHistoryLoading ? 'Refreshing…' : 'Refresh history'}</button>
        </div>
        {historyError ? <p className="error-message" role="alert">{historyError}</p> : null}
        {history.length ? <>
          <div className="history-table" role="table" aria-label="Saved resume analyses">
            <div className="history-row history-header" role="row"><span>Select</span><span>Resume</span><span>Date</span><span>Match</span><span>ATS</span><span>Actions</span></div>
            {history.map((item) => <div className="history-row" role="row" key={item.analysis_id}>
              <span><input type="checkbox" aria-label={`Select ${item.filename} for comparison`} checked={selectedHistoryIds.includes(item.analysis_id)} onChange={() => toggleHistorySelection(item.analysis_id)} /></span>
              <span className="history-name"><strong>{item.filename}</strong><small>{item.resume_name}</small></span>
              <span>{item.created_at ? new Date(item.created_at).toLocaleDateString() : 'Unknown'}</span>
              <span>{Math.round(item.scores.compatibility)}/100</span>
              <span>{Math.round(item.scores.ats_compatibility)}/100</span>
              <span className="history-actions"><button type="button" onClick={() => openHistoryItem(item.analysis_id)}>Open</button><button type="button" onClick={() => downloadReport(item.analysis_id)}>PDF</button><button type="button" onClick={() => deleteHistoryItem(item.analysis_id)}>Delete</button></span>
            </div>)}
          </div>
          <div className="compare-controls"><span>{selectedHistoryIds.length} of 2 selected</span><button className="primary" type="button" onClick={compareHistoryItems} disabled={selectedHistoryIds.length !== 2}>Compare versions <span aria-hidden="true">→</span></button></div>
          {comparison ? <div className="comparison-result" aria-live="polite">
            <h3>Version comparison</h3>
            <div className="comparison-scores">{Object.entries(comparison.score_changes).map(([label, change]) => <p key={label}><span>{label.replaceAll('_', ' ')}</span><strong>{change > 0 ? '+' : ''}{change}</strong></p>)}</div>
            <p><strong>New skills:</strong> {comparison.new_skills.join(', ') || 'None'}</p>
            <p><strong>Removed skills:</strong> {comparison.removed_skills.join(', ') || 'None'}</p>
            <p><strong>New sections:</strong> {comparison.new_sections.join(', ') || 'None'}</p>
            <p><strong>Removed sections:</strong> {comparison.removed_sections.join(', ') || 'None'}</p>
          </div> : null}
        </> : <p className="history-empty">{isHistoryLoading ? 'Loading saved analyses…' : 'No saved analyses yet. New analyses are added here automatically.'}</p>}
      </section>
      <section className="improvements-section" id="improvements" aria-labelledby="improvements-title">
        <div className="history-heading">
          <div><p className="eyebrow">Writing support</p><h2 id="improvements-title">Improve resume wording</h2></div>
        </div>
        <form className="improvement-form" onSubmit={handleImprove}>
          <div className="mode-switch" role="group" aria-label="Text to improve">
            <button type="button" className={improvementKind === 'summary' ? 'active' : ''} aria-pressed={improvementKind === 'summary'} onClick={() => { setImprovementKind('summary'); setImprovementResult(null) }}>Summary</button>
            <button type="button" className={improvementKind === 'bullet' ? 'active' : ''} aria-pressed={improvementKind === 'bullet'} onClick={() => { setImprovementKind('bullet'); setImprovementResult(null) }}>Bullet point</button>
          </div>
          <label className="field-label" htmlFor="improvement-input">{improvementKind === 'summary' ? 'Current summary' : 'Current bullet point'}</label>
          <textarea id="improvement-input" maxLength={10000} value={improvementInput} onChange={(event) => setImprovementInput(event.target.value)} placeholder={improvementKind === 'summary' ? 'Paste your existing resume summary…' : 'Paste one existing resume bullet…'} />
          <div className="actions"><button className="primary" type="submit" disabled={isImproving}>{isImproving ? 'Working…' : 'Improve wording'}<span aria-hidden="true">→</span></button></div>
          {improvementError ? <p className="error-message" role="alert">{improvementError}</p> : null}
        </form>
        {improvementResult ? <div className="improvement-output" aria-live="polite">
          <div className="output-heading"><h3>Suggested wording</h3><span className={improvementResult.mode === 'ai' ? 'mode-ai' : 'mode-fallback'}>{improvementResult.mode === 'ai' ? `AI · ${improvementResult.provider}` : 'Rule-based fallback'}</span></div>
          <p>{improvementResult.improved_text || 'Not detected'}</p>
          <small>{improvementResult.notice}</small>
        </div> : null}
      </section>
      <section className="settings-section" id="settings" aria-labelledby="settings-title">
        <div className="history-heading">
          <div><p className="eyebrow">Configuration and privacy</p><h2 id="settings-title">Settings</h2></div>
        </div>
        {settingsError ? <p className="error-message" role="alert">{settingsError}</p> : null}
        <div className="settings-grid">
          <section className="settings-block" aria-labelledby="provider-title">
            <p className="eyebrow">Provider status</p><h3 id="provider-title">AI wording enhancement</h3>
            <dl className="meta-list">
              <div><dt>Provider</dt><dd>{settings?.ai?.provider || 'Not configured'}</dd></div>
              <div><dt>Connection</dt><dd>{settings?.ai?.configured ? 'Configured' : 'Rule-based fallback active'}</dd></div>
              <div><dt>Model</dt><dd>{settings?.ai?.model || 'Not configured'}</dd></div>
              <div><dt>Semantic model</dt><dd>{settings?.semantic_model || 'Not available'}</dd></div>
              <div><dt>Scanned PDF OCR</dt><dd>{settings?.ocr?.configured ? `Available · ${settings.ocr.language}` : 'Tesseract executable not found'}</dd></div>
            </dl>
            <p className="muted">Provider keys remain in the backend environment and are never returned here.</p>
            {!settings?.ocr?.configured ? <p className="muted">Install Tesseract OCR and set TESSERACT_CMD if it is not on PATH. {settings?.ocr?.note}</p> : null}
          </section>
          <section className="settings-block" aria-labelledby="privacy-title">
            <p className="eyebrow">Data handling</p><h3 id="privacy-title">Privacy and retention</h3>
            <p>{settings?.history_storage || 'Analysis results are stored in the configured database until deleted.'}</p>
            <p>{settings?.uploaded_files || 'Separately uploaded files may remain in the configured upload directory.'}</p>
            <p>Resume analysis sends the selected file to this backend. When an AI provider is configured, only wording-improvement text is sent to that provider.</p>
            <button className="danger-button" type="button" onClick={clearHistory} disabled={isClearingHistory}>{isClearingHistory ? 'Clearing…' : 'Clear saved analysis history'}</button>
            <button className="danger-button account-delete-button" type="button" onClick={deleteAccount}>Delete account and its analyses</button>
          </section>
        </div>
      </section>
      </main>
      <footer className="site-footer"><span>Resume Scanner</span><p>Analysis is heuristic and should support, not replace, your review.</p></footer>
    </div>
  )
}

export default App
