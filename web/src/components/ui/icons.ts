/**
 * Centralized icon registry and dynamic icon hook.
 *
 * Export all icons from a single place:
 *   import { icons, usePlatformIcon, useSessionIcon } from "@/components/ui/icons";
 *
 * Dynamic icon mapping for platform states and session sources:
 *   const { Icon, state } = usePlatformIcon("telegram", "connected");
 */

import type { LucideProps } from "lucide-react";
import {
  AlertCircle,
  AlertTriangle,
  Brain,
  Check,
  CheckCircle2,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  ChevronUp,
  Clock,
  Copy,
  Database,
  ExternalLink,
  Eye,
  Gauge,
  Globe,
  Hash,
  Lightbulb,
  LogIn,
  LogOut,
  MessageCircle,
  MessageSquare,
  Palette,
  PanelRight,
  Play,
  Radio,
  RefreshCw,
  Search,
  ShieldCheck,
  ShieldOff,
  Terminal,
  Trash2,
  Wifi,
  WifiOff,
  Wrench,
  X,
  Zap,
  Loader2,
  Send,
  Settings,
  User,
  Plus,
  Minus,
  MoreHorizontal,
  MoreVertical,
  Edit,
  Save,
  Download,
  Upload,
  Folder,
  File,
  FileText,
  Mail,
  Lock,
  Unlock,
  Key,
  Bell,
  Calendar,
  Home,
  Info,
} from "lucide-react";

// Platform icon mapping based on platform type
export const PLATFORM_ICONS: Record<string, React.ComponentType<LucideProps>> = {
  telegram: MessageCircle,
  slack: MessageSquare,
  discord: Hash,
  whatsapp: Globe,
  email: Mail,
  cli: Terminal,
  web: Globe,
  api: Terminal,
};

export type PlatformType = keyof typeof PLATFORM_ICONS;

// Platform connection state icons
export const PLATFORM_STATE_ICONS: Record<
  "connected" | "disconnected" | "fatal",
  React.ComponentType<LucideProps>
> = {
  connected: Wifi,
  disconnected: WifiOff,
  fatal: AlertTriangle,
};

// Session source icon mapping
export const SESSION_SOURCE_ICONS: Record<string, React.ComponentType<LucideProps>> = {
  telegram: MessageCircle,
  slack: MessageSquare,
  discord: Hash,
  whatsapp: Globe,
  cron: Clock,
  api: Terminal,
  cli: Terminal,
  web: Globe,
  database: Database,
};

// Status icon mapping
export const STATUS_ICONS: Record<
  "success" | "warning" | "error" | "info",
  React.ComponentType<LucideProps>
> = {
  success: CheckCircle2,
  warning: AlertTriangle,
  error: AlertCircle,
  info: Info,
};

// All icons registry for external access
export const icons = {
  AlertCircle,
  AlertTriangle,
  Brain,
  Check,
  CheckCircle2,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  ChevronUp,
  Clock,
  Copy,
  Database,
  ExternalLink,
  Eye,
  Gauge,
  Globe,
  Hash,
  Lightbulb,
  LogIn,
  LogOut,
  MessageCircle,
  MessageSquare,
  Palette,
  PanelRight,
  Play,
  Radio,
  RefreshCw,
  Search,
  ShieldCheck,
  ShieldOff,
  Terminal,
  Trash2,
  Wifi,
  WifiOff,
  Wrench,
  X,
  Zap,
  Loader2,
  Send,
  Settings,
  User,
  Plus,
  Minus,
  MoreHorizontal,
  MoreVertical,
  Edit,
  Save,
  Download,
  Upload,
  Folder,
  File,
  FileText,
  Mail,
  Lock,
  Unlock,
  Key,
  Bell,
  Calendar,
  Home,
  Info,
};

export type { LucideProps };
