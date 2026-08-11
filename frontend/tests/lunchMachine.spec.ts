import { describe, expect, it } from 'vitest'

import {
  acceptTicket,
  beginDraw,
  createInitialMachineState,
  showTicket,
  startReroll,
} from '../app/utils/lunchMachine'

const ticket = {
  recommendationId: 1,
  sessionId: 'session-1',
  policyVersion: 'rules-v1',
  food: {
    id: 1,
    name: '순두부찌개',
    family: '찌개',
    description: '매콤하고 따뜻한 두부 국물 요리',
  },
  reason: '비 오는 날에 잘 맞는 따뜻한 국물 메뉴예요.',
}

describe('lunch machine state', () => {
  it('moves from idle to drawing to a visible ticket', () => {
    const drawing = beginDraw(createInitialMachineState())
    const revealed = showTicket(drawing, ticket)

    expect(drawing.status).toBe('drawing')
    expect(revealed.status).toBe('ticket')
    expect(revealed.ticket?.food.name).toBe('순두부찌개')
  })

  it('stamps an accepted ticket', () => {
    const revealed = showTicket(beginDraw(createInitialMachineState()), ticket)

    const accepted = acceptTicket(revealed)

    expect(accepted.status).toBe('accepted')
    expect(accepted.ticket).toEqual(ticket)
  })

  it('keeps the current ticket while reroll feedback is being sent', () => {
    const revealed = showTicket(beginDraw(createInitialMachineState()), ticket)

    const rerolling = startReroll(revealed)

    expect(rerolling.status).toBe('rerolling')
    expect(rerolling.ticket).toEqual(ticket)
  })
})

