"use client";

import { useRef, useState } from "react";

type Props = {
  onSend: (text: string) => void;
  disabled?: boolean;
  /** Anexar imagem (png/jpg/webp); envio separado do texto. */
  onAttachImage?: (file: File) => void;
  imageUploadBusy?: boolean;
};

export function MessageInput({ onSend, disabled, onAttachImage, imageUploadBusy }: Props) {
  const [value, setValue] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  function submit() {
    const t = value.trim();
    if (!t || disabled) return;
    onSend(t);
    setValue("");
  }

  return (
    <div
      style={{
        flexShrink: 0,
        padding: "12px 16px 16px",
        borderTop: "1px solid var(--border)",
        background: "var(--bg)",
        minWidth: 0,
      }}
    >
      <div
        style={{
          maxWidth: 800,
          margin: "0 auto",
          display: "flex",
          gap: 10,
          alignItems: "flex-end",
          minWidth: 0,
        }}
      >
        <input
          ref={fileRef}
          type="file"
          accept="image/png,image/jpeg,image/webp,.png,.jpg,.jpeg,.webp"
          style={{ display: "none" }}
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f && onAttachImage) {
              onAttachImage(f);
              e.target.value = "";
            }
          }}
        />
        {onAttachImage ? (
          <button
            type="button"
            title="Anexar imagem"
            disabled={disabled || imageUploadBusy}
            onClick={() => fileRef.current?.click()}
            style={{
              padding: "12px 14px",
              borderRadius: 12,
              border: "1px solid var(--border)",
              background: "var(--sidebar)",
              color: "var(--text)",
              fontWeight: 600,
              alignSelf: "stretch",
              minWidth: 44,
            }}
          >
            {imageUploadBusy ? "…" : "📎"}
          </button>
        ) : null}
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
