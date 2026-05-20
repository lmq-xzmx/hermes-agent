import type { LucideProps } from "lucide-react";
import type { PlatformStatus } from "@/lib/api";
import { isoTimeAgo } from "@/lib/utils";
import { Badge } from "@nous-research/ui";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Icon } from "@/components/ui";
import type { IconName } from "@/components/ui";
import { useI18n } from "@/i18n";

// Platform icon mapping
const PLATFORM_ICONS: Record<string, IconName> = {
  telegram: "message-circle",
  slack: "message-square",
  discord: "hash",
  whatsapp: "globe",
  email: "mail",
  cli: "terminal",
  web: "globe",
  api: "terminal",
};

// Platform state icons and colors
const PLATFORM_STATE_CONFIG: Record<string, { icon: IconName; colorClass: string }> = {
  connected: { icon: "wifi", colorClass: "text-success" },
  disconnected: { icon: "wifi-off", colorClass: "text-warning" },
  fatal: { icon: "alert-triangle", colorClass: "text-destructive" },
};

interface PlatformItemProps {
  name: string;
  info: PlatformStatus;
  t: ReturnType<typeof useI18n>["t"];
}

function PlatformItem({ name, info, t }: PlatformItemProps) {
  const display = {
    connected: { tone: "success" as const, label: t.status.connected },
    disconnected: { tone: "warning" as const, label: t.status.disconnected },
    fatal: { tone: "destructive" as const, label: t.status.error },
  }[info.state] ?? { tone: "outline" as const, label: info.state };

  const platformIcon = PLATFORM_ICONS[name.toLowerCase()] ?? "globe";
  const stateConfig = PLATFORM_STATE_CONFIG[info.state] ?? PLATFORM_STATE_CONFIG.disconnected;

  return (
    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border border-border p-3 w-full">
      <div className="flex items-center gap-3 min-w-0 w-full">
        <Icon name={platformIcon} size="sm" className="shrink-0 text-muted-foreground" ariaHidden />

        <div className="flex flex-col gap-0.5 min-w-0">
          <span className="text-sm font-medium capitalize truncate">
            {name}
          </span>

          {info.error_message && (
            <span className="text-xs text-destructive">
              {info.error_message}
            </span>
          )}

          {info.updated_at && (
            <span className="text-xs text-muted-foreground">
              {t.status.lastUpdate}: {isoTimeAgo(info.updated_at)}
            </span>
          )}
        </div>
      </div>

      <div className="flex items-center gap-2">
        <Icon name={stateConfig.icon} size="sm" className={`shrink-0 ${stateConfig.colorClass}`} ariaHidden />
        <Badge
          tone={display.tone}
          className="shrink-0 self-start sm:self-center"
        >
          {display.tone === "success" && (
            <span className="mr-1 inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-current" />
          )}
          {display.label}
        </Badge>
      </div>
    </div>
  );
}

export function PlatformsCard({ platforms }: PlatformsCardProps) {
  const { t } = useI18n();

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Icon name="radio" size="md" className="text-muted-foreground" ariaHidden />
          <CardTitle className="text-base">
            {t.status.connectedPlatforms}
          </CardTitle>
        </div>
      </CardHeader>

      <CardContent className="grid gap-3">
        {platforms.map(([name, info]) => (
          <PlatformItem key={name} name={name} info={info} t={t} />
        ))}
      </CardContent>
    </Card>
  );
}

interface PlatformsCardProps {
  platforms: [string, PlatformStatus][];
}
