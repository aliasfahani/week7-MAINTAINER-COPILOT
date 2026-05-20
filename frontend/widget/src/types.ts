export type Message = {
  role: "user" | "assistant";
  content: string;
};

export type WidgetConfig = {
  widget_id: string;
  greeting: string;
  theme: { primaryColor?: string };
  enabled_tools: string[];
};
