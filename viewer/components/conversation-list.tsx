"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import type { ConversationSummary } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Trash2,
  ChevronUp,
  ChevronDown,
  ChevronsUpDown,
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
} from "lucide-react";

const LANG_LABELS: Record<string, string> = {
  mr: "Marathi",
  hi: "Hindi",
  en: "English",
  bhb: "Bhili",
};

const PAGE_SIZES = [25, 50, 100];

type SortKey =
  | "name"
  | "scenario_id"
  | "scenario_category"
  | "location"
  | "language"
  | "target_language"
  | "turn_count"
  | "completed"
  | "mood"
  | "verbosity"
  | "modified";

type SortDir = "asc" | "desc";

interface ConversationListProps {
  conversations: ConversationSummary[];
  onDelete?: (sessionId: string) => void;
}

export function ConversationList({
  conversations,
  onDelete,
}: ConversationListProps) {
  const router = useRouter();
  const [deleting, setDeleting] = useState<string | null>(null);

  const [sortKey, setSortKey] = useState<SortKey>("modified");
  const [sortDir, setSortDir] = useState<SortDir>("desc");

  const [filterLang, setFilterLang] = useState<string>("all");
  const [filterStatus, setFilterStatus] = useState<string>("all");
  const [filterCategory, setFilterCategory] = useState<string>("all");

  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(25);

  const allLanguages = useMemo(() => {
    const langs = new Set<string>();
    conversations.forEach((c) => {
      if (c.target_language) langs.add(c.target_language);
    });
    return Array.from(langs).sort();
  }, [conversations]);

  const allCategories = useMemo(() => {
    const cats = new Set<string>();
    conversations.forEach((c) => {
      if (c.scenario_category) cats.add(c.scenario_category);
    });
    return Array.from(cats).sort();
  }, [conversations]);

  const filtered = useMemo(() => {
    return conversations.filter((c) => {
      if (filterLang !== "all" && c.target_language !== filterLang) return false;
      if (filterStatus === "completed" && !c.completed) return false;
      if (filterStatus === "incomplete" && c.completed) return false;
      if (filterStatus === "error" && !c.has_error) return false;
      if (
        filterCategory !== "all" &&
        c.scenario_category !== filterCategory
      )
        return false;
      return true;
    });
  }, [conversations, filterLang, filterStatus, filterCategory]);

  const sorted = useMemo(() => {
    const arr = [...filtered];
    arr.sort((a, b) => {
      let aVal: string | number | boolean = "";
      let bVal: string | number | boolean = "";

      switch (sortKey) {
        case "name":
          aVal = a.name.toLowerCase();
          bVal = b.name.toLowerCase();
          break;
        case "scenario_id":
          aVal = a.scenario_id;
          bVal = b.scenario_id;
          break;
        case "scenario_category":
          aVal = a.scenario_category;
          bVal = b.scenario_category;
          break;
        case "location":
          aVal = a.location;
          bVal = b.location;
          break;
        case "language":
          aVal = a.language;
          bVal = b.language;
          break;
        case "target_language":
          aVal = a.target_language;
          bVal = b.target_language;
          break;
        case "turn_count":
          aVal = a.turn_count;
          bVal = b.turn_count;
          break;
        case "completed":
          aVal = a.has_error ? 2 : a.completed ? 0 : 1;
          bVal = b.has_error ? 2 : b.completed ? 0 : 1;
          break;
        case "mood":
          aVal = a.mood ?? "";
          bVal = b.mood ?? "";
          break;
        case "verbosity":
          aVal = a.verbosity ?? "";
          bVal = b.verbosity ?? "";
          break;
        case "modified":
          aVal = a.modified ?? 0;
          bVal = b.modified ?? 0;
          break;
      }

      if (aVal < bVal) return sortDir === "asc" ? -1 : 1;
      if (aVal > bVal) return sortDir === "asc" ? 1 : -1;
      return 0;
    });
    return arr;
  }, [filtered, sortKey, sortDir]);

  const totalPages = Math.max(1, Math.ceil(sorted.length / pageSize));
  const safePage = Math.min(page, totalPages - 1);
  const pageData = sorted.slice(
    safePage * pageSize,
    safePage * pageSize + pageSize
  );

  const setFilterAndResetPage = (
    setter: (v: string) => void,
    value: string
  ) => {
    setter(value);
    setPage(0);
  };

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir("asc");
    }
  };

  const handleDelete = async (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation();
    if (!confirm("Delete this conversation?")) return;
    setDeleting(sessionId);
    try {
      const res = await fetch(`/api/conversation/${sessionId}`, {
        method: "DELETE",
      });
      if (res.ok) {
        onDelete?.(sessionId);
      }
    } finally {
      setDeleting(null);
    }
  };

  const SortIcon = ({ col }: { col: SortKey }) => {
    if (sortKey !== col)
      return <ChevronsUpDown className="size-3 opacity-30" />;
    return sortDir === "asc" ? (
      <ChevronUp className="size-3" />
    ) : (
      <ChevronDown className="size-3" />
    );
  };

  const SortableHead = ({
    col,
    children,
    className,
  }: {
    col: SortKey;
    children: React.ReactNode;
    className?: string;
  }) => (
    <TableHead
      className={`cursor-pointer select-none hover:bg-muted/50 ${className ?? ""}`}
      onClick={() => handleSort(col)}
    >
      <span className="inline-flex items-center gap-1">
        {children}
        <SortIcon col={col} />
      </span>
    </TableHead>
  );

  if (conversations.length === 0) {
    return (
      <p className="text-muted-foreground text-sm py-8 text-center">
        No conversations found.
      </p>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground">Language</span>
          <Select
            value={filterLang}
            onValueChange={(v) => setFilterAndResetPage(setFilterLang, v)}
          >
            <SelectTrigger className="w-[130px] h-8 text-xs">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All</SelectItem>
              {allLanguages.map((l) => (
                <SelectItem key={l} value={l}>
                  {LANG_LABELS[l] ?? l}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground">Status</span>
          <Select
            value={filterStatus}
            onValueChange={(v) => setFilterAndResetPage(setFilterStatus, v)}
          >
            <SelectTrigger className="w-[130px] h-8 text-xs">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All</SelectItem>
              <SelectItem value="completed">Completed</SelectItem>
              <SelectItem value="incomplete">Incomplete</SelectItem>
              <SelectItem value="error">Error</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground">Category</span>
          <Select
            value={filterCategory}
            onValueChange={(v) => setFilterAndResetPage(setFilterCategory, v)}
          >
            <SelectTrigger className="w-[150px] h-8 text-xs">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All</SelectItem>
              {allCategories.map((c) => (
                <SelectItem key={c} value={c}>
                  {c}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {(filterLang !== "all" ||
          filterStatus !== "all" ||
          filterCategory !== "all") && (
          <Button
            variant="ghost"
            size="sm"
            className="h-8 text-xs"
            onClick={() => {
              setFilterLang("all");
              setFilterStatus("all");
              setFilterCategory("all");
              setPage(0);
            }}
          >
            Clear filters
          </Button>
        )}

        <span className="text-xs text-muted-foreground ml-auto">
          {filtered.length === conversations.length
            ? `${conversations.length} conversations`
            : `${filtered.length} of ${conversations.length} conversations`}
        </span>
      </div>

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <SortableHead col="name">Name</SortableHead>
              <SortableHead col="scenario_id">Scenario</SortableHead>
              <SortableHead col="scenario_category">Category</SortableHead>
              <SortableHead col="location">Location</SortableHead>
              <SortableHead col="language">User Lang</SortableHead>
              <SortableHead col="target_language">Target Lang</SortableHead>
              <SortableHead col="mood">Mood</SortableHead>
              <SortableHead col="verbosity">Verbosity</SortableHead>
              <SortableHead col="turn_count" className="text-center">
                Turns
              </SortableHead>
              <SortableHead col="completed">Status</SortableHead>
              <SortableHead col="modified">Created</SortableHead>
              <TableHead></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {pageData.map((c) => (
              <TableRow
                key={c.session_id}
                className="cursor-pointer"
                onClick={() => router.push(`/conversation/${c.session_id}`)}
              >
                <TableCell className="font-medium">{c.name}</TableCell>
                <TableCell className="font-mono text-xs">
                  {c.scenario_id}
                </TableCell>
                <TableCell>
                  <Badge variant="secondary">{c.scenario_category}</Badge>
                </TableCell>
                <TableCell className="text-sm">{c.location}</TableCell>
                <TableCell>{LANG_LABELS[c.language] ?? c.language}</TableCell>
                <TableCell>
                  {LANG_LABELS[c.target_language] ?? c.target_language}
                </TableCell>
                <TableCell>
                  <MoodBadge mood={c.mood} />
                </TableCell>
                <TableCell className="text-xs capitalize">
                  {c.verbosity ?? "\u2014"}
                </TableCell>
                <TableCell className="text-center">{c.turn_count}</TableCell>
                <TableCell>
                  <StatusBadge
                    completed={c.completed}
                    hasError={c.has_error}
                  />
                </TableCell>
                <TableCell className="text-xs text-muted-foreground whitespace-nowrap">
                  {c.modified
                    ? new Date(c.modified * 1000).toLocaleString(undefined, {
                        month: "short",
                        day: "numeric",
                        hour: "2-digit",
                        minute: "2-digit",
                      })
                    : "\u2014"}
                </TableCell>
                <TableCell>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="size-8 text-muted-foreground hover:text-destructive"
                    disabled={deleting === c.session_id}
                    onClick={(e) => handleDelete(e, c.session_id)}
                  >
                    <Trash2 className="size-3.5" />
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground">Rows per page</span>
          <Select
            value={String(pageSize)}
            onValueChange={(v) => {
              setPageSize(Number(v));
              setPage(0);
            }}
          >
            <SelectTrigger className="w-[70px] h-8 text-xs">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {PAGE_SIZES.map((s) => (
                <SelectItem key={s} value={String(s)}>
                  {s}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="flex items-center gap-1">
          <span className="text-xs text-muted-foreground mr-2">
            Page {safePage + 1} of {totalPages}
          </span>
          <Button
            variant="outline"
            size="icon"
            className="size-8"
            disabled={safePage === 0}
            onClick={() => setPage(0)}
          >
            <ChevronsLeft className="size-3.5" />
          </Button>
          <Button
            variant="outline"
            size="icon"
            className="size-8"
            disabled={safePage === 0}
            onClick={() => setPage((p) => Math.max(0, p - 1))}
          >
            <ChevronLeft className="size-3.5" />
          </Button>
          <Button
            variant="outline"
            size="icon"
            className="size-8"
            disabled={safePage >= totalPages - 1}
            onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
          >
            <ChevronRight className="size-3.5" />
          </Button>
          <Button
            variant="outline"
            size="icon"
            className="size-8"
            disabled={safePage >= totalPages - 1}
            onClick={() => setPage(totalPages - 1)}
          >
            <ChevronsRight className="size-3.5" />
          </Button>
        </div>
      </div>
    </div>
  );
}

function StatusBadge({
  completed,
  hasError,
}: {
  completed: boolean;
  hasError: boolean;
}) {
  if (hasError) {
    return (
      <Badge className="bg-red-100 text-red-800 border-red-200 dark:bg-red-950 dark:text-red-300 dark:border-red-800">
        Error
      </Badge>
    );
  }
  if (completed) {
    return (
      <Badge className="bg-green-100 text-green-800 border-green-200 dark:bg-green-950 dark:text-green-300 dark:border-green-800">
        Completed
      </Badge>
    );
  }
  return (
    <Badge className="bg-yellow-100 text-yellow-800 border-yellow-200 dark:bg-yellow-950 dark:text-yellow-300 dark:border-yellow-800">
      Incomplete
    </Badge>
  );
}

function MoodBadge({ mood }: { mood?: string }) {
  if (!mood) return <span className="text-xs text-muted-foreground">{"\u2014"}</span>;
  const styles: Record<string, string> = {
    normal: "bg-blue-100 text-blue-800 border-blue-200 dark:bg-blue-950 dark:text-blue-300 dark:border-blue-800",
    frustrated: "bg-orange-100 text-orange-800 border-orange-200 dark:bg-orange-950 dark:text-orange-300 dark:border-orange-800",
    adversarial: "bg-red-100 text-red-800 border-red-200 dark:bg-red-950 dark:text-red-300 dark:border-red-800",
  };
  return (
    <Badge className={`text-xs ${styles[mood] ?? ""}`}>
      {mood}
    </Badge>
  );
}
