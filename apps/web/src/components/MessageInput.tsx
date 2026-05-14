"use client";

import { useState } from "react";

type Props = {
  onSend: (text: string) => void;
  disabled?: boolean;
};

export function MessageInput({ onSend, disabled }: Props) {
  const [value, setValue] = useState("");

  function submit() {
    const t = value.trim();
    if (!t || disabled) return;
    onSend(t);
    setValue("");
  }

  return (
    <div
      style={{
        position: "sticky",
        bottom: 0,
        left: 0,
        right: 0,
        padding: "12px 16px 16px",
        borderTop: "1px solid var(--border)",
        background: "linear-gradient(to top, var(--bg) 80%, transparent)",
      }}
    >
      <div
        style={{
          maxWidth: 800,
          margin: "0 auto",
          display: "flex",
          gap: 10,
          alignItems: "flex-end",
        }}
      >
        <textarea
          rows={2}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              submit();
            }
          }}
          placeholder="Mensagem… (Enter envia, Shift+Enter nova linha)"
          disabled={disabled}
          style={{
            flex: 1,
            resize: "none",
            padding: "12px 14px",
            borderRadius: 12,
            border: "1px solid var(--border)",
            background: "var(--sidebar)",
            minHeight: 48,
          }}
        />
        <button
          type="button"
          onClick={submit}
          disabled={disabled || !value.trim()}
          style={{
            padding: "12px 18px",
            borderRadius: 12,
            border: "none",
            background: "var(--accent)",
            color: "#fff",
            fontWeight: 600,
            alignSelf: "stretch",
          }}
        >
          Enviar
        </button>
      </div>
    </div>
  );
}
