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

export type BootstrapStatus = {
  project_slug: string;
  ok: boolean;
  block_reason?: string | null;
  local_path_resolved: string;
  has_squad_dir: boolean;
  has_context_md: boolean;
  has_backlog_json: boolean;
  context_meets_minimum: boolean;
  needs_bootstrap: boolean;
  ready_for_meta_orchestrator: boolean;
  expected_context_path: string;
};

export type MetaOrchestratorSendResult = {
  user_message: MessageRow;
  assistant_message: MessageRow;
  run_id: string;
  run_path: string;
  status: "success" | "failed" | "bootstrap";
  context_loaded?: boolean;
  context_evidence_path?: string | null;
  mode?: string;
  bootstrap_status?: BootstrapStatus | null;
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

export async function renameChat(chatId: number, title: string): Promise<ChatRow> {
  const base = getApiBaseUrl();
  const res = await fetch(`${base}/api/chats/${chatId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title }),
  });
  if (!res.ok) throw new Error(`PATCH /api/chats: ${res.status} ${await parseError(res)}`);
  return res.json();
}

export async function deleteChat(chatId: number): Promise<void> {
  const base = getApiBaseUrl();
  const res = await fetch(`${base}/api/chats/${chatId}`, { method: "DELETE" });
  if (!res.ok) throw new Error(`DELETE /api/chats: ${res.status} ${await parseError(res)}`);
}

export async function fetchBootstrapStatus(projectSlug: string): Promise<BootstrapStatus> {
  const base = getApiBaseUrl();
  const res = await fetch(
    `${base}/api/projects/${encodeURIComponent(projectSlug)}/bootstrap-status`,
    { cache: "no-store" },
  );
  if (!res.ok) throw new Error(`GET bootstrap-status: ${res.status} ${await parseError(res)}`);
  return res.json();
}

export async function postProjectBootstrap(projectSlug: string): Promise<{
  project_slug: string;
  local_path_resolved: string;
  created_paths: string[];
  bootstrap_status: BootstrapStatus;
}> {
  const base = getApiBaseUrl();
  const res = await fetch(`${base}/api/projects/${encodeURIComponent(projectSlug)}/bootstrap`, {
    method: "POST",
  });
  if (!res.ok) throw new Error(`POST bootstrap: ${res.status} ${await parseError(res)}`);
  return res.json();
}

export async function postRefineContext(
  projectSlug: string,
  chatId: number,
  overwrite = true,
): Promise<{ project_slug: string; context_path: string; bootstrap_status: BootstrapStatus }> {
  const base = getApiBaseUrl();
  const res = await fetch(
    `${base}/api/projects/${encodeURIComponent(projectSlug)}/context/refine`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ chat_id: chatId, overwrite }),
    },
  );
  if (!res.ok) throw new Error(`POST context/refine: ${res.status} ${await parseError(res)}`);
  return res.json();
}

export async function saveImportantPrompt(
  chatId: number,
  content: string,
  titleSlug = "prompt",
): Promise<{ path: string; relative: string }> {
  const base = getApiBaseUrl();
  const res = await fetch(`${base}/api/chats/${chatId}/save-prompt`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title_slug: titleSlug, content }),
  });
  if (!res.ok) throw new Error(`POST save-prompt: ${res.status} ${await parseError(res)}`);
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

/** Status de itens de backlog (épicos, histórias, tarefas). */
export type BacklogStatus =
  | "backlog"
  | "ready"
  | "in_progress"
  | "in_review"
  | "qa"
  | "waiting_human_approval"
  | "done"
  | "blocked";

export type EpicRow = {
  id: number;
  project_id: number;
  title: string;
  description: string | null;
  status: string;
  created_at: string;
  updated_at: string;
};

export type StoryRow = {
  id: number;
  epic_id: number | null;
  project_id: number;
  title: string;
  description: string | null;
  status: string;
  priority: string;
  created_at: string;
  updated_at: string;
};

export type TaskRow = {
  id: number;
  story_id: number | null;
  project_id: number;
  title: string;
  description: string | null;
  status: BacklogStatus;
  assignee_agent: string | null;
  run_id: string | null;
  created_at: string;
  updated_at: string;
  /** Status da linha `squad_runs` ligada a `run_id`, se houver. */
  run_status?: string | null;
};

export async function listEpics(projectSlug: string): Promise<EpicRow[]> {
  const base = getApiBaseUrl();
  const res = await fetch(
    `${base}/api/backlog/${encodeURIComponent(projectSlug)}/epics`,
    { cache: "no-store" },
  );
  if (!res.ok) throw new Error(`GET epics: ${res.status} ${await parseError(res)}`);
  return res.json();
}

export async function createEpic(
  projectSlug: string,
  title: string,
  description?: string,
): Promise<EpicRow> {
  const base = getApiBaseUrl();
  const res = await fetch(`${base}/api/backlog/${encodeURIComponent(projectSlug)}/epics`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, description: description ?? null }),
  });
  if (!res.ok) throw new Error(`POST epic: ${res.status} ${await parseError(res)}`);
  return res.json();
}

export async function listStories(projectSlug: string): Promise<StoryRow[]> {
  const base = getApiBaseUrl();
  const res = await fetch(
    `${base}/api/backlog/${encodeURIComponent(projectSlug)}/stories`,
    { cache: "no-store" },
  );
  if (!res.ok) throw new Error(`GET stories: ${res.status} ${await parseError(res)}`);
  return res.json();
}

export async function createStory(
  projectSlug: string,
  title: string,
  options?: { description?: string; epic_id?: number | null; priority?: string },
): Promise<StoryRow> {
  const base = getApiBaseUrl();
  const res = await fetch(`${base}/api/backlog/${encodeURIComponent(projectSlug)}/stories`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      title,
      description: options?.description ?? null,
      epic_id: options?.epic_id ?? null,
      priority: options?.priority ?? "medium",
    }),
  });
  if (!res.ok) throw new Error(`POST story: ${res.status} ${await parseError(res)}`);
  return res.json();
}

export async function listTasks(projectSlug: string): Promise<TaskRow[]> {
  const base = getApiBaseUrl();
  const res = await fetch(
    `${base}/api/backlog/${encodeURIComponent(projectSlug)}/tasks`,
    { cache: "no-store" },
  );
  if (!res.ok) throw new Error(`GET tasks: ${res.status} ${await parseError(res)}`);
  return res.json();
}

export async function createTask(
  projectSlug: string,
  title: string,
  description?: string,
  storyId?: number | null,
  assigneeAgent?: string | null,
): Promise<TaskRow> {
  const base = getApiBaseUrl();
  const res = await fetch(`${base}/api/backlog/${encodeURIComponent(projectSlug)}/tasks`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      title,
      description: description ?? null,
      story_id: storyId ?? null,
      assignee_agent: assigneeAgent ?? null,
    }),
  });
  if (!res.ok) throw new Error(`POST task: ${res.status} ${await parseError(res)}`);
  return res.json();
}

export async function updateTaskStatus(taskId: number, status: BacklogStatus): Promise<TaskRow> {
  const base = getApiBaseUrl();
  const res = await fetch(`${base}/api/backlog/tasks/${taskId}/status`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status }),
  });
  if (!res.ok) throw new Error(`PATCH task status: ${res.status} ${await parseError(res)}`);
  return res.json();
}

export async function assignTaskToAgent(
  taskId: number,
  assigneeAgent: string | null,
): Promise<TaskRow> {
  const base = getApiBaseUrl();
  const res = await fetch(`${base}/api/backlog/tasks/${taskId}/assign`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ assignee_agent: assigneeAgent }),
  });
  if (!res.ok) throw new Error(`PATCH task assign: ${res.status} ${await parseError(res)}`);
  return res.json();
}

/** Prepara pasta `runs/<slug>/<run_id>/` com input.md e vincula à tarefa (não executa squad). */
export type PrepareTaskRunResult = {
  task: TaskRow;
  run_id: string;
  run_path: string;
  input_path: string;
};

export async function prepareTaskRun(taskId: number): Promise<PrepareTaskRunResult> {
  const base = getApiBaseUrl();
  const res = await fetch(`${base}/api/backlog/tasks/${taskId}/prepare-run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });
  if (!res.ok) {
    throw new Error(`POST prepare-run: ${res.status} ${await parseError(res)}`);
  }
  return res.json();
}

