/** Resposta fake opcional (`NEXT_PUBLIC_USE_FAKE_ASSISTANT=true`). */
export const FAKE_ASSISTANT_REPLY =
  "Mensagem registrada. A execução da squad será conectada na próxima fase.";

/** Base da API FastAPI local (browser + server). */
export function getApiBaseUrl(): string {
  const fromEnv =
    typeof process !== "undefined" && process.env.NEXT_PUBLIC_API_BASE_URL
      ? process.env.NEXT_PUBLIC_API_BASE_URL.trim()
      : "";
  if (fromEnv) return fromEnv.replace(/\/$/, "");
  return "http://127.0.0.1:8000";
}

export type ProjectRow = {
  id: number;
  name: string;
  slug: string;
  local_path: string;
  status: string;
  created_at: string;
  updated_at: string;
};

export type ChatRow = {
  id: number;
  project_id: number;
  title: string;
  status: string;
  created_at: string;
  updated_at: string;
};

export type MessageRow = {
  id: number;
  chat_id: number;
  role: string;
  content: string;
  created_at: string;
};

async function parseError(res: Response): Promise<string> {
  try {
    const t = await res.text();
    if (!t) return res.statusText;
    try {
      const j = JSON.parse(t) as { detail?: unknown };
      const d = j.detail;
      if (typeof d === "string") return d;
      if (Array.isArray(d)) {
        return d
          .map((item) =>
            typeof item === "object" && item !== null && "msg" in item
              ? String((item as { msg: string }).msg)
              : String(item),
          )
          .join("; ");
      }
    } catch {
      /* não é JSON */
    }
    return t;
  } catch {
    return res.statusText;
  }
}

export async function fetchProjects(): Promise<ProjectRow[]> {
  const base = getApiBaseUrl();
  const res = await fetch(`${base}/api/projects`, { cache: "no-store" });
  if (!res.ok) throw new Error(`GET /api/projects: ${res.status} ${await parseError(res)}`);
  return res.json();
}

export async function fetchChats(projectSlug: string): Promise<ChatRow[]> {
  const base = getApiBaseUrl();
  const res = await fetch(`${base}/api/chats/project/${encodeURIComponent(projectSlug)}`, {
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`GET chats: ${res.status} ${await parseError(res)}`);
  return res.json();
}

export async function createChat(projectSlug: string, title: string): Promise<ChatRow> {
  const base = getApiBaseUrl();
  const res = await fetch(`${base}/api/chats`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ project_slug: projectSlug, title }),
  });
  if (!res.ok) throw new Error(`POST /api/chats: ${res.status} ${await parseError(res)}`);
  return res.json();
}

export async function fetchMessages(chatId: number): Promise<MessageRow[]> {
  const base = getApiBaseUrl();
  const res = await fetch(`${base}/api/chats/${chatId}/messages`, { cache: "no-store" });
  if (!res.ok) throw new Error(`GET messages: ${res.status} ${await parseError(res)}`);
  return res.json();
}

export async function sendMessage(
  chatId: number,
  role: "user" | "assistant" | "system" | "agent",
  content: string,
): Promise<MessageRow> {
  const base = getApiBaseUrl();
  const res = await fetch(`${base}/api/chats/messages`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ chat_id: chatId, role, content }),
  });
  if (!res.ok) throw new Error(`POST message: ${res.status} ${await parseError(res)}`);
  return res.json();
}

export type MetaOrchestratorSendResult = {
  user_message: MessageRow;
  assistant_message: MessageRow;
  run_id: string;
  run_path: string;
  status: "success" | "failed";
  context_loaded?: boolean;
  context_evidence_path?: string | null;
};

/** Envia mensagem do usuário e executa o meta-orquestrador (salva resposta assistant na API). */
export async function sendMessageWithMetaOrchestrator(
  chatId: number,
  content: string,
): Promise<MetaOrchestratorSendResult> {
  const base = getApiBaseUrl();
  const res = await fetch(`${base}/api/chats/messages/with-meta-orchestrator`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ chat_id: chatId, content }),
  });
  if (!res.ok) {
    throw new Error(`POST meta-orquestrador: ${res.status} ${await parseError(res)}`);
  }
  return res.json();
}

export type PendingSquadRun = {
  run_id: string;
  run_path: string;
  status: string;
};

export async function fetchPendingSquadRun(chatId: number): Promise<PendingSquadRun | null> {
  const base = getApiBaseUrl();
  const res = await fetch(`${base}/api/chats/${chatId}/pending-squad-run`, { cache: "no-store" });
  if (!res.ok) throw new Error(`GET pending run: ${res.status} ${await parseError(res)}`);
  const data: unknown = await res.json();
  if (data === null) return null;
  return data as PendingSquadRun;
}

export type ExecuteSquadResult = {
  status: string;
  run_id: string;
  final_path: string;
  assistant_message: MessageRow;
  context_loaded?: boolean | null;
  context_evidence_path?: string | null;
};

export async function executeSquad(runId: string, chatId: number): Promise<ExecuteSquadResult> {
  const base = getApiBaseUrl();
  const res = await fetch(`${base}/api/runs/${encodeURIComponent(runId)}/execute-squad`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ chat_id: chatId }),
  });
  if (!res.ok) {
    throw new Error(`POST execute-squad: ${res.status} ${await parseError(res)}`);
  }
  return res.json();
}

export async function createProject(name: string): Promise<ProjectRow> {
  const base = getApiBaseUrl();
  const res = await fetch(`${base}/api/projects`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
  if (!res.ok) throw new Error(`POST /api/projects: ${res.status} ${await parseError(res)}`);
  return res.json();
}

export async function registerProject(name: string, localPath: string): Promise<ProjectRow> {
  const base = getApiBaseUrl();
  const res = await fetch(`${base}/api/projects/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, local_path: localPath }),
  });
  if (!res.ok) throw new Error(`POST register: ${res.status} ${await parseError(res)}`);
  return res.json();
}
