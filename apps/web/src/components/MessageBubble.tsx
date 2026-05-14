type Props = {
  role: string;
  content: string;
};

export function MessageBubble({ role, content }: Props) {
  const isUser = role === "user";
  return (
    <div
      style={{
        display: "flex",
        justifyContent: isUser ? "flex-end" : "flex-start",
        minWidth: 0,
      }}
    >
      <div
        style={{
          maxWidth: "min(720px, 92%)",
          minWidth: 0,
          padding: "10px 14px",
          borderRadius: 12,
          fontSize: 14,
          lineHeight: 1.5,
          whiteSpace: "pre-wrap",
          wordBreak: "break-word",
          overflowWrap: "anywhere",
          background: isUser ? "var(--user-bubble)" : "var(--assistant-bubble)",
          border: "1px solid var(--border)",
        }}
      >
        <div style={{ fontSize: 11, color: "var(--muted)", marginBottom: 4 }}>{role}</div>
        {content}
      </div>
    </div>
  );
}
