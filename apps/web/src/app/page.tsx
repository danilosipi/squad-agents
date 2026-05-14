"use client";

import { useCallback, useEffect, useState } from "react";
import { ChatList } from "@/components/ChatList";
import { ChatWindow } from "@/components/ChatWindow";
import { MessageInput } from "@/components/MessageInput";
import { ProjectSidebar } from "@/components/ProjectSidebar";
import {
  FAKE_ASSISTANT_REPLY,
  createChat,
  createProject,
  executeSquad,
  fetchChats,
  fetchMessages,
  fetchPendingSquadRun,
  fetchProjects,
  registerProject,
  sendMessage,
  sendMessageWithMetaOrchestrator,
  type ChatRow,
  type MessageRow,
  type PendingSquadRun,
  type ProjectRow,
} from "@/lib/api";

const USE_FAKE_ASSISTANT =
  typeof process !== "undefined" && process.env.NEXT_PUBLIC_USE_FAKE_ASSISTANT === "true";

export default function HomePage() {
  const [projects, setProjects] = useState<ProjectRow[]>([]);
  const [selectedSlug, setSelectedSlug] = useState<string | null>(null);
  const [chats, setChats] = useState<ChatRow[]>([]);
  const [selectedChatId, setSelectedChatId] = useState<number | null>(null);
  const [messages, setMessages] = useState<MessageRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [messagesLoading, setMessagesLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [squadExecuting, setSquadExecuting] = useState(false);
  const [pendingRun, setPendingRun] = useState<PendingSquadRun | null>(null);
  const [error, setError] = useState<string | null>(null);

  const selectedProject = projects.find((p) => p.slug === selectedSlug);
  const selectedChat = chats.find((c) => c.id === selectedChatId);

  const refreshProjects = useCallback(async () => {
    setError(null);
    const list = await fetchProjects();
    setProjects(list);
    return list;
  }, []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const list = await fetchProjects();
        if (!cancelled) setProjects(list);
      } catch (e) {
        if (!cancelled)
          setError(e instanceof Error ? e.message : "Falha ao carregar projetos");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const loadChats = useCallback(async (slug: string) => {
    setError(null);
    const list = await fetchChats(slug);
    setChats(list);
    return list;
  }, []);

  const loadMessages = useCallback(async (chatId: number) => {
    setError(null);
    const list = await fetchMessages(chatId);
    setMessages(list);
  }, []);

  const onSelectProject = useCallback(
    async (slug: string) => {
      setSelectedSlug(slug);
      setSelectedChatId(null);
      setMessages([]);
      setPendingRun(null);
      try {
        await loadChats(slug);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Falha ao carregar chats");
      }
    },
    [loadChats],
  );

  const onSelectChat = useCallback(
    async (id: number) => {
      setSelectedChatId(id);
      setMessages([]);
      setPendingRun(null);
      setMessagesLoading(true);
      try {
        await loadMessages(id);
        if (!USE_FAKE_ASSISTANT && selectedSlug === "cap") {
          try {
            setPendingRun(await fetchPendingSquadRun(id));
          } catch {
            setPendingRun(null);
          }
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : "Falha ao carregar mensagens");
      } finally {
        setMessagesLoading(false);
      }
    },
    [loadMessages, selectedSlug],
  );

  const onCreateProject = useCallback(async () => {
    const name = window.prompt("Nome do novo projeto?");
    if (!name?.trim()) return;
    try {
      setLoading(true);
      const row = await createProject(name.trim());
      await refreshProjects();
      await onSelectProject(row.slug);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao criar projeto");
    } finally {
      setLoading(false);
    }
  }, [onSelectProject, refreshProjects]);

  const onRegisterProject = useCallback(async () => {
    const name = window.prompt("Nome exibido do projeto?");
    if (!name?.trim()) return;
    const path = window.prompt("Caminho absoluto da pasta do projeto?");
    if (!path?.trim()) return;
    try {
      setLoading(true);
      const row = await registerProject(name.trim(), path.trim());
      await refreshProjects();
      await onSelectProject(row.slug);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao registrar projeto");
    } finally {
      setLoading(false);
    }
  }, [onSelectProject, refreshProjects]);

  const onNewChat = useCallback(async () => {
    if (!selectedSlug) return;
    const title = window.prompt("Título do chat?");
    if (!title?.trim()) return;
    try {
      const row = await createChat(selectedSlug, title.trim());
      await loadChats(selectedSlug);
      await onSelectChat(row.id);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao criar chat");
    }
  }, [loadChats, onSelectChat, selectedSlug]);

  const onSendMessage = useCallback(
    async (text: string) => {
      if (!selectedChatId) return;
      setSending(true);
      setError(null);
      try {
        if (USE_FAKE_ASSISTANT) {
          await sendMessage(selectedChatId, "user", text);
          await sendMessage(selectedChatId, "assistant", FAKE_ASSISTANT_REPLY);
        } else {
          const result = await sendMessageWithMetaOrchestrator(selectedChatId, text);
          if (result.status === "failed") {
            setError(
              "O meta-orquestrador retornou erro. Os detalhes estão na última mensagem do assistente.",
            );
          }
        }
        const list = await fetchMessages(selectedChatId);
        setMessages(list);
        if (!USE_FAKE_ASSISTANT && selectedSlug === "cap") {
          try {
            setPendingRun(await fetchPendingSquadRun(selectedChatId));
          } catch {
            setPendingRun(null);
          }
        }
      } catch (e) {
        const msg = e instanceof Error ? e.message : "Erro ao enviar mensagem";
        if (
          msg.includes("contexto mínimo") ||
          msg.includes(".squad") ||
          msg.includes("context.md")
        ) {
          setError(
            "Este projeto ainda não possui contexto mínimo. Preencha .squad/context.md antes de executar a squad.",
          );
        } else {
          setError(msg);
        }
      } finally {
        setSending(false);
      }
    },
    [selectedChatId, selectedSlug],
  );

  const onExecuteSquad = useCallback(async () => {
    if (!selectedChatId || !pendingRun) return;
    setSquadExecuting(true);
    setError(null);
    try {
      const r = await executeSquad(pendingRun.run_id, selectedChatId);
      if (r.status === "blocked") {
        const hint =
          selectedProject?.local_path != null && selectedProject.local_path.length > 0
            ? `${selectedProject.local_path.replace(/[/\\]+$/, "")}\\.squad\\context.md`
            : "";
        setError(
          "Este projeto ainda não possui contexto mínimo. Preencha .squad/context.md antes de executar a squad." +
            (hint ? ` Arquivo esperado: ${hint}` : ""),
        );
      } else if (r.status === "failed") {
        setError(
          "A squad completa retornou erro. Os detalhes estão na última mensagem do assistente.",
        );
      }
      await loadMessages(selectedChatId);
      if (selectedSlug === "cap") {
        try {
          setPendingRun(await fetchPendingSquadRun(selectedChatId));
        } catch {
          setPendingRun(null);
        }
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao executar squad");
    } finally {
      setSquadExecuting(false);
    }
  }, [selectedChatId, pendingRun, loadMessages, selectedSlug, selectedProject]);

  const headerTitle = selectedChat?.title ?? selectedProject?.name ?? "squad-agentes";

  return (
    <div style={{ height: "100vh", display: "flex", flexDirection: "column" }}>
      <div
        style={{
          padding: "10px 16px",
          borderBottom: "1px solid var(--border)",
          fontSize: 13,
          color: "var(--muted)",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 12,
        }}
      >
        <span>
          <strong style={{ color: "var(--text)" }}>squad-agentes</strong> — chat local (MVP)
        </span>
        <span style={{ fontSize: 12 }}>
          {USE_FAKE_ASSISTANT
            ? "Modo fake: NEXT_PUBLIC_USE_FAKE_ASSISTANT=true"
            : "Meta-orquestrador + squad completa (aprovação explícita, projeto cap)"}
        </span>
      </div>
      {sending && !USE_FAKE_ASSISTANT && selectedChatId && (
        <div
          style={{
            padding: "8px 16px",
            background: "rgba(80, 140, 200, 0.12)",
            color: "var(--text)",
            fontSize: 13,
            borderBottom: "1px solid var(--border)",
          }}
        >
          Executando meta-orquestrador… isso pode levar alguns minutos.
        </div>
      )}
      {squadExecuting && !USE_FAKE_ASSISTANT && selectedChatId && (
        <div
          style={{
            padding: "8px 16px",
            background: "rgba(120, 100, 200, 0.12)",
            color: "var(--text)",
            fontSize: 13,
            borderBottom: "1px solid var(--border)",
          }}
        >
          Executando squad completa… isso pode levar vários minutos.
        </div>
      )}
      {error && (
        <div
          style={{
            padding: "10px 16px",
            background: "rgba(199, 84, 80, 0.15)",
            color: "var(--danger)",
            fontSize: 13,
            borderBottom: "1px solid var(--border)",
          }}
        >
          {error}
        </div>
      )}
      <div style={{ flex: 1, display: "flex", minHeight: 0 }}>
        <ProjectSidebar
          projects={projects}
          selectedSlug={selectedSlug}
          onSelect={(slug) => void onSelectProject(slug)}
          onCreateProject={() => void onCreateProject()}
          onRegisterProject={() => void onRegisterProject()}
          loading={loading}
        />
        {selectedSlug && (
          <ChatList
            chats={chats}
            selectedChatId={selectedChatId}
            onSelect={(id) => void onSelectChat(id)}
            onNewChat={() => void onNewChat()}
            disabled={!selectedSlug}
          />
        )}
        <div
          style={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            minWidth: 0,
            position: "relative",
          }}
        >
          {!selectedSlug && (
            <div style={{ flex: 1, padding: 32, color: "var(--muted)" }}>
              {loading ? "Carregando projetos…" : "Selecione um projeto na barra à esquerda."}
            </div>
          )}
          {selectedSlug && !selectedChatId && (
            <div style={{ flex: 1, padding: 32, color: "var(--muted)" }}>
              Selecione um chat ou crie um novo.
            </div>
          )}
          {selectedSlug && selectedChatId && (
            <>
              <div style={{ flex: 1, minHeight: 0, display: "flex", flexDirection: "column" }}>
                <ChatWindow
                  title={headerTitle}
                  messages={messages}
                  loading={messagesLoading}
                />
              </div>
              {selectedSlug === "cap" &&
                !USE_FAKE_ASSISTANT &&
                pendingRun &&
                selectedChatId &&
                (pendingRun.status === "awaiting_human_approval" ||
                  pendingRun.status === "meta_completed") && (
                  <div
                    style={{
                      padding: "10px 16px",
                      borderTop: "1px solid var(--border)",
                      display: "flex",
                      alignItems: "center",
                      gap: 12,
                      flexWrap: "wrap",
                    }}
                  >
                    <button
                      type="button"
                      onClick={() => void onExecuteSquad()}
                      disabled={sending || squadExecuting}
                      style={{
                        padding: "8px 14px",
                        borderRadius: 6,
                        border: "1px solid var(--border)",
                        background: "var(--text)",
                        color: "var(--bg)",
                        cursor: sending || squadExecuting ? "not-allowed" : "pointer",
                        fontSize: 13,
                        fontWeight: 600,
                      }}
                    >
                      Executar squad
                    </button>
                    <span style={{ fontSize: 12, color: "var(--muted)" }}>
                      Plano pronto (run {pendingRun.run_id}). Confirme para rodar PO → QA.
                    </span>
                  </div>
                )}
              <MessageInput
                onSend={(t) => void onSendMessage(t)}
                disabled={sending || squadExecuting}
              />
            </>
          )}
        </div>
      </div>
    </div>
  );
}
