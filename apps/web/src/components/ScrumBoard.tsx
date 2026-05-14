"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  assignTaskToAgent,
  createTask,
  executeBoardRun,
  fetchRunArtifacts,
  listTasks,
  prepareTaskRun,
  updateTaskStatus,
  type RunArtifactsPayload,
  type TaskRow,
} from "@/lib/api";

const TASK_STATUSES: { key: TaskRow["status"]; label: string }[] = [
  { key: "backlog", label: "Backlog" },
  { key: "ready", label: "Ready" },
  { key: "in_progress", label: "In Progress" },
  { key: "in_review", label: "In Review" },
  { key: "qa", label: "QA" },
  { key: "waiting_human_approval", label: "Waiting Human Approval" },
  { key: "done", label: "Done" },
  { key: "blocked", label: "Blocked" },
];

const AGENTS = ["po", "architect", "dev-base", "reviewer", "qa"] as const;

function canExecuteBoardRun(t: TaskRow | undefined): boolean {
  if (!t?.run_id) return false;
  const rs = t.run_status ?? null;
  if (rs === "completed" || rs === "running_squad") return false;
  return true;
}

function shortText(text: string | null, max = 140): string {
  if (!text) return "";
  const t = text.trim();
  if (t.length <= max) return t;
  return `${t.slice(0, max)}…`;
}

type Props = {
  projectSlug: string;
  onError: (message: string | null) => void;
};

