"use client";

import { useState } from "react";
import { ChevronRight, Brain } from "lucide-react";
import { cn } from "@/lib/utils";

interface ThinkingBlockProps {
  content: string;
}

export function ThinkingBlock({ content }: ThinkingBlockProps) {
  const [open, setOpen] = useState(false);

  return (
    <div className="border-l-2 border-amber-400 dark:border-amber-600 bg-amber-50/50 dark:bg-amber-950/20 rounded-r-md my-1">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 px-3 py-2 text-xs text-amber-700 dark:text-amber-400 hover:bg-amber-100/50 dark:hover:bg-amber-950/40 w-full text-left transition-colors"
      >
        <ChevronRight
          className={cn(
            "size-3.5 transition-transform",
            open && "rotate-90"
          )}
        />
        <Brain className="size-3.5" />
        <span className="font-medium">Thinking</span>
        {!open && (
          <span className="text-amber-600/60 dark:text-amber-500/60 truncate ml-1">
            {content.slice(0, 80)}...
          </span>
        )}
      </button>
      {open && (
        <div className="px-4 pb-3 text-sm text-amber-900 dark:text-amber-200 whitespace-pre-wrap font-mono leading-relaxed">
          {content}
        </div>
      )}
    </div>
  );
}
