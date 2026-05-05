// Context Menu Types

export interface ContextMenuItem {
  id: 'open' | 'rename' | 'copy' | 'cut' | 'paste' | 'delete' | 'share' | 'info'
  label: string
  icon: string
  shortcut?: string
  danger?: boolean
  disabled?: boolean
  divider?: boolean
}

export interface ContextMenuPosition {
  x: number
  y: number
}

export interface ContextMenuState {
  visible: boolean
  position: ContextMenuPosition
  target: FileItem | null
  items: ContextMenuItem[]
}

export interface FileItem {
  path: string
  name: string
  is_directory: boolean
  size: number
  modified?: string
}

export interface FileOperationPayload {
  paths: string[]
  operation: 'copy' | 'cut' | 'delete' | 'rename' | 'share'
  newName?: string
  targetPath?: string
}