import { useEffect, useState } from 'react'
import { getStatements } from '../api'
import type { Statement } from '../types'
import './feed.css'

export function formatWhen(iso: string) {
  const d = new Date(iso)
  return d.toISOString().slice(0, 16).replace('T', ' ') + 'Z'
}

export default function Feed() {
  const [statements, setStatements] = useState<Statement[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getStatements().then(setStatements).catch((e: Error) => setError(e.message))
  }, [])

  return (
    <>
      <h1>The record</h1>
      <p className="page-intro">Every decision pulled out of the sources you have added, newest first.</p>

      {error && <p className="notice">Could not load statements: {error}</p>}
      {!error && statements === null && <p className="meta">Loading</p>}
      {statements && statements.length === 0 && (
        <p className="notice">Nothing recorded yet. Add a source and its decisions will show up here.</p>
      )}

      <ol className="trail">
        {statements?.map((s) => (
          <li key={s.id} id={`s${s.id}`} className="entry">
            <p className="claim">{s.claim}</p>
            {s.rationale && <p className="rationale">{s.rationale}</p>}
            <p className="meta">
              #{s.id} from source {s.source_id}, {formatWhen(s.created_at)}, confidence{' '}
              {s.confidence.toFixed(2)}
            </p>
            {s.referenced_entities.length > 0 && (
              <ul className="entities">
                {s.referenced_entities.map((e) => (
                  <li key={e}>{e}</li>
                ))}
              </ul>
            )}
          </li>
        ))}
      </ol>
    </>
  )
}
