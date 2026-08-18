import type {
  MultiChoiceSubmission,
  MultiFoodSummary,
  MultiRoomState,
} from '../types/multiRoom'

const ROOM_TOKEN_PREFIX = 'lunch-multi-participant-token:'
const DIRECT_MENU_PATTERN = /^[\p{L}\p{N} &+()/',.·_-]+$/u

export function multiApiUrl(base: string, path: string): string {
  return `${String(base).replace(/\/+$/, '')}/${path.replace(/^\/+/, '')}`
}

export function normalizeMultiChoiceName(value: string): string {
  return value.normalize('NFKC').trim().replace(/\s+/g, ' ').toLocaleLowerCase('ko-KR')
}

export function directChoiceForQuery(
  query: string,
  results: MultiFoodSummary[],
): MultiFoodSummary | null {
  const name = query.normalize('NFKC').trim().replace(/\s+/g, ' ')
  if (!name || name.length > 40 || !DIRECT_MENU_PATTERN.test(name)) {
    return null
  }
  const normalizedName = normalizeMultiChoiceName(name)
  const exactCatalogFood = results.find(
    food => !food.is_custom && normalizeMultiChoiceName(food.name) === normalizedName,
  )
  if (exactCatalogFood) {
    return exactCatalogFood
  }
  return {
    id: null,
    key: `custom:draft:${normalizedName}`,
    name,
    family: '직접 입력',
    cuisine: '사용자 메뉴',
    is_custom: true,
  }
}

export function multiChoiceSubmission(choice: MultiFoodSummary): MultiChoiceSubmission {
  if (choice.is_custom) {
    return { custom_name: choice.name }
  }
  if (choice.id === null) {
    throw new Error('카탈로그 음식 ID가 없어요.')
  }
  return { food_id: choice.id }
}

export function roomTokenStorageKey(code: string): string {
  return `${ROOM_TOKEN_PREFIX}${code.trim().toUpperCase()}`
}

export function multiRoomStatusMessage(room: MultiRoomState): string {
  if (room.blocked_reason === 'waiting_for_participants') {
    return '공유 링크를 보내고 한 명 이상 더 기다려 주세요.'
  }
  if (room.blocked_reason === 'waiting_for_choices') {
    const pending = room.participants.filter(participant => !participant.is_ready).length
    return `${pending}명이 먹고 싶은 목록을 작성하고 있어요.`
  }
  if (room.blocked_reason === 'no_overlap') {
    return '서로 겹치는 메뉴가 없어요. 목록을 수정해야 레버를 당길 수 있어요.'
  }
  if (room.blocked_reason === 'decision_complete') {
    return '단독 최다 메뉴로 결정됐어요.'
  }
  if (room.can_reroll) {
    return '공동 최다 메뉴가 여러 개예요. 레버를 다시 당길 수 있어요.'
  }
  return '모두 준비됐어요. 방장이 레버를 당기면 됩니다.'
}

export function multiLeverLabel(room: MultiRoomState): string {
  return room.can_reroll ? '공동 최다 메뉴 다시 뽑기' : '공동 점심 레버 당기기'
}

export function multiShareUrl(origin: string, code: string): string {
  return `${origin.replace(/\/$/, '')}/multi/${encodeURIComponent(code.toUpperCase())}`
}
