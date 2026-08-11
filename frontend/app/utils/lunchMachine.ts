import type { RecommendationTicket } from '../types/recommendation'

export type MachineStatus =
  | 'idle'
  | 'drawing'
  | 'ticket'
  | 'rerolling'
  | 'accepted'
  | 'error'

export interface LunchMachineState {
  status: MachineStatus
  ticket: RecommendationTicket | null
  error: string | null
}

export function createInitialMachineState(): LunchMachineState {
  return {
    status: 'idle',
    ticket: null,
    error: null,
  }
}

export function beginDraw(): LunchMachineState {
  return {
    status: 'drawing',
    ticket: null,
    error: null,
  }
}

export function showTicket(
  _state: LunchMachineState,
  ticket: RecommendationTicket,
): LunchMachineState {
  return {
    status: 'ticket',
    ticket,
    error: null,
  }
}

export function acceptTicket(state: LunchMachineState): LunchMachineState {
  return {
    ...state,
    status: 'accepted',
    error: null,
  }
}

export function startReroll(state: LunchMachineState): LunchMachineState {
  return {
    ...state,
    status: 'rerolling',
    error: null,
  }
}

export function failMachine(state: LunchMachineState, error: string): LunchMachineState {
  return {
    ...state,
    status: 'error',
    error,
  }
}

