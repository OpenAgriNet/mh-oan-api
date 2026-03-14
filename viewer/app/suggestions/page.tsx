"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { ThemeToggle } from "@/components/theme-toggle";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Loader2, RefreshCw } from "lucide-react";

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
                      {s.target_language}
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
                      {selected.target_language}
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
        )}
      </div>
    </div>
  );
}
