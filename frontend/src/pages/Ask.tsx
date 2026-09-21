import { useState } from 'react'
import type { FormEvent } from 'react'
import { ask } from '../api'
import type { Answer } from '../types'
import './forms.css'
import './ask.css'

export default function Ask() {
  const [question, setQuestion] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [answer, setAnswer] = useState<Answer | null>(null)

  async function submit(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    setAnswer(null)
    try {
      setAnswer(await ask(question.trim()))
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
        </section>
      )}
    </>
  )
}
