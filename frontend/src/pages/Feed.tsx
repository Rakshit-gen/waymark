import { useEffect, useState } from 'react'
import { getStatements } from '../api'
import type { Statement } from '../types'
import './feed.css'

export function formatWhen(iso: string) {
  const d = new Date(iso)
  return d.toISOString().slice(0, 16).replace('T', ' ') + 'Z'
}

function markFor(s: Statement) {
  if (s.contradictions.length > 0) return 'is-contradicted'
  if (s.staleness_flags.length > 0) return 'is-stale'
  return ''
}

type Filter = 'all' | 'contradicted' | 'stale'

export default function Feed() {
  const [filter, setFilter] = useState<Filter>('all')
  const [statements, setStatements] = useState<Statement[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getStatements().then(setStatements).catch((e: Error) => setError(e.message))
  }, [])

  const shown = statements?.filter((s) =>
    filter === 'contradicted' ? s.contradictions.length > 0 : filter === 'stale' ? s.staleness_flags.length > 0 : true,
  )

  return (
    <>
      <h1>The record</h1>
      <p className="page-intro">Every decision pulled out of the sources you have added, newest first.</p>

      <div className="filters" role="group" aria-label="Filter statements">
        {(['all', 'contradicted', 'stale'] as const).map((f) => (
          <button
            key={f}
            type="button"
            className="filter"
            aria-pressed={filter === f}
            onClick={() => setFilter(f)}
          >
            {f}
          </button>
        ))}
      </div>

      {error && <p className="notice">Could not load statements: {error}</p>}
      {!error && statements === null && <p className="meta">Loading</p>}
      {statements && statements.length === 0 && (
        <p className="notice">Nothing recorded yet. Add a source and its decisions will show up here.</p>
      )}

      {shown && statements && shown.length === 0 && statements.length > 0 && (
        <p className="notice">No {filter} statements.</p>
      )}

      <ol className="trail">
        {shown?.map((s) => (
          <li key={s.id} id={`s${s.id}`} className={`entry ${markFor(s)}`}>
            {(s.contradictions.length > 0 || s.staleness_flags.length > 0) && (
              <p className="flags">
                {s.contradictions.length > 0 && <span className="flag flag-contradiction">Contradicted</span>}
                {s.staleness_flags.length > 0 && <span className="flag flag-stale">Stale</span>}
              </p>
            )}
            <p className="claim">{s.claim}</p>
            {s.rationale && <p className="rationale">{s.rationale}</p>}
            <p className="meta">
              #{s.id} from {s.source_label}, {formatWhen(s.created_at)}, confidence {s.confidence.toFixed(2)}
            </p>
            {s.contradictions.map((c) => {
              const other = c.statement_a_id === s.id ? c.statement_b_id : c.statement_a_id
              return (
                <p key={c.id} className="note note-contradiction">
                  Conflicts with <a href={`#s${other}`}>#{other}</a>. {c.explanation}
                </p>
              )
            })}
            {s.staleness_flags.map((f) => (
              <p key={f.id} className="note note-stale">
                {f.reason}.
              </p>
            ))}
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
