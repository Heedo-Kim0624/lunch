import type { MultiRoomState } from '../types/multiRoom'

const ROOM_TOKEN_PREFIX = 'lunch-multi-participant-token:'

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
