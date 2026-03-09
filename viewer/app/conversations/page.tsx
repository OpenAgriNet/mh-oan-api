"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import type { ConversationSummary } from "@/lib/types";
import { ConversationList } from "@/components/conversation-list";
import { ThemeToggle } from "@/components/theme-toggle";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Loader2, Play, RefreshCw } from "lucide-react";

export default function ConversationsPage() {
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
          <div className="flex items-center gap-4">
            <Link href="/">
              <Button variant="ghost" size="sm">
                <ArrowLeft className="size-3.5" />
                Back to Stats
              </Button>
            </Link>
            <div>
              <h1 className="text-xl font-semibold">Conversations</h1>
              <p className="text-sm text-muted-foreground">
                Browse farmer-agent conversation transcripts
              </p>
            </div>
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
            <Link href="/simulate">
              <Button variant="outline" size="sm">
                <Play className="size-3.5" />
                Simulate New
              </Button>
            </Link>
            <ThemeToggle />
          </div>
        </div>
      </header>

      <main className="max-w-[1400px] mx-auto px-6 py-6">
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
          <ConversationList
            conversations={conversations}
            onDelete={(sessionId) =>
              setConversations((prev) =>
                prev.filter((c) => c.session_id !== sessionId)
              )
            }
          />
        )}
      </main>
    </div>
  );
}
