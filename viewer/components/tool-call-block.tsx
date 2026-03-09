"use client";

import { useState } from "react";
import { ChevronRight, Wrench } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface ToolCallBlockProps {
  toolName: string;
  toolArgs?: string | Record<string, unknown>;
  toolCallId?: string;
  returnContent?: string;
}

function normalizeArgs(args: string | Record<string, unknown> | undefined): string {
  if (!args) return "";
  if (typeof args === "object") return JSON.stringify(args, null, 2);
  try {
    return JSON.stringify(JSON.parse(args), null, 2);
  } catch {
    return args;
  }
}

function previewArgs(args: string | Record<string, unknown> | undefined): string {
  if (!args) return "";
  const s = typeof args === "object" ? JSON.stringify(args) : args;
  return s.slice(0, 60);
}

export function ToolCallBlock({
  toolName,
  toolArgs,
  toolCallId,
  returnContent,
}: ToolCallBlockProps) {
  const [open, setOpen] = useState(false);

  return (
    <div className="border border-purple-200 dark:border-purple-800 bg-purple-50/50 dark:bg-purple-950/20 rounded-md my-1 overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 px-3 py-2 text-xs w-full text-left hover:bg-purple-100/50 dark:hover:bg-purple-950/40 transition-colors"
      >
        <ChevronRight
          className={cn(
            "size-3.5 transition-transform text-purple-600 dark:text-purple-400",
            open && "rotate-90"
          )}
        />
        <Wrench className="size-3.5 text-purple-600 dark:text-purple-400" />
        <Badge className="bg-purple-100 text-purple-800 border-purple-300 dark:bg-purple-900 dark:text-purple-200 dark:border-purple-700 text-xs">
          {toolName}
        </Badge>
        {!open && toolArgs && (
          <span className="text-muted-foreground truncate ml-1 font-mono">
            {previewArgs(toolArgs)}
          </span>
        )}
      </button>
      {open && (
        <div className="border-t border-purple-200 dark:border-purple-800">
          {toolArgs && (
            <div className="px-4 py-2">
              <div className="text-xs font-medium text-purple-700 dark:text-purple-300 mb-1">
                Arguments
              </div>
              <pre className="text-xs font-mono bg-purple-100/50 dark:bg-purple-950/50 p-2 rounded overflow-x-auto">
                {normalizeArgs(toolArgs)}
              </pre>
            </div>
          )}
          {returnContent && (
            <div className="px-4 py-2 border-t border-purple-200 dark:border-purple-800">
              <div className="text-xs font-medium text-purple-700 dark:text-purple-300 mb-1">
                Return
              </div>
              <div className="text-xs font-mono bg-purple-100/50 dark:bg-purple-950/50 p-2 rounded overflow-x-auto whitespace-pre-wrap max-h-64 overflow-y-auto">
                {returnContent}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
