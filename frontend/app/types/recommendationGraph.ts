export type GraphCuisineGroup =
  | 'korean'
  | 'chinese'
  | 'western'
  | 'japanese'
  | 'southeast_asian'
  | 'other'

export type GraphRelation = 'content' | 'collaborative' | 'hybrid'

export interface RecommendationGraphNode {
  id: number
  name: string
  family: string
  cuisine: string
  cuisine_group: GraphCuisineGroup
  attributes: Record<string, number>
  selector_count: number
}

export interface RecommendationGraphEdge {
  source: number
  target: number
  relation: GraphRelation
  similarity: number
  content_similarity: number
  collaborative_similarity: number
  selector_count: number
}

export interface RecommendationGraphResponse {
  policy_version: string
  generated_at: string
  nodes: RecommendationGraphNode[]
  edges: RecommendationGraphEdge[]
  stats: {
    mode: 'content_only' | 'hybrid'
    node_count: number
    edge_count: number
    contributing_accounts: number
  }
  privacy: {
    minimum_shared_selectors: number
    identity_data_exposed: boolean
  }
}
