import type {
  MultiRoomEnvelope,
  MultiRoomJoinEnvelope,
  MultiRoomState,
} from '../types/multiRoom'
import { roomTokenStorageKey } from '../utils/multiRoom'

interface MultiRoomApiError {
  code?: string
  detail?: string
}

function errorMessage(error: unknown): string {
  if (typeof error === 'object' && error !== null && 'data' in error) {
    const payload = (error as { data?: MultiRoomApiError }).data
    if (payload?.detail) {
      return payload.detail
    }
  }
  return '공유방과 연결하지 못했어요. 잠시 후 다시 시도해 주세요.'
}

export function useMultiRoom(code: string) {
  const config = useRuntimeConfig()
  const normalizedCode = code.trim().toUpperCase()
  const room = ref<MultiRoomState | null>(null)
  const token = ref<string | null>(null)
  const isLoading = ref(true)
  const isMutating = ref(false)
  const error = ref('')
  let pollTimer: ReturnType<typeof setInterval> | null = null
  let refreshInFlight = false

  function requestHeaders(): Record<string, string> {
    return token.value ? { 'X-Multi-Token': token.value } : {}
  }

  function saveToken(nextToken: string): void {
    token.value = nextToken
    localStorage.setItem(roomTokenStorageKey(normalizedCode), nextToken)
  }

  function clearToken(): void {
    token.value = null
    localStorage.removeItem(roomTokenStorageKey(normalizedCode))
  }

  async function refresh(silent = false): Promise<void> {
    if (refreshInFlight) {
      return
    }
    refreshInFlight = true
    if (!silent) {
      isLoading.value = true
    }
    try {
      const response = await $fetch<MultiRoomEnvelope>(
        `${config.public.apiBase}/multi/rooms/${encodeURIComponent(normalizedCode)}`,
        { headers: requestHeaders() },
      )
      room.value = response.room
      error.value = ''
      if (token.value && !response.room.self) {
        clearToken()
      }
    }
    catch (caught) {
      if (!silent) {
        error.value = errorMessage(caught)
      }
    }
    finally {
      isLoading.value = false
      refreshInFlight = false
    }
  }

  async function initialize(): Promise<void> {
    token.value = localStorage.getItem(roomTokenStorageKey(normalizedCode))
    await refresh()
  }

  async function join(nickname: string): Promise<void> {
    isMutating.value = true
    error.value = ''
    try {
      const response = await $fetch<MultiRoomJoinEnvelope>(
        `${config.public.apiBase}/multi/rooms/${encodeURIComponent(normalizedCode)}/join`,
        { method: 'POST', body: { nickname } },
      )
      saveToken(response.participant_token)
      room.value = response.room
    }
    catch (caught) {
      error.value = errorMessage(caught)
      throw caught
    }
    finally {
      isMutating.value = false
    }
  }

  async function submitChoices(foodIds: number[]): Promise<void> {
    isMutating.value = true
    error.value = ''
    try {
      const response = await $fetch<MultiRoomEnvelope>(
        `${config.public.apiBase}/multi/rooms/${encodeURIComponent(normalizedCode)}/choices`,
        {
          method: 'PUT',
          headers: requestHeaders(),
          body: { food_ids: foodIds },
        },
      )
      room.value = response.room
    }
    catch (caught) {
      error.value = errorMessage(caught)
      throw caught
    }
    finally {
      isMutating.value = false
    }
  }

  async function draw(): Promise<void> {
    isMutating.value = true
    error.value = ''
    try {
      const response = await $fetch<MultiRoomEnvelope>(
        `${config.public.apiBase}/multi/rooms/${encodeURIComponent(normalizedCode)}/draw`,
        { method: 'POST', headers: requestHeaders() },
      )
      room.value = response.room
    }
    catch (caught) {
      error.value = errorMessage(caught)
      throw caught
    }
    finally {
      isMutating.value = false
    }
  }

  function startPolling(): void {
    if (pollTimer) {
      return
    }
    pollTimer = setInterval(() => void refresh(true), 3000)
  }

  function stopPolling(): void {
    if (pollTimer) {
      clearInterval(pollTimer)
      pollTimer = null
    }
  }

  return {
    room,
    isLoading,
    isMutating,
    error,
    initialize,
    refresh,
    join,
    submitChoices,
    draw,
    startPolling,
    stopPolling,
  }
}
