// File Selection Types

export interface FileSelectionState {
  selectedPaths: Set<string>
  hoveredPath: string | null
  dragRect: DOMRect | null
  isDragging: boolean
  lastClickedPath: string | null
}

export type SelectionAction =
  | { type: 'single'; path: string }
  | { type: 'multi'; paths: string[] }
  | { type: 'range'; path: string; from: string }
  | { type: 'add'; path: string }
  | { type: 'clear' }