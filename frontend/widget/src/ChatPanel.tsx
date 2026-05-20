import { useState } from "react";
import { sendChat } from "./api";
import type { Message, WidgetConfig } from "./types";

export function ChatPanel({ config, widgetId }: { config: WidgetConfig; widgetId: string }) {
  const [messages, setMessages] = useState<Message[]>([{ role: "assistant", content: config.greeting }]);
  const [input, setInput] = useState("");
  const conversationId = `widget-${widgetId}`;

  async function submit() {
    if (!input.trim()) return;
    const userMessage: Message = { role: "user", content: input };
    setMessages((current) => [...current, userMessage]);
    setInput("");
    const result = await sendChat(input, conversationId, widgetId);
    setMessages((current) => [...current, { role: "assistant", content: result.answer }]);
  }

  return (
    <section className="mc-panel">
      <div className="mc-header" style={{ background: config.theme.primaryColor || "#2563eb" }}>
        Maintainer's Copilot
      </div>
      <div className="mc-messages">
        {messages.map((message, index) => (
          <div key={index} className={`mc-message ${message.role}`}>{message.content}</div>
        ))}
      </div>
      <div className="mc-input">
        <input value={input} onChange={(event) => setInput(event.target.value)} onKeyDown={(event) => event.key === "Enter" && submit()} />
        <button onClick={submit}>Send</button>
      </div>
    </section>
  );
}
