import type { WidgetConfig } from "./types";

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export async function fetchConfig(widgetId: string): Promise<WidgetConfig> {
  const response = await fetch(`${API_BASE_URL}/widgets/${widgetId}/config`);
  if (!response.ok) throw new Error("Widget config is unavailable");
  return response.json();
}

export async function sendChat(message: string, conversationId: string, widgetId: string) {
  const response = await fetch(`${API_BASE_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ conversation_id: conversationId, message: `${message}\n\nwidget:${widgetId}` })
  });
  if (!response.ok) return { answer: "Chat requires login in the API right now.", tool_calls: [] };
  return response.json();
}