/** Executa squad para run `board-*` já preparada (ação explícita). */
export type ExecuteBoardRunResult = {
  status: string;
  run_id: string;
  final_path: string;
  execution_log_path: string;
  task: TaskRow;
  error_detail: string | null;
};

export async function executeBoardRun(runId: string): Promise<ExecuteBoardRunResult> {
  const base = getApiBaseUrl();
  const res = await fetch(`${base}/api/runs/${encodeURIComponent(runId)}/execute-board-run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });
  if (!res.ok) {
    throw new Error(`POST execute-board-run: ${res.status} ${await parseError(res)}`);
  }
  return res.json();
}

/** Artefactos de uma run (input.md, final.md, execution.log). */
export type RunArtifactItem = {
  name: string;
  type: string;
  exists: boolean;
  content: string | null;
  truncated?: boolean | null;
};

export type RunArtifactsPayload = {
  run_id: string;
  project_slug: string;
  artifacts: RunArtifactItem[];
};

export async function fetchRunArtifacts(runId: string): Promise<RunArtifactsPayload> {
  const base = getApiBaseUrl();
  const res = await fetch(`${base}/api/runs/${encodeURIComponent(runId)}/artifacts`, {
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`GET run artifacts: ${res.status} ${await parseError(res)}`);
  return res.json();
}

export type ChatAttachmentRow = {
  id: number;
  chat_id: number;
  message_id: number | null;
  project_slug: string;
  file_name: string;
  file_path: string;
  mime_type: string;
  size_bytes: number;
  created_at: string;
};

export function getChatAttachmentUrl(attachmentId: number): string {
  return `${getApiBaseUrl()}/api/chats/attachments/${attachmentId}`;
}

export async function fetchChatAttachments(chatId: number): Promise<ChatAttachmentRow[]> {
  const base = getApiBaseUrl();
  const res = await fetch(`${base}/api/chats/${chatId}/attachments`, { cache: "no-store" });
  if (!res.ok) throw new Error(`GET attachments: ${res.status} ${await parseError(res)}`);
  return res.json();
}

export async function uploadChatImage(chatId: number, file: File): Promise<ChatAttachmentRow> {
  const base = getApiBaseUrl();
  const body = new FormData();
  body.append("file", file);
  const res = await fetch(`${base}/api/chats/${chatId}/attachments`, {
    method: "POST",
    body,
  });
  if (!res.ok) throw new Error(`POST attachment: ${res.status} ${await parseError(res)}`);
  return res.json();
}
