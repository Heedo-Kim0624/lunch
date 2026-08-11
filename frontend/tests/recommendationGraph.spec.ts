import { describe, expect, it } from 'vitest'

import type {
  RecommendationGraphEdge,
  RecommendationGraphNode,
} from '../app/types/recommendationGraph'
import {
  GRAPH_HEIGHT,
  GRAPH_WIDTH,
  positionGraphEdges,
  positionGraphNodes,
} from '../app/utils/recommendationGraph'

const nodes: RecommendationGraphNode[] = [
  {
    id: 1,
    name: '치킨',
    family: '치킨',
    cuisine: '한식',
    cuisine_group: 'korean',
    attributes: { protein: 0.8 },
    selector_count: 5,
  },
  {
    id: 2,
    name: '라면',
    family: '라면',
    cuisine: '일식',
    cuisine_group: 'japanese',
    attributes: { broth: 0.8 },
    selector_count: 5,
  },
]

describe('recommendation graph layout', () => {
  it('positions every node deterministically inside the view box', () => {
    const first = positionGraphNodes(nodes)
    const second = positionGraphNodes(nodes)

    expect(first).toEqual(second)
    expect(first).toHaveLength(nodes.length)
    for (const node of first) {
      expect(node.x).toBeGreaterThanOrEqual(0)
      expect(node.x).toBeLessThanOrEqual(GRAPH_WIDTH)
      expect(node.y).toBeGreaterThanOrEqual(0)
      expect(node.y).toBeLessThanOrEqual(GRAPH_HEIGHT)
    }
    expect(first[0]?.y).not.toBe(first[1]?.y)
  })

  it('joins only edges whose endpoints are visible', () => {
    const edges: RecommendationGraphEdge[] = [
      {
        source: 1,
        target: 2,
        relation: 'hybrid',
        similarity: 0.8,
        content_similarity: 0.7,
        collaborative_similarity: 0.8,
        selector_count: 5,
      },
      {
        source: 1,
        target: 99,
        relation: 'content',
        similarity: 0.9,
        content_similarity: 0.9,
        collaborative_similarity: 0,
        selector_count: 0,
      },
    ]

    const positioned = positionGraphEdges(edges, positionGraphNodes(nodes))

    expect(positioned).toHaveLength(1)
    expect(positioned[0]).toMatchObject({ source: 1, target: 2, relation: 'hybrid' })
  })
})
