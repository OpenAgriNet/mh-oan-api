"use client";

import dynamic from "next/dynamic";

const JsonView = dynamic(() => import("@microlink/react-json-view"), {
  ssr: false,
  loading: () => (
    <div className="text-muted-foreground text-sm p-4">Loading JSON viewer...</div>
  ),
});

interface RawJsonViewerProps {
  data: unknown;
  name?: string;
}

export function RawJsonViewer({ data, name }: RawJsonViewerProps) {
  return (
    <div className="overflow-auto max-h-[70vh] p-4 bg-card rounded-lg border">
      <JsonView
        src={typeof data === "string" ? JSON.parse(data) : data}
        name={name ?? "root"}
        collapsed={2}
        enableClipboard
        displayDataTypes={false}
        style={{ fontSize: "13px" }}
      />
    </div>
  );
}
