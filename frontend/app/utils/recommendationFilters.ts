import type {
  RecommendationFilterKey,
  RecommendationFilters,
  RecommendationFilterValue,
} from '../types/recommendation'

export interface RecommendationFilterOption {
  label: string
  value: RecommendationFilterValue
}

export interface RecommendationFilterGroup {
  key: RecommendationFilterKey
  label: string
  options: RecommendationFilterOption[]
}

export const RECOMMENDATION_FILTER_GROUPS: RecommendationFilterGroup[] = [
  {
    key: 'temperature',
    label: '온도',
    options: [
      { value: 'hot', label: '뜨거운 것' },
      { value: 'cold', label: '차가운 것' },
    ],
  },
  {
    key: 'staples',
    label: '종류',
    options: [
      { value: 'rice', label: '밥' },
      { value: 'bread', label: '빵' },
      { value: 'noodle', label: '면' },
    ],
  },
  {
    key: 'cuisines',
    label: '나라',
    options: [
      { value: 'korean', label: '한식' },
      { value: 'chinese', label: '중식' },
      { value: 'western', label: '양식' },
      { value: 'japanese', label: '일식' },
      { value: 'southeast_asian', label: '동남아식' },
      { value: 'other', label: '그 외' },
    ],
  },
  {
    key: 'spice',
    label: '맵기',
    options: [
      { value: 'spicy', label: '매운 것' },
      { value: 'mild', label: '안 매운 것' },
    ],
  },
]

export function createEmptyRecommendationFilters(): RecommendationFilters {
  return {
    temperature: [],
    staples: [],
    cuisines: [],
    spice: [],
  }
}

export function cloneRecommendationFilters(
  filters: RecommendationFilters,
): RecommendationFilters {
  return {
    temperature: [...filters.temperature],
    staples: [...filters.staples],
    cuisines: [...filters.cuisines],
    spice: [...filters.spice],
  }
}

export function countRecommendationFilters(filters: RecommendationFilters): number {
  return Object.values(filters).reduce((total, values) => total + values.length, 0)
}

export function toggleRecommendationFilter(
  filters: RecommendationFilters,
  key: RecommendationFilterKey,
  value: RecommendationFilterValue,
): RecommendationFilters {
  const next = cloneRecommendationFilters(filters)
  const selected = next[key]
  next[key] = selected.includes(value)
    ? selected.filter(candidate => candidate !== value)
    : [...selected, value]
  return next
}
