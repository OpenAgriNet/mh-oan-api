"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import type { ConversationSummary } from "@/lib/types";
import { StatsDashboard } from "@/components/stats-dashboard";
import { ThemeToggle } from "@/components/theme-toggle";
import { Button } from "@/components/ui/button";
import { ArrowRight, Loader2, RefreshCw } from "lucide-react";

export default function HomePage() {
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchConversations = useCallback(() => {
    setLoading(true);
    setError(null);
    fetch("/api/conversations")
      .then((r) => r.json())
      .then((data: ConversationSummary[]) => {
        setConversations(data);
        setLoading(false);
      })
      .catch(() => {
        setError("Failed to connect to backend. Is the server running on :8000?");
        setLoading(false);
      });
  }, []);

  useEffect(() => {
    fetchConversations();
  }, [fetchConversations]);

  return (
    <div className="min-h-screen">
      <header className="border-b">
        <div className="max-w-[1400px] mx-auto px-6 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold">
              MahaVistaar Synthetic Viewer
            </h1>
            <p className="text-sm text-muted-foreground">
              Dataset stats and distribution overview
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              size="sm"
              onClick={fetchConversations}
              disabled={loading}
            >
              <RefreshCw className={`size-3.5 ${loading ? "animate-spin" : ""}`} />
              Refresh
            </Button>
            <ThemeToggle />
          </div>
        </div>
      </header>

      <main className="max-w-[1400px] mx-auto px-6 py-6 space-y-6">
        {loading && (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="size-5 animate-spin text-muted-foreground" />
          </div>
        )}

        {error && (
          <div className="bg-destructive/10 text-destructive rounded-md px-4 py-3 text-sm">
            {error}
          </div>
        )}

        {!loading && !error && (
          <>
            <StatsDashboard conversations={conversations} />
            <div className="flex justify-center gap-3 pt-2">
              <Link href="/conversations">
                <Button variant="outline" size="lg">
                  View All Conversations
                  <ArrowRight className="size-4 ml-1" />
                </Button>
              </Link>
              <Link href="/suggestions">
                <Button variant="outline" size="lg">
                  View Suggestions
                  <ArrowRight className="size-4 ml-1" />
                </Button>
              </Link>
            </div>
          </>
        )}
      </main>
    </div>
  );
}
