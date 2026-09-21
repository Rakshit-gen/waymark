import { useEffect, useState } from 'react'
import Feed from './pages/Feed'
import './shell.css'

const PAGES = [
  { id: 'feed', label: 'Record' },
  { id: 'add', label: 'Add source' },
  { id: 'ask', label: 'Ask' },
  { id: 'entities', label: 'Registry' },
] as const

type PageId = (typeof PAGES)[number]['id']

function currentPage(): PageId {
  const hash = window.location.hash.replace('#/', '')
  return PAGES.some((p) => p.id === hash) ? (hash as PageId) : 'feed'
}

export default function App() {
  const [page, setPage] = useState<PageId>(currentPage())

  useEffect(() => {
    const onHash = () => setPage(currentPage())
    window.addEventListener('hashchange', onHash)
    return () => window.removeEventListener('hashchange', onHash)
  }, [])

  return (
    <div className="shell">
      <header className="signpost">
        <a className="wordmark" href="#/feed">
          Waymark
        </a>
        <nav aria-label="Pages">
          {PAGES.map((p) => (
            <a key={p.id} href={`#/${p.id}`} aria-current={p.id === page ? 'page' : undefined}>
              {p.label}
            </a>
          ))}
        </nav>
      </header>
      <main className="page">
        {page === 'feed' && <Feed />}
      </main>
    </div>
  )
}
