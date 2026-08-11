import { computed, ref } from 'vue'

import type {
  FeedbackType,
  RecommendationApiResponse,
  RecommendationFilters,
  RecommendationTicket,
} from '../types/recommendation'
import {
  acceptTicket,
  beginDraw,
  createInitialMachineState,
  failMachine,
  showTicket,
  startReroll,
} from '../utils/lunchMachine'
import {
  cloneRecommendationFilters,
  createEmptyRecommendationFilters,
} from '../utils/recommendationFilters'

const DEVICE_ID_KEY = 'lunch-machine-device-id'

function createDeviceId(): string {
  if (globalThis.crypto?.randomUUID) {
    return globalThis.crypto.randomUUID()
  }
  return `local-${Date.now()}-${Math.random().toString(16).slice(2)}`
}

function getDeviceId(): string {
  const existing = localStorage.getItem(DEVICE_ID_KEY)
  if (existing) {
    return existing
  }
  const created = createDeviceId()
  localStorage.setItem(DEVICE_ID_KEY, created)
  return created
}

function getAutomaticContext(): Record<string, string | number> {
  const now = new Date()
  return {
    meal_type: 'LUNCH',
    weekday: new Intl.DateTimeFormat('en-US', { weekday: 'long' })
      .format(now)
      .toUpperCase(),
    hour: now.getHours(),
  }
}

function toTicket(response: RecommendationApiResponse): RecommendationTicket {
  return {
    recommendationId: response.recommendation_id,
    sessionId: response.session_id,
    policyVersion: response.policy_version,
    food: response.food,
    reason: response.reason,
  }
}

interface RecommendationError {
  message: string
  noMatches: boolean
}

function errorDetails(error: unknown): RecommendationError {
  if (typeof error === 'object' && error !== null && 'data' in error) {
    const data = (error as { data?: unknown }).data
    if (typeof data === 'object' && data !== null) {
      const payload = data as { code?: unknown, detail?: unknown }
      if (payload.code === 'no_matching_foods' && typeof payload.detail === 'string') {
        return { message: payload.detail, noMatches: true }
      }
      if (typeof payload.detail === 'string') {
        return { message: payload.detail, noMatches: false }
      }
    }
  }
  if (error instanceof Error && error.message) {
    return {
      message: '추천 서버와 연결하지 못했어요. 잠시 후 다시 당겨 주세요.',
      noMatches: false,
    }
  }
  return { message: '점심표를 만드는 중 문제가 생겼어요.', noMatches: false }
}

export function useLunchMachine() {
  const config = useRuntimeConfig()
  const { authorizationHeaders } = useAuth()
  const state = ref(createInitialMachineState())
  const isSendingFeedback = ref(false)
  const filters = ref(createEmptyRecommendationFilters())
  const noMatchingFoods = ref(false)

  const isBusy = computed(
    () =>
      state.value.status === 'drawing'
      || state.value.status === 'rerolling'
      || isSendingFeedback.value,
  )

  async function requestRecommendation(): Promise<void> {
    state.value = beginDraw()
    noMatchingFoods.value = false
    try {
      const response = await $fetch<RecommendationApiResponse>(
        `${config.public.apiBase}/recommendations`,
        {
          method: 'POST',
          headers: authorizationHeaders(),
          body: {
            anonymous_id: getDeviceId(),
            context: getAutomaticContext(),
            filters: filters.value,
          },
        },
      )
      state.value = showTicket(state.value, toTicket(response))
    }
    catch (error) {
      const details = errorDetails(error)
      noMatchingFoods.value = details.noMatches
      state.value = failMachine(state.value, details.message)
    }
  }

  async function sendFeedback(eventType: FeedbackType): Promise<void> {
    const ticket = state.value.ticket
    if (!ticket) {
      return
    }
    await $fetch(`${config.public.apiBase}/recommendations/${ticket.recommendationId}/feedback`, {
      method: 'POST',
      headers: authorizationHeaders(),
      body: {
        anonymous_id: getDeviceId(),
        event_type: eventType,
      },
    })
  }

  async function accept(): Promise<void> {
    if (!state.value.ticket || isBusy.value) {
      return
    }
    isSendingFeedback.value = true
    try {
      await sendFeedback('ACCEPTED')
      state.value = acceptTicket(state.value)
    }
    catch (error) {
      state.value = failMachine(state.value, errorDetails(error).message)
    }
    finally {
      isSendingFeedback.value = false
    }
  }

  async function reroll(): Promise<void> {
    if (!state.value.ticket || isBusy.value) {
      return
    }
    state.value = startReroll(state.value)
    try {
      await sendFeedback('REROLLED')
      await requestRecommendation()
    }
    catch (error) {
      state.value = failMachine(state.value, errorDetails(error).message)
    }
  }

  function setFilters(nextFilters: RecommendationFilters): void {
    filters.value = cloneRecommendationFilters(nextFilters)
  }

  return {
    state,
    isBusy,
    filters,
    noMatchingFoods,
    setFilters,
    draw: requestRecommendation,
    accept,
    reroll,
  }
}