export function ScrumBoard({ projectSlug, onError }: Props) {
  const [tasks, setTasks] = useState<TaskRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [quickTitle, setQuickTitle] = useState("");
  const [quickDesc, setQuickDesc] = useState("");
  const [creating, setCreating] = useState(false);
  const [selectedTaskId, setSelectedTaskId] = useState<number | null>(null);
  const [preparingRun, setPreparingRun] = useState(false);
  const [executingRun, setExecutingRun] = useState(false);
  const [boardHint, setBoardHint] = useState<{ type: "ok" | "err"; text: string } | null>(null);
  const [runResultOpen, setRunResultOpen] = useState(false);
  const [runResultLoading, setRunResultLoading] = useState(false);
  const [runResultError, setRunResultError] = useState<string | null>(null);
  const [runArtifacts, setRunArtifacts] = useState<RunArtifactsPayload | null>(null);
  const [artifactTab, setArtifactTab] = useState<"input.md" | "final.md" | "execution.log">(
    "final.md",
  );

  const byStatus = useMemo(() => {
    const m = new Map<string, TaskRow[]>();
    for (const s of TASK_STATUSES) m.set(s.key, []);
    for (const t of tasks) {
      const list = m.get(t.status);
      if (list) list.push(t);
      else {
        const fallback = m.get("backlog")!;
        fallback.push(t);
      }
    }
    return m;
  }, [tasks]);

  const refresh = useCallback(async () => {
    setLoading(true);
    onError(null);
    try {
      setTasks(await listTasks(projectSlug));
    } catch (e) {
      onError(e instanceof Error ? e.message : "Falha ao carregar tarefas");
    } finally {
      setLoading(false);
    }
  }, [projectSlug, onError]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const onCreateQuick = useCallback(async () => {
    const title = quickTitle.trim();
    if (!title) return;
    setCreating(true);
    onError(null);
    try {
      await createTask(projectSlug, title, quickDesc.trim() || undefined);
      setQuickTitle("");
      setQuickDesc("");
      await refresh();
    } catch (e) {
      onError(e instanceof Error ? e.message : "Erro ao criar tarefa");
    } finally {
      setCreating(false);
    }
  }, [projectSlug, quickTitle, quickDesc, refresh, onError]);

  const onStatusChange = useCallback(
    async (taskId: number, status: TaskRow["status"]) => {
      setBusyId(taskId);
      onError(null);
      try {
        await updateTaskStatus(taskId, status);
        await refresh();
      } catch (e) {
        onError(e instanceof Error ? e.message : "Erro ao atualizar status");
      } finally {
        setBusyId(null);
      }
    },
    [refresh, onError],
  );

  const onAgentChange = useCallback(
    async (taskId: number, agent: string) => {
      setBusyId(taskId);
      onError(null);
      try {
        await assignTaskToAgent(taskId, agent === "" ? null : agent);
        await refresh();
      } catch (e) {
        onError(e instanceof Error ? e.message : "Erro ao atribuir agente");
      } finally {
        setBusyId(null);
      }
    },
    [refresh, onError],
  );

  const statusIndex = useCallback((s: string) => TASK_STATUSES.findIndex((x) => x.key === s), []);

  const nudgeStatus = useCallback(
    async (task: TaskRow, delta: number) => {
      const idx = statusIndex(task.status);
      const next = TASK_STATUSES[Math.min(TASK_STATUSES.length - 1, Math.max(0, idx + delta))];
      if (next && next.key !== task.status) await onStatusChange(task.id, next.key);
    },
    [onStatusChange, statusIndex],
  );

  const selectedTask = useMemo(
    () => (selectedTaskId != null ? tasks.find((t) => t.id === selectedTaskId) : undefined),
    [tasks, selectedTaskId],
  );

  const onPrepareRun = useCallback(async () => {
    if (selectedTaskId == null) return;
    setPreparingRun(true);
    onError(null);
    setBoardHint(null);
    try {
      await prepareTaskRun(selectedTaskId);
      setBoardHint({ type: "ok", text: "Run preparada. Você pode executar quando quiser." });
      await refresh();
    } catch (e) {
      onError(e instanceof Error ? e.message : "Erro ao preparar execução");
    } finally {
      setPreparingRun(false);
    }
  }, [selectedTaskId, refresh, onError]);

  const onExecuteBoardRun = useCallback(async () => {
    const rid = selectedTask?.run_id;
    if (!rid) return;
    setExecutingRun(true);
    onError(null);
    setBoardHint(null);
    try {
      const r = await executeBoardRun(rid);
      if (r.status === "completed") {
        setBoardHint({ type: "ok", text: "Execução concluída (squad). Revise o resultado em final.md." });
      } else {
        const d = (r.error_detail ?? "Falha na execução.").slice(0, 200);
        setBoardHint({ type: "err", text: d });
      }
      await refresh();
    } catch (e) {
      onError(e instanceof Error ? e.message : "Erro ao executar run");
    } finally {
      setExecutingRun(false);
    }
  }, [selectedTask, refresh, onError]);

  const openRunResult = useCallback(async () => {
    const rid = selectedTask?.run_id;
    if (!rid) {
      setRunResultError("Selecione uma tarefa com run associada.");
      return;
    }
    const rs = selectedTask?.run_status ?? null;
    setArtifactTab(
      rs === "failed" ? "execution.log" : rs === "completed" ? "final.md" : "input.md",
    );
    setRunResultOpen(true);
    setRunResultLoading(true);
    setRunResultError(null);
    setRunArtifacts(null);
    try {
      setRunArtifacts(await fetchRunArtifacts(rid));
    } catch (e) {
      setRunResultError(e instanceof Error ? e.message : "Falha ao carregar artefactos");
    } finally {
      setRunResultLoading(false);
    }
  }, [selectedTask]);

  return (
    <div
      style={{
        flex: 1,
        display: "flex",
        flexDirection: "column",
        minHeight: 0,
        minWidth: 0,
        background: "var(--bg)",
      }}
    >
      <div
        style={{
          padding: "12px 16px",
          borderBottom: "1px solid var(--border)",
          display: "flex",
          flexDirection: "column",
          gap: 8,
        }}
      >
        <div style={{ fontSize: 14, fontWeight: 600, color: "var(--text)" }}>Quadro — tarefas</div>
        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            gap: 8,
            alignItems: "center",
            paddingTop: 4,
            borderTop: "1px solid var(--border)",
          }}
        >
          <span style={{ fontSize: 12, color: "var(--muted)", flex: "1 1 220px" }}>
            {selectedTaskId == null
              ? "Clique em uma tarefa para selecionar."
              : selectedTask?.run_id && selectedTask.run_status === "completed"
                ? "Run concluída — não é possível reexecutar por aqui."
                : selectedTask?.run_id && selectedTask.run_status === "running_squad"
                  ? "Run em execução no servidor — aguarde."
                  : selectedTask?.run_id
                    ? `Run: ${selectedTask.run_id}. Use “Executar run” para rodar a squad (usa input.md).`
                    : `Selecionada: #${selectedTaskId} — ${selectedTask?.title ?? ""}`}
          </span>
          <button
            type="button"
            onClick={() => void onPrepareRun()}
            disabled={
              preparingRun ||
              executingRun ||
              selectedTaskId == null ||
              (selectedTask != null && selectedTask.run_id != null)
            }
            style={{
              padding: "8px 14px",
              borderRadius: 6,
              border: "1px solid var(--border)",
              background: "var(--sidebar)",
              color: "var(--text)",
              fontWeight: 600,
              fontSize: 13,
              opacity:
                preparingRun ||
                executingRun ||
                selectedTaskId == null ||
                (selectedTask != null && selectedTask.run_id != null)
                  ? 0.45
                  : 1,
            }}
          >
            {preparingRun ? "Preparando…" : "Preparar execução"}
          </button>
          <button
            type="button"
            onClick={() => void onExecuteBoardRun()}
            disabled={
              executingRun ||
              preparingRun ||
              selectedTaskId == null ||
              !canExecuteBoardRun(selectedTask)
            }
            style={{
              padding: "8px 14px",
              borderRadius: 6,
              border: "1px solid var(--border)",
              background: "var(--accent)",
              color: "#fff",
              fontWeight: 600,
              fontSize: 13,
              opacity:
                executingRun ||
                preparingRun ||
                selectedTaskId == null ||
                !canExecuteBoardRun(selectedTask)
                  ? 0.45
                  : 1,
            }}
          >
            {executingRun ? "Executando…" : "Executar run"}
          </button>
          <button
            type="button"
            onClick={() => void openRunResult()}
            disabled={preparingRun || executingRun || selectedTaskId == null || !selectedTask?.run_id}
            style={{
              padding: "8px 14px",
              borderRadius: 6,
              border: "1px solid var(--border)",
              background: "var(--sidebar)",
              color: "var(--text)",
              fontWeight: 600,
              fontSize: 13,
              opacity:
                preparingRun || executingRun || selectedTaskId == null || !selectedTask?.run_id
                  ? 0.45
                  : 1,
            }}
          >
            Ver resultado
          </button>
        </div>
        {boardHint && (
          <div
            style={{
              fontSize: 12,
              padding: "6px 0 0",
              color: boardHint.type === "ok" ? "var(--accent)" : "var(--danger)",
            }}
          >
            {boardHint.text}
          </div>
        )}
        <div style={{ display: "flex", flexWrap: "wrap", gap: 8, alignItems: "flex-end" }}>
          <label style={{ display: "flex", flexDirection: "column", gap: 4, flex: "1 1 200px" }}>
            <span style={{ fontSize: 11, color: "var(--muted)" }}>Título (rápido)</span>
            <input
              value={quickTitle}
              onChange={(e) => setQuickTitle(e.target.value)}
              placeholder="Nova tarefa…"
              style={{
                padding: "8px 10px",
                borderRadius: 6,
                border: "1px solid var(--border)",
                background: "var(--sidebar)",
              }}
            />
          </label>
          <label style={{ display: "flex", flexDirection: "column", gap: 4, flex: "2 1 280px" }}>
            <span style={{ fontSize: 11, color: "var(--muted)" }}>Descrição (opcional)</span>
            <input
              value={quickDesc}
              onChange={(e) => setQuickDesc(e.target.value)}
              placeholder="Detalhes curtos…"
              style={{
                padding: "8px 10px",
                borderRadius: 6,
                border: "1px solid var(--border)",
                background: "var(--sidebar)",
              }}
            />
          </label>
          <button
            type="button"
            onClick={() => void onCreateQuick()}
            disabled={creating || !quickTitle.trim()}
            style={{
              padding: "8px 14px",
              borderRadius: 6,
              border: "none",
              background: "var(--accent)",
              color: "#fff",
              fontWeight: 600,
              fontSize: 13,
              opacity: creating || !quickTitle.trim() ? 0.5 : 1,
            }}
          >
            Criar tarefa
          </button>
        </div>
      </div>

      <div style={{ flex: 1, overflow: "auto", padding: 12 }}>
        {loading ? (
          <div style={{ color: "var(--muted)", padding: 16 }}>Carregando tarefas…</div>
        ) : (
          <div
            style={{
              display: "flex",
              gap: 10,
              alignItems: "flex-start",
              minWidth: "min-content",
            }}
          >
            {TASK_STATUSES.map((col) => (
              <div
                key={col.key}
                style={{
                  width: 220,
                  flex: "0 0 220px",
                  background: "var(--sidebar)",
                  borderRadius: 8,
                  border: "1px solid var(--border)",
                  display: "flex",
                  flexDirection: "column",
                  maxHeight: "100%",
                }}
              >
                <div
                  style={{
                    padding: "8px 10px",
                    fontSize: 12,
                    fontWeight: 600,
                    borderBottom: "1px solid var(--border)",
                    color: "var(--text)",
                  }}
                >
                  {col.label}
                  <span style={{ color: "var(--muted)", fontWeight: 400, marginLeft: 6 }}>
                    ({byStatus.get(col.key)?.length ?? 0})
                  </span>
                </div>
                <div style={{ padding: 8, display: "flex", flexDirection: "column", gap: 8 }}>
                  {(byStatus.get(col.key) ?? []).map((task) => (
                    <div
                      key={task.id}
                      onClick={() => setSelectedTaskId(task.id)}
                      style={{
                        padding: 10,
                        borderRadius: 6,
                        background: "var(--bg)",
                        border:
                          selectedTaskId === task.id
                            ? "2px solid var(--accent)"
                            : "1px solid var(--border)",
                        fontSize: 12,
                        opacity: busyId === task.id ? 0.6 : 1,
                        cursor: "pointer",
                      }}
                    >
                      <div style={{ fontWeight: 600, marginBottom: 6, color: "var(--text)" }}>
                        {task.title}
                      </div>
                      {task.description ? (
                        <div style={{ color: "var(--muted)", marginBottom: 8, lineHeight: 1.35 }}>
                          {shortText(task.description)}
                        </div>
                      ) : null}
                      <div style={{ fontSize: 11, color: "var(--muted)", marginBottom: 6 }}>
                        {task.story_id != null ? `Story #${task.story_id}` : "Sem story"}{" "}
                        {task.run_id != null ? ` · Run ${task.run_id}` : ""}
                      </div>
                      <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                        <label style={{ display: "flex", flexDirection: "column", gap: 2 }}>
                          <span style={{ fontSize: 10, color: "var(--muted)" }}>Status</span>
                          <div
                            style={{ display: "flex", gap: 4, alignItems: "center" }}
                            onClick={(e) => e.stopPropagation()}
                            onKeyDown={(e) => e.stopPropagation()}
                          >
                            <button
                              type="button"
                              title="Coluna anterior"
                              onClick={(e) => {
                                e.stopPropagation();
                                void nudgeStatus(task, -1);
                              }}
                              disabled={busyId === task.id}
                              style={{
                                padding: "2px 6px",
                                borderRadius: 4,
                                border: "1px solid var(--border)",
                                background: "var(--sidebar)",
                                color: "var(--text)",
                                fontSize: 11,
                              }}
                            >
                              «
                            </button>
                            <select
                              value={task.status}
                              onClick={(e) => e.stopPropagation()}
                              onChange={(e) =>
                                void onStatusChange(task.id, e.target.value as TaskRow["status"])
                              }
                              disabled={busyId === task.id}
                              style={{
                                flex: 1,
                                fontSize: 11,
                                padding: "4px 6px",
                                borderRadius: 4,
                                border: "1px solid var(--border)",
                                background: "var(--sidebar)",
                                color: "var(--text)",
                              }}
                            >
                              {TASK_STATUSES.map((s) => (
                                <option key={s.key} value={s.key}>
                                  {s.label}
                                </option>
                              ))}
                            </select>
                            <button
                              type="button"
                              title="Próxima coluna"
                              onClick={(e) => {
                                e.stopPropagation();
                                void nudgeStatus(task, 1);
                              }}
                              disabled={busyId === task.id}
                              style={{
                                padding: "2px 6px",
                                borderRadius: 4,
                                border: "1px solid var(--border)",
                                background: "var(--sidebar)",
                                color: "var(--text)",
                                fontSize: 11,
                              }}
                            >
                              »
                            </button>
                          </div>
                        </label>
                        <label
                          style={{ display: "flex", flexDirection: "column", gap: 2 }}
                          onClick={(e) => e.stopPropagation()}
                          onKeyDown={(e) => e.stopPropagation()}
                        >
                          <span style={{ fontSize: 10, color: "var(--muted)" }}>Agente</span>
                          <select
                            value={task.assignee_agent ?? ""}
                            onClick={(e) => e.stopPropagation()}
                            onChange={(e) => void onAgentChange(task.id, e.target.value)}
                            disabled={busyId === task.id}
                            style={{
                              fontSize: 11,
                              padding: "4px 6px",
                              borderRadius: 4,
                              border: "1px solid var(--border)",
                              background: "var(--sidebar)",
                              color: "var(--text)",
                            }}
                          >
                            <option value="">—</option>
                            {AGENTS.map((a) => (
                              <option key={a} value={a}>
                                {a}
                              </option>
                            ))}
                          </select>
                        </label>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
      {runResultOpen ? (
        <div
          role="presentation"
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0,0,0,0.35)",
            zIndex: 40,
            display: "flex",
            justifyContent: "flex-end",
          }}
          onClick={() => setRunResultOpen(false)}
          onKeyDown={(e) => {
            if (e.key === "Escape") setRunResultOpen(false);
          }}
        >
          <div
            role="dialog"
            aria-label="Resultado da run"
            style={{
              width: "min(560px, 96vw)",
              height: "100%",
              background: "var(--bg)",
              borderLeft: "1px solid var(--border)",
              display: "flex",
              flexDirection: "column",
              boxShadow: "-4px 0 24px rgba(0,0,0,0.12)",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div
              style={{
                padding: "12px 14px",
                borderBottom: "1px solid var(--border)",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                gap: 8,
              }}
            >
              <div style={{ fontWeight: 600, fontSize: 14, color: "var(--text)" }}>
                Resultado da run
                {selectedTask?.run_id ? (
                  <span style={{ fontWeight: 400, color: "var(--muted)", marginLeft: 8 }}>
                    {selectedTask.run_id}
                  </span>
                ) : null}
              </div>
              <button
                type="button"
                onClick={() => setRunResultOpen(false)}
                style={{
                  padding: "6px 12px",
                  borderRadius: 6,
                  border: "1px solid var(--border)",
                  background: "var(--sidebar)",
                  color: "var(--text)",
                  fontSize: 12,
                }}
              >
                Fechar
              </button>
            </div>
            <div style={{ padding: "10px 14px", borderBottom: "1px solid var(--border)" }}>
              {selectedTask?.run_status === "created" || selectedTask?.run_status === "failed" ? (
                <p style={{ margin: 0, fontSize: 12, color: "var(--muted)" }}>
                  {selectedTask.run_status === "created"
                    ? "A squad ainda não foi executada para esta run — só verá input.md com certeza; final.md e o log aparecem após “Executar run”."
                    : "Run falhou — veja execution.log para detalhes; final.md pode estar ausente ou parcial."}
                </p>
              ) : selectedTask?.run_status === "running_squad" ? (
                <p style={{ margin: 0, fontSize: 12, color: "var(--muted)" }}>
                  Execução em curso — pode atualizar daqui a instantes.
                </p>
              ) : null}
              {runResultError ? (
                <p style={{ margin: "8px 0 0", fontSize: 12, color: "var(--danger)" }}>
                  {runResultError}
                </p>
              ) : null}
            </div>
            <div style={{ display: "flex", gap: 6, padding: "8px 12px", flexWrap: "wrap" }}>
              {(["input.md", "final.md", "execution.log"] as const).map((name) => (
                <button
                  key={name}
                  type="button"
                  onClick={() => setArtifactTab(name)}
                  style={{
                    padding: "6px 10px",
                    borderRadius: 6,
                    border: "1px solid var(--border)",
                    background: artifactTab === name ? "var(--accent)" : "var(--sidebar)",
                    color: artifactTab === name ? "#fff" : "var(--text)",
                    fontSize: 12,
                    fontWeight: artifactTab === name ? 600 : 400,
                  }}
                >
                  {name === "execution.log" ? "execution.log" : name}
                </button>
              ))}
            </div>
            <div style={{ flex: 1, overflow: "auto", padding: 12 }}>
              {runResultLoading ? (
                <p style={{ color: "var(--muted)", fontSize: 13 }}>A carregar…</p>
              ) : (
                (() => {
                  const art = runArtifacts?.artifacts.find((a) => a.name === artifactTab);
                  if (!art?.exists) {
                    return (
                      <p style={{ color: "var(--muted)", fontSize: 13 }}>
                        Este ficheiro ainda não existe nesta run.
                      </p>
                    );
                  }
                  if (art.truncated) {
                    return (
                      <p style={{ color: "var(--danger)", fontSize: 13 }}>
                        Ficheiro demasiado grande para pré-visualização (limite da API).
                      </p>
                    );
                  }
                  return (
                    <pre
                      style={{
                        margin: 0,
                        whiteSpace: "pre-wrap",
                        wordBreak: "break-word",
                        fontSize: 12,
                        lineHeight: 1.45,
                        color: "var(--text)",
                        fontFamily: "ui-monospace, monospace",
                      }}
                    >
                      {art.content ?? ""}
                    </pre>
                  );
                })()
              )}
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
