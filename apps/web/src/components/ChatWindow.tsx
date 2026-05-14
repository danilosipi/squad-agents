import { getChatAttachmentUrl, type ChatAttachmentRow, type MessageRow } from "@/lib/api";
import { MessageBubble } from "./MessageBubble";

type Props = {
  title: string;
  messages: MessageRow[];
  loading?: boolean;
  attachments?: ChatAttachmentRow[];
};

export function ChatWindow({ title, messages, loading, attachments }: Props) {
  return (
    <div
      style={{
        flex: 1,
        minHeight: 0,
        display: "flex",
        flexDirection: "column",
        minWidth: 0,
        background: "var(--bg)",
      }}
    >
      <header
        style={{
          flexShrink: 0,
          padding: "12px 20px",
          borderBottom: "1px solid var(--border)",
          fontWeight: 600,
          fontSize: 15,
        }}
      >
        {title}
      </header>
      {attachments && attachments.length > 0 ? (
        <div
          style={{
            flexShrink: 0,
            padding: "8px 16px",
            borderBottom: "1px solid var(--border)",
            display: "flex",
            flexWrap: "wrap",
            gap: 8,
            alignItems: "center",
            fontSize: 12,
            color: "var(--muted)",
          }}
        >
          <span style={{ fontWeight: 600, color: "var(--text)" }}>Anexos:</span>
          {attachments.map((a) => (
            <a
              key={a.id}
              href={getChatAttachmentUrl(a.id)}
              target="_blank"
              rel="noopener noreferrer"
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: 4,
                padding: "4px 8px",
                borderRadius: 6,
                border: "1px solid var(--border)",
                background: "var(--sidebar)",
                color: "var(--accent)",
                textDecoration: "none",
                maxWidth: 200,
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap",
              }}
              title={a.file_name}
            >
              {/* eslint-disable-next-line @next/next/no-img-element -- preview via API local */}
              <img
                src={getChatAttachmentUrl(a.id)}
                alt=""
                width={28}
                height={28}
                style={{ objectFit: "cover", borderRadius: 4 }}
              />
              {a.file_name}
            </a>
          ))}
        </div>
      ) : null}
      <div
        style={{
          flex: 1,
          minHeight: 0,
          overflowY: "auto",
          overflowX: "hidden",
          padding: "20px 16px",
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
