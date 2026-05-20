/**
 * Icon — Unified icon wrapper for lucide-react components.
 *
 * Provides:
 * - Consistent sizing via CSS variables (--icon-sm, --icon-md, --icon-lg)
 * - Color inheritance via currentColor (theme-aware)
 * - Hover state support
 * - Accessibility (aria-label injection)
 *
 * Usage:
 *   <Icon name="wifi" size="md" label="Wireless connection" />
 *   <Icon name="wifi" size="sm" className="text-success" />
 */

import { type LucideProps } from "lucide-react";
import { forwardRef } from "react";

export type IconName =
  | "activity"
  | "alert-circle"
  | "alert-triangle"
  | "bar-chart-3"
  | "bell"
  | "block"
  | "book-open"
  | "brain"
  | "calendar"
  | "check"
  | "check-circle-2"
  | "chevron-down"
  | "chevron-left"
  | "chevron-right"
  | "chevron-up"
  | "clock"
  | "code"
  | "copy"
  | "cpu"
  | "database"
  | "download"
  | "ear"
  | "edit"
  | "external-link"
  | "eye"
  | "eye-off"
  | "file"
  | "file-question"
  | "file-text"
  | "filter"
  | "folder"
  | "gauge"
  | "globe"
  | "hash"
  | "heart"
  | "home"
  | "info"
  | "key"
  | "key-round"
  | "lightbulb"
  | "loader-2"
  | "lock"
  | "log-in"
  | "log-out"
  | "menu"
  | "mail"
  | "message-circle"
  | "message-square"
  | "mic"
  | "minus"
  | "more-horizontal"
  | "more-vertical"
  | "monitor"
  | "package"
  | "palette"
  | "panel-right"
  | "pause"
  | "pencil"
  | "play"
  | "plus"
  | "puzzle"
  | "radio"
  | "refresh-cw"
  | "rotate-ccw"
  | "rotate-cw"
  | "save"
  | "search"
  | "send"
  | "settings"
  | "settings-2"
  | "shield"
  | "shield-check"
  | "shield-off"
  | "sparkles"
  | "star"
  | "terminal"
  | "trash-2"
  | "trending-up"
  | "unlock"
  | "upload"
  | "user"
  | "users"
  | "volume-2"
  | "wifi"
  | "wifi-off"
  | "wrench"
  | "x"
  | "zap";

export type IconSize = "xs" | "sm" | "md" | "lg" | "xl";

const SIZE_MAP: Record<IconSize, string> = {
  xs: "h-3 w-3",
  sm: "h-4 w-4",
  md: "h-5 w-5",
  lg: "h-6 w-6",
  xl: "h-8 w-8",
};

export interface IconProps extends Omit<LucideProps, "ref"> {
  name: IconName;
  size?: IconSize;
  label?: string;
  ariaHidden?: boolean;
}

// Lucide icon imports - centralized
import {
  Activity,
  AlertCircle,
  AlertTriangle,
  BarChart3,
  Bell,
  Blocks,
  BookOpen,
  Brain,
  Calendar,
  Check,
  CheckCircle2,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  ChevronUp,
  ClipboardList,
  Clock,
  Code,
  Copy,
  Cpu,
  Database,
  Download,
  Ear,
  Edit,
  ExternalLink,
  Eye,
  EyeOff,
  File,
  FileQuestion,
  FileText,
  Filter,
  Folder,
  FormInput,
  Gauge,
  Globe,
  Hash,
  Heart,
  Home,
  Info,
  Key,
  KeyRound,
  Lightbulb,
  Loader2,
  Lock,
  LogIn,
  LogOut,
  Mail,
  Menu,
  MessageCircle,
  MessageSquare,
  Mic,
  Minus,
  MoreHorizontal,
  MoreVertical,
  Monitor,
  Package,
  Palette,
  PanelRight,
  Pause,
  Pencil,
  Play,
  Plus,
  Puzzle,
  Radio,
  RefreshCw,
  RotateCcw,
  RotateCw,
  Save,
  Search,
  Send,
  Settings,
  Settings2,
  Shield,
  ShieldCheck,
  ShieldOff,
  Sparkles,
  Star,
  Terminal,
  Trash2,
  TrendingUp,
  Unlock,
  Upload,
  User,
  Users,
  Volume2,
  Wifi,
  WifiOff,
  Wrench,
  X,
  Zap,
} from "lucide-react";

const ICON_MAP: Record<IconName, React.ComponentType<LucideProps>> = {
  activity: Activity,
  "alert-circle": AlertCircle,
  "alert-triangle": AlertTriangle,
  "bar-chart-3": BarChart3,
  bell: Bell,
  block: Blocks,
  "book-open": BookOpen,
  brain: Brain,
  calendar: Calendar,
  check: Check,
  "check-circle-2": CheckCircle2,
  "chevron-down": ChevronDown,
  "chevron-left": ChevronLeft,
  "chevron-right": ChevronRight,
  "chevron-up": ChevronUp,
  clock: Clock,
  code: Code,
  copy: Copy,
  cpu: Cpu,
  database: Database,
  download: Download,
  ear: Ear,
  edit: Edit,
  "external-link": ExternalLink,
  eye: Eye,
  "eye-off": EyeOff,
  file: File,
  "file-question": FileQuestion,
  "file-text": FileText,
  filter: Filter,
  folder: Folder,
  gauge: Gauge,
  globe: Globe,
  hash: Hash,
  heart: Heart,
  home: Home,
  info: Info,
  key: Key,
  "key-round": KeyRound,
  lightbulb: Lightbulb,
  "loader-2": Loader2,
  lock: Lock,
  "log-in": LogIn,
  "log-out": LogOut,
  mail: Mail,
  menu: Menu,
  "message-circle": MessageCircle,
  "message-square": MessageSquare,
  mic: Mic,
  minus: Minus,
  "more-horizontal": MoreHorizontal,
  "more-vertical": MoreVertical,
  monitor: Monitor,
  package: Package,
  palette: Palette,
  "panel-right": PanelRight,
  pause: Pause,
  pencil: Pencil,
  play: Play,
  plus: Plus,
  puzzle: Puzzle,
  radio: Radio,
  "refresh-cw": RefreshCw,
  "rotate-ccw": RotateCcw,
  "rotate-cw": RotateCw,
  save: Save,
  search: Search,
  send: Send,
  settings: Settings,
  "settings-2": Settings2,
  shield: Shield,
  "shield-check": ShieldCheck,
  "shield-off": ShieldOff,
  sparkles: Sparkles,
  star: Star,
  terminal: Terminal,
  "trash-2": Trash2,
  "trending-up": TrendingUp,
  unlock: Unlock,
  upload: Upload,
  user: User,
  users: Users,
  "volume-2": Volume2,
  wifi: Wifi,
  "wifi-off": WifiOff,
  wrench: Wrench,
  x: X,
  zap: Zap,
};

export const Icon = forwardRef<SVGSVGElement, IconProps>(function Icon(
  { name, size = "md", label, ariaHidden = false, className, ...props },
  ref,
) {
  const IconComponent = ICON_MAP[name];
  if (!IconComponent) {
    console.warn(`Icon "${name}" not found in registry`);
    return null;
  }

  return (
    <IconComponent
      ref={ref}
      className={`icon ${SIZE_MAP[size]} ${className ?? ""}`}
      aria-label={label}
      aria-hidden={ariaHidden || !!label ? undefined : true}
      {...props}
    />
  );
});
