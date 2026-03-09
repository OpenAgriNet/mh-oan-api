"use client";

import { useMemo } from "react";
import type { ConversationSummary } from "@/lib/types";
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

const LANG_LABELS: Record<string, string> = {
  mr: "Marathi",
  en: "English",
};

const COLORS = [
  "#6366f1",
  "#f59e0b",
  "#10b981",
  "#ef4444",
  "#8b5cf6",
  "#06b6d4",
  "#f97316",
  "#84cc16",
  "#ec4899",
  "#14b8a6",
  "#a855f7",
  "#eab308",
];

const STATUS_COLORS: Record<string, string> = {
  Completed: "#10b981",
  Incomplete: "#f59e0b",
  Error: "#ef4444",
};

const MOOD_COLORS: Record<string, string> = {
  normal: "#6366f1",
  frustrated: "#f97316",
  adversarial: "#ef4444",
};

const VERBOSITY_COLORS: Record<string, string> = {
  low: "#06b6d4",
  medium: "#f59e0b",
  high: "#8b5cf6",
};

function formatLabel(s: string): string {
  return s
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

interface StatsDashboardProps {
  conversations: ConversationSummary[];
}

export function StatsDashboard({ conversations }: StatsDashboardProps) {
  const stats = useMemo(() => {
    const total = conversations.length;
    if (total === 0) return null;

    const completed = conversations.filter((c) => c.completed).length;
    const errors = conversations.filter((c) => c.has_error).length;
    const incomplete = total - completed - errors;
    const turns = conversations.map((c) => c.turn_count);
    const avgTurns = (turns.reduce((a, b) => a + b, 0) / total).toFixed(1);
    const maxTurns = Math.max(...turns);
    const minTurns = Math.min(...turns);

    // Agristack distribution
    const withAgristack = conversations.filter((c) => c.has_agristack).length;

    // Language distribution
    const langCounts: Record<string, number> = {};
    conversations.forEach((c) => {
      const l = c.target_language || "?";
      langCounts[l] = (langCounts[l] || 0) + 1;
    });
    const langData = Object.entries(langCounts)
      .map(([lang, count]) => ({
        name: LANG_LABELS[lang] ?? lang,
        value: count,
      }))
      .sort((a, b) => b.value - a.value);

    // Category distribution
    const catCounts: Record<string, number> = {};
    conversations.forEach((c) => {
      const cat = c.scenario_category || "?";
      catCounts[cat] = (catCounts[cat] || 0) + 1;
    });
    const catData = Object.entries(catCounts)
      .map(([cat, count]) => ({ name: formatLabel(cat), value: count }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 10);

    // Mood distribution
    const moodCounts: Record<string, number> = {};
    conversations.forEach((c) => {
      const m = c.mood || "?";
      moodCounts[m] = (moodCounts[m] || 0) + 1;
    });
    const moodData = Object.entries(moodCounts)
      .map(([mood, count]) => ({ name: mood, value: count }))
      .sort((a, b) => b.value - a.value);

    // Verbosity distribution
    const verbCounts: Record<string, number> = {};
    conversations.forEach((c) => {
      const v = c.verbosity || "?";
      verbCounts[v] = (verbCounts[v] || 0) + 1;
    });
    const verbData = Object.entries(verbCounts)
      .map(([v, count]) => ({ name: v, value: count }))
      .sort((a, b) => b.value - a.value);

    // Status distribution
    const statusData = [
      { name: "Completed", value: completed },
      { name: "Incomplete", value: incomplete },
      { name: "Error", value: errors },
    ].filter((d) => d.value > 0);

    // Turn count distribution
    const turnBuckets: Record<number, number> = {};
    turns.forEach((t) => {
      turnBuckets[t] = (turnBuckets[t] || 0) + 1;
    });
    const turnData = Object.entries(turnBuckets)
      .map(([t, count]) => ({ turns: Number(t), count }))
      .sort((a, b) => a.turns - b.turns);

    return {
      total,
      completed,
      errors,
      avgTurns,
      maxTurns,
      minTurns,
      withAgristack,
      langData,
      catData,
      moodData,
      verbData,
      statusData,
      turnData,
    };
  }, [conversations]);

  if (!stats) return null;

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-6 gap-3">
        <StatCard label="Total" value={stats.total} />
        <StatCard
          label="Completed"
          value={stats.completed}
          sub={`${((stats.completed / stats.total) * 100).toFixed(0)}%`}
        />
        <StatCard
          label="Errors"
          value={stats.errors}
          variant={stats.errors > 0 ? "destructive" : "default"}
        />
        <StatCard label="Avg Turns" value={stats.avgTurns} />
        <StatCard
          label="Turn Range"
          value={`${stats.minTurns}–${stats.maxTurns}`}
        />
        <StatCard
          label="Agristack"
          value={stats.withAgristack}
          sub={`${((stats.withAgristack / stats.total) * 100).toFixed(0)}%`}
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <ChartCard title="Languages">
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie
                data={stats.langData}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                outerRadius={70}
                innerRadius={35}
                paddingAngle={2}
                label={({ name, percent }) =>
                  `${name} ${((percent ?? 0) * 100).toFixed(0)}%`
                }
                labelLine={false}
                fontSize={11}
              >
                {stats.langData.map((_, i) => (
                  <Cell
                    key={i}
                    fill={COLORS[i % COLORS.length]}
                  />
                ))}
              </Pie>
              <Tooltip
                formatter={(value) => [value, "Count"]}
              />
            </PieChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Scenario Categories">
          <ResponsiveContainer width="100%" height={Math.min(300, Math.max(200, stats.catData.length * 30))}>
            <BarChart
              data={stats.catData}
              layout="vertical"
              margin={{ left: 8, right: 32, top: 4, bottom: 4 }}
            >
              <XAxis type="number" hide />
              <YAxis
                type="category"
                dataKey="name"
                width={120}
                tick={{ fontSize: 11 }}
                tickLine={false}
                axisLine={false}
              />
              <Tooltip
                formatter={(value) => [value, "Count"]}
              />
              <Bar
                dataKey="value"
                fill="#6366f1"
                radius={[0, 4, 4, 0]}
                barSize={18}
                label={{ position: "right", fontSize: 11 }}
              />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Turn Distribution">
          <ResponsiveContainer width="100%" height={200}>
            <BarChart
              data={stats.turnData}
              margin={{ left: 0, right: 12, top: 4, bottom: 4 }}
            >
              <XAxis
                dataKey="turns"
                tick={{ fontSize: 11 }}
                label={{
                  value: "Turns",
                  position: "insideBottom",
                  offset: -2,
                  fontSize: 11,
                }}
              />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip
                formatter={(value) => [value, "Conversations"]}
              />
              <Bar
                dataKey="count"
                fill="#10b981"
                radius={[4, 4, 0, 0]}
                barSize={20}
              />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Mood Distribution">
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie
                data={stats.moodData}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                outerRadius={70}
                innerRadius={35}
                paddingAngle={2}
                label={({ name, percent }) =>
                  `${formatLabel(name ?? "")} ${((percent ?? 0) * 100).toFixed(0)}%`
                }
                labelLine={false}
                fontSize={11}
              >
                {stats.moodData.map((entry, i) => (
                  <Cell
                    key={i}
                    fill={MOOD_COLORS[entry.name] ?? COLORS[i % COLORS.length]}
                  />
                ))}
              </Pie>
              <Tooltip
                formatter={(value) => [value, "Count"]}
              />
            </PieChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Verbosity Distribution">
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie
                data={stats.verbData}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                outerRadius={70}
                innerRadius={35}
                paddingAngle={2}
                label={({ name, percent }) =>
                  `${formatLabel(name ?? "")} ${((percent ?? 0) * 100).toFixed(0)}%`
                }
                labelLine={false}
                fontSize={11}
              >
                {stats.verbData.map((entry, i) => (
                  <Cell
                    key={i}
                    fill={VERBOSITY_COLORS[entry.name] ?? COLORS[i % COLORS.length]}
                  />
                ))}
              </Pie>
              <Tooltip
                formatter={(value) => [value, "Count"]}
              />
            </PieChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Completion Status">
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie
                data={stats.statusData}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                outerRadius={70}
                innerRadius={35}
                paddingAngle={2}
                label={({ name, percent }) =>
                  `${name} ${((percent ?? 0) * 100).toFixed(0)}%`
                }
                labelLine={false}
                fontSize={11}
              >
                {stats.statusData.map((entry, i) => (
                  <Cell
                    key={i}
                    fill={STATUS_COLORS[entry.name] ?? COLORS[i % COLORS.length]}
                  />
                ))}
              </Pie>
              <Tooltip
                formatter={(value) => [value, "Count"]}
              />
            </PieChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>
    </div>
  );
}

function StatCard({
  label,
  value,
  sub,
  variant = "default",
}: {
  label: string;
  value: string | number;
  sub?: string;
  variant?: "default" | "destructive";
}) {
  return (
    <div className="rounded-lg border px-4 py-3">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p
        className={`text-2xl font-semibold tabular-nums ${variant === "destructive" && Number(value) > 0 ? "text-destructive" : ""}`}
      >
        {value}
        {sub && (
          <span className="text-xs font-normal text-muted-foreground ml-1.5">
            {sub}
          </span>
        )}
      </p>
    </div>
  );
}

function ChartCard({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-lg border p-4">
      <h3 className="text-sm font-medium mb-3">{title}</h3>
      {children}
    </div>
  );
}
