export interface MultiFoodSummary {
  id: number | null
  key: string
  name: string
  family: string
  cuisine: string
  is_custom: boolean
}

export type MultiChoiceSubmission =
  | { food_id: number }
  | { custom_name: string }

export interface MultiParticipant {
  id: number
  nickname: string
  is_host: boolean
  is_ready: boolean
  choice_count: number
}

export interface MultiRoomSelf {
  id: number
  is_host: boolean
  is_ready: boolean
  choices: MultiFoodSummary[]
}

export interface MultiRoomLeader {
  id: number | null
  key: string
  name: string
  votes: number
  is_custom: boolean
}

export interface MultiRoomResult {
  food: MultiFoodSummary & { description: string }
  votes: number
  draw_count: number
}

export type MultiBlockedReason =
  | 'waiting_for_participants'
  | 'waiting_for_choices'
  | 'no_overlap'
  | 'decision_complete'
  | null

export interface MultiRoomState {
  code: string
  status: 'WAITING' | 'DRAWN'
  expires_at: string
  participant_count: number
  participants: MultiParticipant[]
  self: MultiRoomSelf | null
  all_ready: boolean
  can_draw: boolean
  can_reroll: boolean
  blocked_reason: MultiBlockedReason
  leaders: MultiRoomLeader[]
  max_votes: number
  result: MultiRoomResult | null
}

export interface MultiRoomEnvelope {
  room: MultiRoomState
}

export interface MultiRoomJoinEnvelope extends MultiRoomEnvelope {
  participant_token: string
}

export interface FoodSearchEnvelope {
  foods: MultiFoodSummary[]
}
