/**
 * Dynamic icon hooks for platform, session, and status icons.
 *
 * Usage:
 *   const IconComponent = usePlatformIcon("telegram");
 *   const { Icon: StateIcon, colorClass } = usePlatformStateIcon("connected");
 *   const IconComponent = useSessionIcon("slack");
 */

import type { LucideProps } from "lucide-react";
import { useMemo } from "react";
import {
  Globe,
  Wifi,
  WifiOff,
  AlertTriangle,
  Info,
  MessageCircle,
  MessageSquare,
  Hash,
  Mail,
  Terminal,
  Clock,
  Database,
  CheckCircle2,
} from "lucide-react";

// Platform icon mapping
const PLATFORM_ICONS: Record<string, React.ComponentType<LucideProps>> = {
  telegram: MessageCircle,
  slack: MessageSquare,
  discord: Hash,
  whatsapp: Globe,
  email: Mail,
  cli: Terminal,
  web: Globe,
  api: Terminal,
};

// Session source icon mapping
const SESSION_SOURCE_ICONS: Record<string, React.ComponentType<LucideProps>> = {
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
const STATUS_ICONS: Record<
  "success" | "warning" | "error" | "info",
  React.ComponentType<LucideProps>
> = {
  success: CheckCircle2,
  warning: AlertTriangle,
  error: AlertTriangle,
  info: Info,
};

/**
 * Get the appropriate icon component for a platform type.
 * Falls back to Globe if platform type is unknown.
 */
export function usePlatformIcon(
  platform: string,
): React.ComponentType<LucideProps> {
  return useMemo(
    () => PLATFORM_ICONS[platform.toLowerCase()] ?? Globe,
    [platform],
  );
}

/**
 * Get the appropriate icon and color class for a platform connection state.
 */
export function usePlatformStateIcon(
  state: "connected" | "disconnected" | "fatal",
): {
  Icon: React.ComponentType<LucideProps>;
  colorClass: string;
} {
  return useMemo(() => {
    const iconMap = {
      connected: { Icon: Wifi, colorClass: "text-success" },
      disconnected: { Icon: WifiOff, colorClass: "text-warning" },
      fatal: { Icon: AlertTriangle, colorClass: "text-destructive" },
    } as const;
    return (
      iconMap[state] ?? { Icon: WifiOff, colorClass: "text-warning" }
    );
  }, [state]);
}

/**
 * Get the appropriate icon component for a session source.
 * Falls back to Globe if source is unknown.
 */
export function useSessionIcon(
  source: string,
): React.ComponentType<LucideProps> {
  return useMemo(
    () => SESSION_SOURCE_ICONS[source.toLowerCase()] ?? Globe,
    [source],
  );
}

/**
 * Get the appropriate icon for a status level.
 */
export function useStatusIcon(
  status: "success" | "warning" | "error" | "info",
): React.ComponentType<LucideProps> {
  return useMemo(() => STATUS_ICONS[status] ?? Info, [status]);
}
