import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { getEntities, saveEntity } from '../api'
import type { Entity } from '../types'
import './forms.css'
import './entities.css'

export default function Entities() {
  const [entities, setEntities] = useState<Entity[] | null>(null)
  const [name, setName] = useState('')
  const [status, setStatus] = useState<Entity['status']>('active')
  const [error, setError] = useState<string | null>(null)

  const load = () => getEntities().then(setEntities).catch((e: Error) => setError(e.message))

  useEffect(() => {
    load()
  }, [])

  async function submit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    try {
      await saveEntity(name.trim(), status)
      setName('')
      await load()
    } catch (err) {
      setError((err as Error).message)
    }
  }

  return (
    <>
      <h1>Registry</h1>
      <p className="page-intro">
        The systems, tools, and vendors that exist today. Mark one retired and every statement that
        references it gets flagged as stale.
      </p>

      <form className="form form-row" onSubmit={submit}>
        <label>
          Name
          <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Jenkins" required />
        </label>
        <label>
          Status
          <select value={status} onChange={(e) => setStatus(e.target.value as Entity['status'])}>
            <option value="active">active</option>
            <option value="retired">retired</option>
          </select>
        </label>
        <button type="submit">Save</button>
      </form>

      {error && <p className="notice">{error}</p>}
      {entities && entities.length === 0 && (
        <p className="notice">No entities yet. Add the systems your team runs so retired ones can be caught.</p>
      )}

      <ul className="registry">
        {entities?.map((en) => (
          <li key={en.id} className={en.status}>
            <span className="entity-name">{en.name}</span>
            <span className="row-actions">
              <span className="meta">{en.status}</span>
              <button
                type="button"
                className="small"
                onClick={() =>
                  saveEntity(en.name, en.status === 'active' ? 'retired' : 'active')
                    .then(load)
                    .catch((e: Error) => setError(e.message))
                }
              >
                {en.status === 'active' ? 'Retire' : 'Reactivate'}
              </button>
            </span>
          </li>
        ))}
      </ul>
    </>
  )
}
