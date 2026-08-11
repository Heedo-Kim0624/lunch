import type {
  GraphCuisineGroup,
  RecommendationGraphEdge,
  RecommendationGraphNode,
} from '../types/recommendationGraph'

export const GRAPH_WIDTH = 960
export const GRAPH_HEIGHT = 620

const GROUP_CENTERS: Record<GraphCuisineGroup, { x: number, y: number }> = {
  korean: { x: 165, y: 170 },
  chinese: { x: 480, y: 135 },
  western: { x: 795, y: 170 },
  japanese: { x: 165, y: 455 },
  southeast_asian: { x: 480, y: 490 },
  other: { x: 795, y: 455 },
}

const GOLDEN_ANGLE = Math.PI * (3 - Math.sqrt(5))

export interface PositionedGraphNode extends RecommendationGraphNode {
  x: number
  y: number
}

export interface PositionedGraphEdge extends RecommendationGraphEdge {
  x1: number
  y1: number
  x2: number
  y2: number
}

export function positionGraphNodes(
  nodes: RecommendationGraphNode[],
): PositionedGraphNode[] {
  const buckets = new Map<GraphCuisineGroup, RecommendationGraphNode[]>()
  for (const node of nodes) {
    const bucket = buckets.get(node.cuisine_group) ?? []
    bucket.push(node)
    buckets.set(node.cuisine_group, bucket)
  }

  const positioned: PositionedGraphNode[] = []
  for (const [group, groupNodes] of buckets) {
    const center = GROUP_CENTERS[group]
    groupNodes
      .slice()
      .sort((a, b) => a.name.localeCompare(b.name, 'ko'))
      .forEach((node, index) => {
        const radius = index === 0 ? 0 : 30 + Math.sqrt(index) * 25
        const angle = index * GOLDEN_ANGLE
        positioned.push({
          ...node,
          x: Math.max(24, Math.min(GRAPH_WIDTH - 24, center.x + Math.cos(angle) * radius)),
          y: Math.max(24, Math.min(GRAPH_HEIGHT - 24, center.y + Math.sin(angle) * radius)),
        })
      })
  }
  return positioned
}

export function positionGraphEdges(
  edges: RecommendationGraphEdge[],
  nodes: PositionedGraphNode[],
): PositionedGraphEdge[] {
  const byId = new Map(nodes.map(node => [node.id, node]))
  return edges.flatMap((edge) => {
    const source = byId.get(edge.source)
    const target = byId.get(edge.target)
    if (!source || !target) return []
    return [{ ...edge, x1: source.x, y1: source.y, x2: target.x, y2: target.y }]
  })
}
