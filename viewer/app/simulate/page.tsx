"use client";

import { useRef, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ThemeToggle } from "@/components/theme-toggle";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  ArrowLeft,
  Loader2,
  Play,
  Square,
  User,
  MapPin,
  Sprout,
  Wrench,
  CheckCircle2,
  XCircle,
} from "lucide-react";
import type { FarmerProfile, ConversationEnv } from "@/lib/types";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface StreamItem {
  kind: "user" | "agent" | "typing" | "language_switch";
  turn_number: number;
  text: string;
  tool_calls?: { tool_name: string; args: string }[];
}

type SimStatus = "idle" | "running" | "done" | "error";

export default function SimulatePage() {
  const [maxTurns, setMaxTurns] = useState("25");
  const [language, setLanguage] = useState("any");
  const [targetLanguage, setTargetLanguage] = useState("any");
  const [customScenario, setCustomScenario] = useState("");
  const [forceLanguageSwitch, setForceLanguageSwitch] = useState(false);
  const [status, setStatus] = useState<SimStatus>("idle");
  const [env, setEnv] = useState<ConversationEnv | null>(null);
  const [profile, setProfile] = useState<FarmerProfile | null>(null);
  const [items, setItems] = useState<StreamItem[]>([]);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [savedFile, setSavedFile] = useState<string | null>(null);
  const [savedSessionId, setSavedSessionId] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  const autoScroll = () => {
    setTimeout(() => {
      scrollRef.current?.scrollTo({
        top: scrollRef.current.scrollHeight,
        behavior: "smooth",
      });
    }, 50);
  };

  const turnCount = () => {
    const turns = new Set(items.map((i) => i.turn_number));
    return turns.size;
  };

  const startSimulation = async () => {
    setStatus("running");
    setEnv(null);
    setProfile(null);
    setItems([]);
    setErrorMsg(null);
    setSavedFile(null);
    setSavedSessionId(null);

    const controller = new AbortController();
    abortRef.current = controller;

    try {
      const body: Record<string, unknown> = {
        max_turns: parseInt(maxTurns),
      };
      if (language !== "any") body.language = language;
      if (targetLanguage !== "any") body.target_language = targetLanguage;
      if (customScenario.trim()) body.custom_scenario = customScenario.trim();
      if (forceLanguageSwitch) body.force_language_switch = true;

      const response = await fetch("http://localhost:8000/api/simulate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
        signal: controller.signal,
      });

      if (!response.ok || !response.body) {
        throw new Error(`HTTP ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() ?? "";

        let eventType = "";
        for (const line of lines) {
          if (line.startsWith("event: ")) {
            eventType = line.slice(7).trim();
          } else if (line.startsWith("data: ") && eventType) {
            const data = JSON.parse(line.slice(6));
            handleEvent(eventType, data);
            eventType = "";
          }
        }
      }
    } catch (err: unknown) {
      if (err instanceof Error && err.name === "AbortError") {
        setStatus("idle");
      } else {
        setErrorMsg(err instanceof Error ? err.message : String(err));
        setStatus("error");
      }
    }
  };

  const handleEvent = (event: string, data: unknown) => {
    switch (event) {
      case "env":
        setEnv(data as ConversationEnv);
        break;
      case "profile":
        setProfile(data as FarmerProfile);
        break;
      case "language_switch": {
        const d = data as { turn_number: number; from_lang: string; to_lang: string };
        setItems((prev) => [
          ...prev,
          {
            kind: "language_switch",
            turn_number: d.turn_number,
            text: `Language switched: ${d.from_lang} → ${d.to_lang}`,
          },
        ]);
        autoScroll();
        break;
      }
      case "user_message": {
        const d = data as { turn_number: number; text: string; is_end: boolean };
        setItems((prev) => prev.filter((i) => i.kind !== "typing"));
        setItems((prev) => [
          ...prev,
          { kind: "user", turn_number: d.turn_number, text: d.text },
        ]);
        if (!d.is_end) {
          setItems((prev) => [
            ...prev,
            { kind: "typing", turn_number: d.turn_number, text: "" },
          ]);
        }
        autoScroll();
        break;
      }
      case "agent_message": {
        const d = data as {
          turn_number: number;
          text: string;
          tool_calls: { tool_name: string; args: string }[];
        };
        setItems((prev) => prev.filter((i) => i.kind !== "typing"));
        setItems((prev) => [
          ...prev,
          {
            kind: "agent",
            turn_number: d.turn_number,
            text: d.text,
            tool_calls: d.tool_calls,
          },
        ]);
        autoScroll();
        break;
      }
      case "done": {
        const d = data as { record: { session_id: string }; file: string };
        setItems((prev) => prev.filter((i) => i.kind !== "typing"));
        setSavedFile(d.file);
        setSavedSessionId(d.record.session_id);
        setStatus("done");
        break;
      }
      case "error":
        setItems((prev) => prev.filter((i) => i.kind !== "typing"));
        setErrorMsg((data as { message: string }).message);
        setStatus("error");
        break;
    }
  };

  const stopSimulation = () => {
    abortRef.current?.abort();
    abortRef.current = null;
    setStatus("idle");
  };

  const renderItems = () => {
    const elements: React.ReactNode[] = [];
    let lastTurn = 0;

    for (let i = 0; i < items.length; i++) {
      const item = items[i];

      if (item.turn_number > lastTurn) {
        lastTurn = item.turn_number;
        elements.push(
          <div key={`sep-${item.turn_number}`} className="flex items-center gap-3 py-2">
            <div className="flex-1 h-px bg-border" />
            <span className="text-xs font-medium text-muted-foreground px-2">
              Turn {item.turn_number}
            </span>
            <div className="flex-1 h-px bg-border" />
          </div>
        );
      }

      if (item.kind === "user") {
        elements.push(
          <div key={`user-${i}`} className="flex justify-start my-2">
            <div className="max-w-[85%] rounded-xl rounded-bl-sm px-4 py-3 text-sm bg-green-100 dark:bg-green-950/40 text-green-950 dark:text-green-100">
              <div className="text-xs font-medium mb-1 opacity-60">Farmer</div>
              <div className="prose prose-sm dark:prose-invert max-w-none [&_p]:mb-1 [&_p:last-child]:mb-0">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {item.text}
                </ReactMarkdown>
              </div>
            </div>
          </div>
        );
      } else if (item.kind === "agent") {
        if (item.tool_calls && item.tool_calls.length > 0) {
          elements.push(
            <div key={`tools-${i}`} className="flex flex-wrap gap-1.5 my-2 justify-end">
              {item.tool_calls.map((tc, j) => (
                <Badge
                  key={j}
                  className="bg-purple-100 text-purple-800 border-purple-300 dark:bg-purple-900 dark:text-purple-200 dark:border-purple-700 text-xs"
                >
                  <Wrench className="size-3 mr-1" />
                  {tc.tool_name}
                </Badge>
              ))}
            </div>
          );
        }
        elements.push(
          <div key={`agent-${i}`} className="flex justify-end my-2">
            <div className="max-w-[85%] rounded-xl rounded-br-sm px-4 py-3 text-sm bg-blue-100 dark:bg-blue-950/40 text-blue-950 dark:text-blue-100">
              <div className="text-xs font-medium mb-1 opacity-60">MahaVistaar</div>
              <div className="prose prose-sm dark:prose-invert max-w-none [&_p]:mb-1 [&_p:last-child]:mb-0">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {item.text}
                </ReactMarkdown>
              </div>
            </div>
          </div>
        );
      } else if (item.kind === "language_switch") {
        elements.push(
          <div key={`lang-switch-${i}`} className="flex items-center justify-center gap-2 py-2">
            <Badge className="bg-orange-100 text-orange-800 border-orange-300 dark:bg-orange-900/40 dark:text-orange-200 dark:border-orange-700 text-xs">
              {item.text}
            </Badge>
          </div>
        );
      } else if (item.kind === "typing") {
        elements.push(
          <div key={`typing-${i}`} className="flex justify-end my-2">
            <div className="rounded-xl rounded-br-sm px-4 py-3 text-sm bg-blue-100 dark:bg-blue-950/40 text-blue-400 dark:text-blue-500 flex items-center gap-2">
              <Loader2 className="size-3.5 animate-spin" />
              <span className="text-xs">MahaVistaar is thinking...</span>
            </div>
          </div>
        );
      }
    }

    return elements;
  };

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
            <h1 className="text-lg font-semibold">Real-time Simulation</h1>
          </div>
          <ThemeToggle />
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-6 space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Configuration</CardTitle>
            <CardDescription>
              Configure and start a new farmer-agent conversation simulation
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap items-end gap-4">
              <div>
                <label className="text-xs font-medium text-muted-foreground mb-1 block">
                  Max Turns
                </label>
                <Select
                  value={maxTurns}
                  onValueChange={setMaxTurns}
                  disabled={status === "running"}
                >
                  <SelectTrigger className="w-[100px]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {[5, 10, 15, 20, 25].map((n) => (
                      <SelectItem key={n} value={String(n)}>
                        {n}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <label className="text-xs font-medium text-muted-foreground mb-1 block">
                  User Language
                </label>
                <Select
                  value={language}
                  onValueChange={setLanguage}
                  disabled={status === "running"}
                >
                  <SelectTrigger className="w-[140px]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="any">Random</SelectItem>
                    <SelectItem value="mr">Marathi</SelectItem>
                    <SelectItem value="en">English</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <label className="text-xs font-medium text-muted-foreground mb-1 block">
                  Target Language
                </label>
                <Select
                  value={targetLanguage}
                  onValueChange={setTargetLanguage}
                  disabled={status === "running"}
                >
                  <SelectTrigger className="w-[140px]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="any">Random</SelectItem>
                    <SelectItem value="mr">Marathi</SelectItem>
                    <SelectItem value="en">English</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="flex-1 min-w-[200px]">
                <label className="text-xs font-medium text-muted-foreground mb-1 block">
                  Custom Scenario (optional)
                </label>
                <textarea
                  value={customScenario}
                  onChange={(e) => setCustomScenario(e.target.value)}
                  disabled={status === "running"}
                  placeholder="e.g. Ask about mandi prices for onion near Nashik"
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:opacity-50 resize-none h-[38px]"
                />
              </div>

              <label className="flex items-center gap-2 text-sm cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={forceLanguageSwitch}
                  onChange={(e) => setForceLanguageSwitch(e.target.checked)}
                  disabled={status === "running"}
                  className="rounded border-input"
                />
                <span className="text-muted-foreground">Force Lang Switch</span>
              </label>

              {status === "running" ? (
                <Button variant="destructive" onClick={stopSimulation}>
                  <Square className="size-3.5" />
                  Stop
                </Button>
              ) : (
                <Button onClick={startSimulation}>
                  <Play className="size-3.5" />
                  Start Simulation
                </Button>
              )}

              {status === "running" && (
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Loader2 className="size-4 animate-spin" />
                  Running... ({turnCount()} turns)
                </div>
              )}

              {status === "done" && savedFile && savedSessionId && (
                <Link
                  href={`/conversation/${savedSessionId}`}
                >
                  <Button variant="outline" size="sm">
                    <CheckCircle2 className="size-3.5" />
                    View Full Conversation
                  </Button>
                </Link>
              )}
            </div>
          </CardContent>
        </Card>

        {profile && (
          <Card>
            <CardContent className="pt-6">
              <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-sm">
                <div className="flex items-center gap-2">
                  <User className="size-4 text-muted-foreground" />
                  <span className="font-medium">{profile.name}</span>
                  <Badge variant="secondary">{profile.mood}</Badge>
                </div>
                <div className="flex items-center gap-2 text-muted-foreground">
                  <MapPin className="size-4" />
                  {profile.village}, {profile.taluka}, {profile.district}
                </div>
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Sprout className="size-4" />
                  {profile.crops.join(", ")} ({profile.land_acres} acres)
                </div>
                <Badge variant="outline">{profile.scenario.id}</Badge>
                {profile.has_agristack && (
                  <Badge className="bg-emerald-100 text-emerald-800 border-emerald-300 dark:bg-emerald-900/40 dark:text-emerald-200 dark:border-emerald-700 text-xs">
                    Agristack
                  </Badge>
                )}
                {profile.is_pocra && (
                  <Badge className="bg-teal-100 text-teal-800 border-teal-300 dark:bg-teal-900/40 dark:text-teal-200 dark:border-teal-700 text-xs">
                    PoCRA
                  </Badge>
                )}
              </div>
              <div className="flex flex-wrap items-center gap-2 mt-2">
                <Badge className="bg-amber-100 text-amber-800 border-amber-300 dark:bg-amber-900/40 dark:text-amber-200 dark:border-amber-700">
                  User: {profile.language}
                </Badge>
                {env && (
                  <Badge className="bg-sky-100 text-sky-800 border-sky-300 dark:bg-sky-900/40 dark:text-sky-200 dark:border-sky-700">
                    Target: {env.target_language}
                  </Badge>
                )}
                <Badge className="bg-violet-100 text-violet-800 border-violet-300 dark:bg-violet-900/40 dark:text-violet-200 dark:border-violet-700">
                  Verbosity: {profile.verbosity}
                </Badge>
                {env && (
                  <span className="text-xs text-muted-foreground ml-1">
                    Model: {env.agrinet_model}
                  </span>
                )}
              </div>
              <p className="text-sm text-muted-foreground mt-2">
                {profile.scenario.description}
              </p>
            </CardContent>
          </Card>
        )}

        {errorMsg && (
          <div className="bg-destructive/10 text-destructive rounded-md px-4 py-3 text-sm flex items-start gap-2">
            <XCircle className="size-4 mt-0.5 shrink-0" />
            <pre className="whitespace-pre-wrap font-mono text-xs max-h-48 overflow-y-auto">
              {errorMsg}
            </pre>
          </div>
        )}

        {items.length > 0 && (
          <div
            ref={scrollRef}
            className="space-y-1 max-h-[65vh] overflow-y-auto pr-2"
          >
            {renderItems()}

            {status === "done" && (
              <div className="flex items-center justify-center gap-2 py-4 text-sm text-green-700 dark:text-green-400">
                <CheckCircle2 className="size-4" />
                Simulation complete — {turnCount()} turns, saved to {savedFile}
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
