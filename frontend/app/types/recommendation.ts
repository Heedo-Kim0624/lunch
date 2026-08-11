export interface FoodTicket {
  id: number
  name: string
  family: string
  description: string
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

