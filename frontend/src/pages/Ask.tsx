import { useState } from 'react'
import type { FormEvent } from 'react'
import { ask, getStatements } from '../api'
import { formatWhen } from './Feed'
import type { Answer, Statement } from '../types'
import './forms.css'
import './ask.css'

export default function Ask() {
  const [question, setQuestion] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [answer, setAnswer] = useState<Answer | null>(null)
  const [cited, setCited] = useState<Statement[]>([])

  async function submit(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    setAnswer(null)
    setCited([])
    try {
      const result = await ask(question.trim())
      setAnswer(result)
      const all = await getStatements()
      setCited(all.filter((st) => result.cited_ids.includes(st.id)))
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <h1>Ask why</h1>
      <p className="page-intro">
        Ask about a system or a choice, like why we use Postgres for jobs. The answer only uses what is on
        record and says which statements it came from.
      </p>

      <form className="form" onSubmit={submit}>
        <label>
          Question
          <input
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Why did we stop using Jenkins?"
            required
          />
        </label>
        <button type="submit" disabled={busy}>
          {busy ? 'Looking' : 'Ask'}
        </button>
      </form>

      {error && <p className="notice">{error}</p>}

      {answer && (
        <section className="answer">
          {answer.contested && (
            <p className="contested">This record is contested. Statements it relies on disagree with each other.</p>
          )}
          <p className="answer-text">{answer.answer}</p>
          {cited.length > 0 && (
            <>
              <h2>Sources</h2>
              <ol className="citations">
                {cited.map((st) => (
                  <li key={st.id}>
                    <span className="meta">
                      #{st.id}, {formatWhen(st.created_at)}
                    </span>
                    <p className="claim">{st.claim}</p>
                    {st.rationale && <p>{st.rationale}</p>}
                  </li>
                ))}
              </ol>
            </>
          )}
        </section>
      )}
    </>
  )
}
