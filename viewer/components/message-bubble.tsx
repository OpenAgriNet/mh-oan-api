import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { cn } from "@/lib/utils";

interface MessageBubbleProps {
  role: "user" | "agent";
  content: string;
  contentEn?: string;  // English original (shown for Bhili conversations)
}

export function MessageBubble({ role, content, contentEn }: MessageBubbleProps) {
  const isUser = role === "user";

  return (
    <div
      className={cn("flex my-2", isUser ? "justify-start" : "justify-end")}
    >
      <div
        className={cn(
          "max-w-[85%] rounded-xl px-4 py-3 text-sm",
          isUser
            ? "bg-green-100 dark:bg-green-950/40 text-green-950 dark:text-green-100 rounded-bl-sm"
            : "bg-blue-100 dark:bg-blue-950/40 text-blue-950 dark:text-blue-100 rounded-br-sm"
        )}
      >
        <div className="text-xs font-medium mb-1 opacity-60">
          {isUser ? "Farmer" : "MahaVistaar"}
        </div>
        <div className="prose prose-sm dark:prose-invert max-w-none [&_p]:mb-1 [&_p:last-child]:mb-0">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
        </div>
        {contentEn && contentEn !== content && (
          <div className={cn(
            "mt-2 pt-2 border-t text-xs italic opacity-60",
            isUser
              ? "border-green-300 dark:border-green-800"
              : "border-blue-300 dark:border-blue-800"
          )}>
            <span className="italic font-medium opacity-80">EN:</span>
            {contentEn}
          </div>
        )}
      </div>
    </div>
  );
}

