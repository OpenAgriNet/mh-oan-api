"use client";

import type { TimelineEntry } from "@/lib/types";
import { MessageBubble } from "./message-bubble";
import { ToolCallBlock } from "./tool-call-block";
import { SystemPromptBlock } from "./system-prompt-block";

interface MessageTimelineProps {
  entries: TimelineEntry[];
}

export function MessageTimeline({ entries }: MessageTimelineProps) {
  const toolReturns = new Map<string, string>();
  for (const entry of entries) {
    if (entry.type === "tool-return" && entry.toolCallId) {
      toolReturns.set(entry.toolCallId, entry.content ?? "");
    }
  }

  return (
    <div className="space-y-1">
      {entries.map((entry, i) => {
        switch (entry.type) {
          case "system-prompt":
            return (
              <SystemPromptBlock
                key={i}
                agent={entry.agent ?? "agrinet"}
                content={entry.content ?? ""}
              />
            );

          case "turn-separator":
            return (
              <div
                key={i}
                className="flex items-center gap-3 py-3"
              >
                <div className="flex-1 h-px bg-border" />
                <span className="text-xs font-medium text-muted-foreground px-2">
                  Turn {entry.turn}
                </span>
                <div className="flex-1 h-px bg-border" />
              </div>
            );

          case "user-message":
            return (
              <MessageBubble
                key={i}
                role="user"
                content={entry.content ?? ""}
              />
            );

          case "agent-text":
            return (
              <MessageBubble
                key={i}
                role="agent"
                content={entry.content ?? ""}
              />
            );


          case "tool-call":
            return (
              <div key={i} className="flex justify-end my-1">
                <div className="max-w-[85%]">
                  <ToolCallBlock
                    toolName={entry.toolName ?? "unknown"}
                    toolArgs={entry.toolArgs}
                    toolCallId={entry.toolCallId}
                    returnContent={
                      entry.toolCallId
                        ? toolReturns.get(entry.toolCallId)
                        : undefined
                    }
                  />
                </div>
              </div>
            );

          case "tool-return":
            return null;

          default:
            return null;
        }
      })}
    </div>
  );
}
