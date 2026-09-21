import type { Answer, Entity, NewStatement, Statement } from './types'

const BASE = import.meta.env.VITE_API_BASE ?? 'http://127.0.0.1:8000'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(BASE + path, init)
  if (!res.ok) {
    let detail = res.statusText
    try {
      detail = (await res.json()).detail ?? detail
    } catch {
      /* body was not json, keep status text */
    }
    throw new Error(detail)
  }
  return res.json()
}

const json = (body: unknown): RequestInit => ({
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(body),
})

export const getStatements = () =>
  request<{ statements: Statement[] }>('/statements').then((r) => r.statements)

export const addSource = (label: string, raw_text: string) =>
  request<{ statements: NewStatement[] }>('/sources', json({ label, raw_text })).then((r) => r.statements)

export const getEntities = () => request<{ entities: Entity[] }>('/entities').then((r) => r.entities)

export const saveEntity = (name: string, status: Entity['status']) =>
  request<Entity>('/entities', json({ name, status }))

export const ask = (q: string) => request<Answer>('/ask?q=' + encodeURIComponent(q))
