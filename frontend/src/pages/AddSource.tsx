import { useState } from 'react'
import type { FormEvent } from 'react'
import { addSource, getEntities } from '../api'
import type { NewStatement } from '../types'
import './forms.css'

export default function AddSource() {
  const [label, setLabel] = useState('')
  const [text, setText] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<NewStatement[] | null>(null)
  const [unknown, setUnknown] = useState<string[]>([])

  async function submit(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    setResult(null)
    setUnknown([])
    try {
      const added = await addSource(label.trim(), text)
      setResult(added)
      const known = new Set((await getEntities()).map((en) => en.name))
      const mentioned = new Set(added.flatMap((st) => st.referenced_entities))
      setUnknown([...mentioned].filter((name) => !known.has(name)))
      setText('')
      setLabel('')
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <h1>Add a source</h1>
      <p className="page-intro">
        Paste a meeting note, a Slack thread, or a piece of a design doc. Waymark pulls out the decisions
        and checks them against what is already on record.
      </p>

      <form className="form" onSubmit={submit}>
        <label>
          Where it came from
          <input
            value={label}
            onChange={(e) => setLabel(e.target.value)}
            placeholder="Infra sync, 12 March"
            required
          />
        </label>
        <label>
          Text
          <textarea value={text} onChange={(e) => setText(e.target.value)} rows={14} required />
        </label>
        <button type="submit" disabled={busy}>
          {busy ? 'Reading the text' : 'Extract decisions'}
        </button>
      </form>

      {error && (
        <p className="notice" role="alert">
          {error}
        </p>
      )}

      {result && (
        <section className="result" aria-live="polite">
          <h2>{result.length === 0 ? 'No decisions found' : `Recorded ${result.length}`}</h2>
          <ul>
            {result.map((s) => (
              <li key={s.id}>
                <p className="claim">{s.claim}</p>
                <p className="meta">
                  {s.contradictions.length} conflicts, {s.staleness_flags.length} stale references
                </p>
              </li>
            ))}
          </ul>
          {unknown.length > 0 && (
            <p className="notice">
              Not in the registry yet: {unknown.join(', ')}. <a href="#/entities">Add them</a> so a retired one
              gets caught later.
            </p>
          )}
          <p>
            <a href="#/feed">Open the record</a>
          </p>
        </section>
      )}
    </>
  )
}
