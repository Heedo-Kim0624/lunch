import { computed, ref } from 'vue'

import type {
  FeedbackType,
  RecommendationApiResponse,
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

function errorMessage(error: unknown): string {
  if (error instanceof Error && error.message) {
    return '추천 서버와 연결하지 못했어요. 잠시 후 다시 당겨 주세요.'
  }
  return '점심표를 만드는 중 문제가 생겼어요.'
}

export function useLunchMachine() {
  const config = useRuntimeConfig()
  const { authorizationHeaders } = useAuth()
  const state = ref(createInitialMachineState())
  const isSendingFeedback = ref(false)

  const isBusy = computed(
    () =>
      state.value.status === 'drawing'
      || state.value.status === 'rerolling'
      || isSendingFeedback.value,
  )

  async function requestRecommendation(): Promise<void> {
    state.value = beginDraw()
    try {
      const response = await $fetch<RecommendationApiResponse>(
        `${config.public.apiBase}/recommendations`,
        {
          method: 'POST',
          headers: authorizationHeaders(),
          body: {
            anonymous_id: getDeviceId(),
            context: getAutomaticContext(),
          },
        },
      )
      state.value = showTicket(state.value, toTicket(response))
    }
    catch (error) {
      state.value = failMachine(state.value, errorMessage(error))
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
      state.value = failMachine(state.value, errorMessage(error))
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
      state.value = failMachine(state.value, errorMessage(error))
    }
  }

  return {
    state,
    isBusy,
    draw: requestRecommendation,
    accept,
    reroll,
  }
}
