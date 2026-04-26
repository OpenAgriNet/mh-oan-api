import type { ConversationRecord } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  MapPin,
  Sprout,
  Languages,
  Calendar,
  User,
  Hash,
  Database,
  Shield,
} from "lucide-react";

const langLabels: Record<string, string> = {
  mr: "Marathi",
  hi: "Hindi",
  en: "English",
  bhb: "Bhili",
};

interface ConversationHeaderProps {
  record: ConversationRecord;
}

export function ConversationHeader({ record }: ConversationHeaderProps) {
  const { profile, env } = record;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <User className="size-5" />
          {profile.name}
          <Badge variant="secondary" className="ml-2">
            {profile.mood}
          </Badge>
          {profile.has_agristack && (
            <Badge className="bg-emerald-100 text-emerald-800 border-emerald-300 dark:bg-emerald-900/40 dark:text-emerald-200 dark:border-emerald-700">
              Agristack
            </Badge>
          )}
          {profile.is_pocra && (
            <Badge className="bg-teal-100 text-teal-800 border-teal-300 dark:bg-teal-900/40 dark:text-teal-200 dark:border-teal-700">
              PoCRA
            </Badge>
          )}
        </CardTitle>
        <CardDescription>
          {profile.scenario.description}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <InfoItem
            icon={<MapPin className="size-4" />}
            label="Location"
            value={`${profile.village}, ${profile.taluka}, ${profile.district}`}
          />
          <InfoItem
            icon={<Sprout className="size-4" />}
            label="Crops"
            value={profile.crops.join(", ")}
          />
          <InfoItem
            icon={<Languages className="size-4" />}
            label="User Language"
            value={langLabels[profile.language] ?? profile.language}
          />
          <InfoItem
            icon={<Languages className="size-4" />}
            label="Target Language"
            value={langLabels[env.target_language] ?? env.target_language}
          />
          <InfoItem
            icon={<Hash className="size-4" />}
            label="Verbosity"
            value={profile.verbosity}
          />
          <InfoItem
            icon={<Calendar className="size-4" />}
            label="Sim Date"
            value={new Date(env.today_date).toLocaleDateString()}
          />
          <InfoItem
            icon={<Hash className="size-4" />}
            label="Scenario"
            value={`${profile.scenario.category} / ${profile.scenario.id}`}
          />
          <InfoItem
            icon={<Sprout className="size-4" />}
            label="Land"
            value={`${profile.land_acres} acres`}
          />
          <InfoItem
            icon={<Database className="size-4" />}
            label="Gender / Caste"
            value={`${profile.gender} / ${profile.caste_category}`}
          />
          <InfoItem
            icon={<Shield className="size-4" />}
            label="MahaDBT Schemes"
            value={profile.mahadbt_scheme_codes?.length > 0 ? profile.mahadbt_scheme_codes.join(", ") : "None"}
          />
        </div>
        <div className="mt-4 flex gap-2 text-xs text-muted-foreground">
          <span>Model: {env.agrinet_model}</span>
          <span>&middot;</span>
          <span>Turns: {record.turn_count}</span>
          <span>&middot;</span>
          <span>
            {record.completed
              ? "Completed"
              : record.error
              ? "Error"
              : "Incomplete"}
          </span>
        </div>
      </CardContent>
    </Card>
  );
}

function InfoItem({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
}) {
  return (
    <div className="flex items-start gap-2">
      <span className="text-muted-foreground mt-0.5">{icon}</span>
      <div>
        <div className="text-muted-foreground text-xs">{label}</div>
        <div>{value}</div>
      </div>
    </div>
  );
}
