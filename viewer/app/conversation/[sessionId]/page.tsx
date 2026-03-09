"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import type { ConversationRecord } from "@/lib/types";
import { parseMessages } from "@/lib/parse-messages";
import { ConversationHeader } from "@/components/conversation-header";
import { MessageTimeline } from "@/components/message-timeline";
import { RawJsonViewer } from "@/components/raw-json-viewer";
import { ThemeToggle } from "@/components/theme-toggle";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Loader2 } from "lucide-react";

export default function ConversationPage() {
  const params = useParams();
  const sessionId = params.sessionId as string;

  const [record, setRecord] = useState<ConversationRecord | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!sessionId) return;
    setLoading(true);
    fetch(`/api/conversation/${sessionId}`)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((data: ConversationRecord) => {
        setRecord(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, [sessionId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="size-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error || !record) {
    return (
      <div className="max-w-4xl mx-auto px-6 py-12">
        <div className="bg-destructive/10 text-destructive rounded-md px-4 py-3 text-sm">
          {error ?? "Conversation not found"}
        </div>
        <Link href="/" className="mt-4 inline-block">
          <Button variant="ghost" size="sm">
            <ArrowLeft className="size-4" />
            Back
          </Button>
        </Link>
      </div>
    );
  }

  const timeline = parseMessages(
    record.agrinet_messages_json,
    record.user_messages_json
  );

  return (
    <div className="min-h-screen">
      <header className="border-b">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link href="/">
              <Button variant="ghost" size="icon">
                <ArrowLeft className="size-4" />
              </Button>
            </Link>
            <div>
              <h1 className="text-lg font-semibold">Conversation Detail</h1>
              <p className="text-xs text-muted-foreground font-mono">
                {sessionId}
              </p>
            </div>
          </div>
          <ThemeToggle />
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-6 space-y-6">
        <ConversationHeader record={record} />

        {record.error && (
          <div className="bg-destructive/10 text-destructive rounded-md px-4 py-3 text-sm">
            <div className="font-medium mb-1">Error</div>
            <pre className="text-xs whitespace-pre-wrap font-mono max-h-48 overflow-y-auto">
              {record.error}
            </pre>
          </div>
        )}

        <Tabs defaultValue="chat">
          <TabsList>
            <TabsTrigger value="chat">Chat</TabsTrigger>
            <TabsTrigger value="agrinet-json">MahaVistaar Raw JSON</TabsTrigger>
            <TabsTrigger value="user-json">User Raw JSON</TabsTrigger>
          </TabsList>

          <TabsContent value="chat">
            {timeline.length > 0 ? (
              <MessageTimeline entries={timeline} />
            ) : (
              <p className="text-muted-foreground text-sm py-8 text-center">
                No messages in this conversation.
              </p>
            )}
          </TabsContent>

          <TabsContent value="agrinet-json">
            <RawJsonViewer
              data={record.agrinet_messages_json}
              name="agrinet_messages"
            />
          </TabsContent>

          <TabsContent value="user-json">
            <RawJsonViewer
              data={record.user_messages_json}
              name="user_messages"
            />
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}
