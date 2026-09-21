export interface Contradiction {
  id: number
  statement_a_id: number
  statement_b_id: number
  explanation: string
  created_at: string
}

export interface StalenessFlag {
  id: number
  statement_id: number
  entity: string
  reason: string
  created_at: string
}

export interface Statement {
  id: number
  source_id: number
  claim: string
  rationale: string
  referenced_entities: string[]
  confidence: number
  created_at: string
  contradictions: Contradiction[]
  staleness_flags: StalenessFlag[]
}

export interface Entity {
  id: number
  name: string
  status: 'active' | 'retired'
}

export interface Answer {
  answer: string
  cited_ids: number[]
  contested: boolean
}

/** Shape returned by POST /sources, before the statement is read back from the feed. */
export interface NewStatement {
  id: number
  claim: string
  rationale: string
  referenced_entities: string[]
  confidence: number
  contradictions: { prior_id: number; explanation: string }[]
  staleness_flags: { entity: string; reason: string }[]
}
