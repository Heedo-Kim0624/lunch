import { describe, expect, it } from 'vitest'

import {
  cloneRecommendationFilters,
  countRecommendationFilters,
  createEmptyRecommendationFilters,
  toggleRecommendationFilter,
} from '../app/utils/recommendationFilters'

describe('recommendation filters', () => {
  it('starts with every group unrestricted', () => {
    const filters = createEmptyRecommendationFilters()

    expect(filters).toEqual({ temperature: [], staples: [], cuisines: [], spice: [] })
    expect(countRecommendationFilters(filters)).toBe(0)
  })

  it('allows multiple choices in the same group without mutating the source', () => {
    const source = createEmptyRecommendationFilters()
    const withRice = toggleRecommendationFilter(source, 'staples', 'rice')
    const withRiceAndNoodles = toggleRecommendationFilter(withRice, 'staples', 'noodle')

    expect(source.staples).toEqual([])
    expect(withRiceAndNoodles.staples).toEqual(['rice', 'noodle'])
    expect(countRecommendationFilters(withRiceAndNoodles)).toBe(2)
  })

  it('clones every selected-value array', () => {
    const source = toggleRecommendationFilter(
      createEmptyRecommendationFilters(),
      'temperature',
      'cold',
    )
    const clone = cloneRecommendationFilters(source)
    clone.temperature.push('hot')

    expect(source.temperature).toEqual(['cold'])
    expect(clone.temperature).toEqual(['cold', 'hot'])
  })
})
