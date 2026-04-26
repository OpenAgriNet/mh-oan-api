"use client";

import { useEffect, useState, useCallback, useMemo } from "react";
import Link from "next/link";
import { ThemeToggle } from "@/components/theme-toggle";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Loader2, RefreshCw } from "lucide-react";
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

interface SuggestionSummary {
  id: string;
  source_session_id: string;
  target_language: string;
  suggestion_count: number;
}

interface SuggestionDetail {
  id: string;
  source_session_id: string;
  target_language: string;
  suggestions_input: string;
  suggestions: string[];
}

const LANG_LABELS: Record<string, string> = {
  mr: "Marathi",
  hi: "Hindi",
  en: "English",
  bhb: "Bhili",
};

const COLORS = ["#6366f1", "#f59e0b", "#10b981", "#ef4444", "#8b5cf6", "#06b6d4"];

export default function SuggestionsPage() {
  const [suggestions, setSuggestions] = useState<SuggestionSummary[]>([]);
  const [selected, setSelected] = useState<SuggestionDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSuggestions = useCallback(() => {
    setLoading(true);
    setError(null);
    fetch("/api/suggestions")
      .then((r) => r.json())
      .then((data: SuggestionSummary[]) => {
        setSuggestions(data);
        setLoading(false);
      })
      .catch(() => {
        setError("Failed to connect to backend. Is the server running on :8000?");
        setLoading(false);
      });
  }, []);

  useEffect(() => {
    fetchSuggestions();
  }, [fetchSuggestions]);

  const stats = useMemo(() => {
    const langCounts: Record<string, number> = {};
    let totalSuggestions = 0;
    for (const s of suggestions) {
      const label = LANG_LABELS[s.target_language] || s.target_language;
      langCounts[label] = (langCounts[label] || 0) + 1;
      totalSuggestions += s.suggestion_count;
    }
    const langData = Object.entries(langCounts)
      .map(([name, value]) => ({ name, value }))
      .sort((a, b) => b.value - a.value);

    const suggCountCounts: Record<number, number> = {};
    for (const s of suggestions) {
      suggCountCounts[s.suggestion_count] = (suggCountCounts[s.suggestion_count] || 0) + 1;
    }
    const countData = Object.entries(suggCountCounts)
      .map(([name, value]) => ({ name: `${name} suggestions`, value }))
      .sort((a, b) => parseInt(a.name) - parseInt(b.name));

    return { langData, countData, totalSuggestions };
  }, [suggestions]);

  const loadDetail = (id: string) => {
    fetch(`/api/suggestion/${id}`)
      .then((r) => r.json())
      .then((data: SuggestionDetail) => setSelected(data))
      .catch(() => setError("Failed to load suggestion detail"));
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="border-b">
        <div className="container mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link href="/">
              <Button variant="ghost" size="sm">
                <ArrowLeft className="h-4 w-4 mr-1" /> Back
              </Button>
            </Link>
            <h1 className="text-xl font-semibold">Suggestions</h1>
            <span className="text-sm text-muted-foreground">
              {suggestions.length} records
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={fetchSuggestions}>
              <RefreshCw className="h-4 w-4 mr-1" /> Refresh
            </Button>
            <ThemeToggle />
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-6">
        {loading && (
          <div className="flex justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        )}

        {error && (
          <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-destructive">
            {error}
          </div>
        )}

        {!loading && !error && (
          <div className="space-y-6">
            {/* Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="rounded-lg border p-4">
                <p className="text-2xl font-bold">{suggestions.length}</p>
                <p className="text-xs text-muted-foreground">Total Records</p>
              </div>
              <div className="rounded-lg border p-4">
                <p className="text-2xl font-bold">{stats.totalSuggestions}</p>
                <p className="text-xs text-muted-foreground">Total Suggestions</p>
              </div>
              <div className="rounded-lg border p-4">
                <p className="text-sm font-medium text-muted-foreground mb-2">Language Distribution</p>
                <ResponsiveContainer width="100%" height={140}>
                  <PieChart>
                    <Pie
                      data={stats.langData}
                      dataKey="value"
                      nameKey="name"
                      cx="50%"
                      cy="50%"
                      outerRadius={55}
                      innerRadius={28}
                      paddingAngle={2}
                      label={({ name, percent }) =>
                        `${name} ${((percent ?? 0) * 100).toFixed(0)}%`
                      }
                      labelLine={false}
                    >
                      {stats.langData.map((_, i) => (
                        <Cell key={i} fill={COLORS[i % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value) => [value, "Count"]} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="rounded-lg border p-4">
                <p className="text-sm font-medium text-muted-foreground mb-2">Suggestions per Record</p>
                <ResponsiveContainer width="100%" height={140}>
                  <PieChart>
                    <Pie
                      data={stats.countData}
                      dataKey="value"
                      nameKey="name"
                      cx="50%"
                      cy="50%"
                      outerRadius={55}
                      innerRadius={28}
                      paddingAngle={2}
                      label={({ name, percent }) =>
                        `${name} ${((percent ?? 0) * 100).toFixed(0)}%`
                      }
                      labelLine={false}
                    >
                      {stats.countData.map((_, i) => (
                        <Cell key={i} fill={COLORS[i % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value) => [value, "Count"]} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* List */}
            <div className="space-y-2">
              <h2 className="text-sm font-medium text-muted-foreground mb-3">
                Select a suggestion to view
              </h2>
              {suggestions.map((s) => (
                <button
                  key={s.id}
                  onClick={() => loadDetail(s.id)}
                  className={`w-full text-left rounded-lg border p-3 hover:bg-accent transition-colors ${
                    selected?.id === s.id ? "border-primary bg-accent" : ""
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono text-muted-foreground">
                      {s.id.slice(0, 8)}...
                    </span>
                    <span className="text-xs px-2 py-0.5 rounded-full bg-primary/10 text-primary">
                      {LANG_LABELS[s.target_language] ?? s.target_language}
                    </span>
                  </div>
                  <div className="text-sm mt-1">
                    {s.suggestion_count} suggestions &middot; from{" "}
                    <Link
                      href={`/conversation/${s.source_session_id}`}
                      className="text-primary hover:underline"
                      onClick={(e) => e.stopPropagation()}
                    >
                      {s.source_session_id.slice(0, 8)}...
                    </Link>
                  </div>
                </button>
              ))}
              {suggestions.length === 0 && (
                <p className="text-muted-foreground text-sm">
                  No suggestions generated yet.
                </p>
              )}
            </div>

            {/* Detail */}
            <div>
              {selected ? (
                <div className="rounded-lg border p-4 space-y-4">
                  <div className="flex items-center justify-between">
                    <h2 className="font-semibold">Suggestion Detail</h2>
                    <span className="text-xs px-2 py-0.5 rounded-full bg-primary/10 text-primary">
                      {LANG_LABELS[selected.target_language] ??
                        selected.target_language}
                    </span>
                  </div>

                  <div>
                    <h3 className="text-sm font-medium text-muted-foreground mb-2">
                      Conversation Context (Input)
                    </h3>
                    <div className="rounded-md bg-muted p-3 text-sm whitespace-pre-wrap max-h-96 overflow-y-auto">
                      {selected.suggestions_input}
                    </div>
                  </div>

                  <div>
                    <h3 className="text-sm font-medium text-muted-foreground mb-2">
                      Generated Suggestions
                    </h3>
                    <div className="space-y-2">
                      {selected.suggestions.map((s, i) => (
                        <div
                          key={i}
                          className="rounded-md border bg-background p-3 text-sm"
                        >
                          {s}
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="text-xs text-muted-foreground">
                    Source:{" "}
                    <Link
                      href={`/conversation/${selected.source_session_id}`}
                      className="text-primary hover:underline"
                    >
                      {selected.source_session_id}
                    </Link>
                  </div>
                </div>
              ) : (
                <div className="rounded-lg border border-dashed p-12 text-center text-muted-foreground">
                  Select a suggestion from the list to view details
                </div>
              )}
            </div>
          </div>
          </div>
        )}
      </div>
    </div>
  );
}
