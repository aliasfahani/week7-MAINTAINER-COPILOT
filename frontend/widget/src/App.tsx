import { useEffect, useState } from "react";
import { Bubble } from "./Bubble";
import { ChatPanel } from "./ChatPanel";
import { fetchConfig } from "./api";
import type { WidgetConfig } from "./types";
import "./style.css";

export function App() {
  const widgetId = new URLSearchParams(window.location.search).get("widget_id") || "demo-widget";
  const [open, setOpen] = useState(false);
  const [config, setConfig] = useState<WidgetConfig | null>(null);

  useEffect(() => {
    fetchConfig(widgetId)
      .then(setConfig)
      .catch(() => setConfig({ widget_id: widgetId, greeting: "Hi! How can I help?", theme: { primaryColor: "#2563eb" }, enabled_tools: [] }));
  }, [widgetId]);

  const color = config?.theme.primaryColor || "#2563eb";
  return open && config ? <ChatPanel config={config} widgetId={widgetId} /> : <Bubble onClick={() => setOpen(true)} color={color} />;
}
