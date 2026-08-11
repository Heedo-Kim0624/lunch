export interface FoodTicket {
  id: number
  name: string
  family: string
  cuisine: string
  staple_types: string[]
  description: string
}

export type RecommendationFilterKey = 'temperature' | 'staples' | 'cuisines' | 'spice'

export type RecommendationFilterValue =
  | 'hot'
  | 'cold'
  | 'rice'
  | 'bread'
  | 'noodle'
  | 'korean'
  | 'chinese'
  | 'western'
  | 'japanese'
  | 'southeast_asian'
  | 'other'
  | 'spicy'
  | 'mild'

export interface RecommendationFilters {
  temperature: RecommendationFilterValue[]
  staples: RecommendationFilterValue[]
  cuisines: RecommendationFilterValue[]
  spice: RecommendationFilterValue[]
}

export interface RecommendationTicket {
  recommendationId: number
  sessionId: string
  policyVersion: string
  food: FoodTicket
  reason: string
}

export interface RecommendationApiResponse {
  recommendation_id: number
  session_id: string
  policy_version: string
  food: FoodTicket
  reason: string
  score_breakdown: Record<string, number>
}

export type FeedbackType =
  | 'ACCEPTED'
  | 'ATE'
  | 'REJECTED'
  | 'REROLLED'
  | 'FAVORITED'
  | 'DISLIKED'
