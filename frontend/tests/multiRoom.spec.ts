import { describe, expect, it } from 'vitest'

import type { MultiRoomState } from '../app/types/multiRoom'
import {
  directChoiceForQuery,
  multiApiUrl,
  multiChoiceSubmission,
  multiLeverLabel,
  multiRoomStatusMessage,
  multiShareUrl,
  roomTokenStorageKey,
} from '../app/utils/multiRoom'

function room(overrides: Partial<MultiRoomState> = {}): MultiRoomState {
  return {
    code: 'ABC234WXYZ',
    status: 'WAITING',
    expires_at: '2026-08-13T12:00:00+09:00',
    participant_count: 2,
    participants: [
      { id: 1, nickname: '방장', is_host: true, is_ready: true, choice_count: 2 },
      { id: 2, nickname: '민지', is_host: false, is_ready: true, choice_count: 2 },
    ],
    self: null,
    all_ready: true,
    can_draw: true,
    can_reroll: false,
    blocked_reason: null,
    leaders: [{ id: 1, key: 'food:1', name: '치킨', votes: 2, is_custom: false }],
    max_votes: 2,
    result: null,
    ...overrides,
  }
}

describe('multi room presentation rules', () => {
  it('explains why no-overlap rooms cannot draw', () => {
    const message = multiRoomStatusMessage(
      room({ can_draw: false, blocked_reason: 'no_overlap', leaders: [], max_votes: 1 }),
    )

    expect(message).toContain('겹치는 메뉴가 없어요')
  })

  it('counts participants who still need to finish', () => {
    const state = room({
      all_ready: false,
      can_draw: false,
      blocked_reason: 'waiting_for_choices',
      participants: [
        { id: 1, nickname: '방장', is_host: true, is_ready: true, choice_count: 2 },
        { id: 2, nickname: '민지', is_host: false, is_ready: false, choice_count: 0 },
        { id: 3, nickname: '준', is_host: false, is_ready: false, choice_count: 0 },
      ],
    })

    expect(multiRoomStatusMessage(state)).toBe('2명이 먹고 싶은 목록을 작성하고 있어요.')
  })

  it('labels a tied leader draw as a reroll', () => {
    expect(multiLeverLabel(room({ can_reroll: true }))).toContain('다시 뽑기')
  })

  it('normalizes room token keys and share links', () => {
    expect(roomTokenStorageKey(' abc234wxyz ')).toBe(
      'lunch-multi-participant-token:ABC234WXYZ',
    )
    expect(multiShareUrl('https://lunch.example/', 'abc234wxyz')).toBe(
      'https://lunch.example/multi/ABC234WXYZ',
    )
  })

  it('builds a stable food-search URL regardless of trailing slashes', () => {
    expect(multiApiUrl('https://lunch.example/api/v1/', '/foods')).toBe(
      'https://lunch.example/api/v1/foods',
    )
  })

  it('uses an exact catalog match or creates a room-scoped direct choice', () => {
    const catalogFood = {
      id: 7,
      key: 'food:7',
      name: '라면',
      family: '면',
      cuisine: '한식',
      is_custom: false,
    }

    expect(directChoiceForQuery('  라면 ', [catalogFood])).toEqual(catalogFood)

    const custom = directChoiceForQuery('  새우   오일 파스타 ', [catalogFood])
    expect(custom).toMatchObject({
      id: null,
      name: '새우 오일 파스타',
      family: '직접 입력',
      is_custom: true,
    })
    expect(multiChoiceSubmission(custom!)).toEqual({ custom_name: '새우 오일 파스타' })
  })
})
