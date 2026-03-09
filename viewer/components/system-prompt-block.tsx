"use client";

import { useState } from "react";
import { ChevronRight, FileText } from "lucide-react";
import { cn } from "@/lib/utils";

interface SystemPromptBlockProps {
  agent: "user" | "agrinet";
  content: string;
}

export function SystemPromptBlock({ agent, content }: SystemPromptBlockProps) {
  const [open, setOpen] = useState(false);
  const label = agent === "user" ? "User Agent" : "MahaVistaar Agent";

  return (
    <div className="border border-slate-200 dark:border-slate-700 bg-slate-50/50 dark:bg-slate-800/30 rounded-md my-2 overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 px-3 py-2 text-xs w-full text-left hover:bg-slate-100/50 dark:hover:bg-slate-800/50 transition-colors"
      >
        <ChevronRight
          className={cn(
            "size-3.5 transition-transform text-slate-500",
            open && "rotate-90"
          )}
        />
        <FileText className="size-3.5 text-slate-500" />
        <span className="font-medium text-slate-700 dark:text-slate-300">
          System Prompt — {label}
        </span>
      </button>
      {open && (
        <div className="border-t border-slate-200 dark:border-slate-700 px-4 py-3 text-sm whitespace-pre-wrap font-mono leading-relaxed max-h-96 overflow-y-auto">
          {content}
        </div>
      )}
    </div>
  );
}
