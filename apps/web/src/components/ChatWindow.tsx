import type { MessageRow } from "@/lib/api";
import { MessageBubble } from "./MessageBubble";

type Props = {
  title: string;
  messages: MessageRow[];
  loading?: boolean;
};

export function ChatWindow({ title, messages, loading }: Props) {
  return (
    <div
      style={{
        flex: 1,
        display: "flex",
        flexDirection: "column",
        minWidth: 0,
        background: "var(--bg)",
      }}
    >
      <header
        style={{
          padding: "12px 20px",
          borderBottom: "1px solid var(--border)",
          fontWeight: 600,
          fontSize: 15,
        }}
      >
        {title}
      </header>
      <div
        style={{
          flex: 1,
          overflowY: "auto",
          padding: "20px 16px 120px",
          display: "flex",
          flexDirection: "column",
          gap: 12,
        }}
      >
        {loading && <p style={{ color: "var(--muted)", fontSize: 13 }}>Carregando…</p>}
        {!loading && messages.length === 0 && (
          <p style={{ color: "var(--muted)", fontSize: 14 }}>Sem mensagens. Envie algo abaixo.</p>
        )}
        {messages.map((m) => (
          <MessageBubble key={m.id} role={m.role} content={m.content} />
        ))}
      </div>
    </div>
  );
}
