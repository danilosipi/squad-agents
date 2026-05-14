import type { ChatRow } from "@/lib/api";

type Props = {
  chats: ChatRow[];
  selectedChatId: number | null;
  onSelect: (id: number) => void;
  onNewChat: () => void;
  disabled?: boolean;
};

export function ChatList({ chats, selectedChatId, onSelect, onNewChat, disabled }: Props) {
  return (
    <div
      style={{
        width: 220,
        minWidth: 220,
        background: "var(--sidebar)",
        borderRight: "1px solid var(--border)",
        display: "flex",
        flexDirection: "column",
        height: "100%",
      }}
    >
      <div
        style={{
          padding: 12,
          borderBottom: "1px solid var(--border)",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 8,
        }}
      >
        <span style={{ fontSize: 12, color: "var(--muted)" }}>Chats</span>
        <button
          type="button"
          onClick={onNewChat}
          disabled={disabled}
          style={{
            padding: "4px 10px",
            borderRadius: 6,
            border: "none",
            background: "var(--accent)",
            color: "#fff",
            fontSize: 12,
          }}
        >
          + Novo
        </button>
      </div>
      <div style={{ flex: 1, overflowY: "auto", padding: 8 }}>
        {chats.length === 0 && (
          <p style={{ fontSize: 13, color: "var(--muted)", margin: 8 }}>Nenhum chat.</p>
        )}
        <ul style={{ listStyle: "none", margin: 0, padding: 0 }}>
          {chats.map((c) => {
            const active = c.id === selectedChatId;
            return (
              <li key={c.id} style={{ marginBottom: 4 }}>
                <button
                  type="button"
                  onClick={() => onSelect(c.id)}
                  style={{
                    width: "100%",
                    textAlign: "left",
                    padding: "8px 10px",
                    borderRadius: 8,
                    border: "none",
                    background: active ? "var(--user-bubble)" : "transparent",
                    color: "var(--text)",
                    fontSize: 13,
                  }}
                >
                  {c.title}
                </button>
              </li>
            );
          })}
        </ul>
      </div>
    </div>
  );
}
