import type { ProjectRow } from "@/lib/api";

type Props = {
  projects: ProjectRow[];
  selectedSlug: string | null;
  onSelect: (slug: string) => void;
  onCreateProject: () => void;
  onRegisterProject: () => void;
  loading?: boolean;
};

export function ProjectSidebar({
  projects,
  selectedSlug,
  onSelect,
  onCreateProject,
  onRegisterProject,
  loading,
}: Props) {
  return (
    <aside
      style={{
        width: 260,
        minWidth: 260,
        background: "var(--sidebar)",
        borderRight: "1px solid var(--border)",
        display: "flex",
        flexDirection: "column",
        height: "100%",
      }}
    >
      <div style={{ padding: "12px 12px 8px", borderBottom: "1px solid var(--border)" }}>
        <div style={{ fontSize: 12, color: "var(--muted)", marginBottom: 8 }}>Projetos</div>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <button
            type="button"
            onClick={onCreateProject}
            disabled={loading}
            style={{
              flex: 1,
              minWidth: 100,
              padding: "6px 8px",
              borderRadius: 6,
              border: "1px solid var(--border)",
              background: "transparent",
              color: "var(--text)",
            }}
          >
            Novo
          </button>
          <button
            type="button"
            onClick={onRegisterProject}
            disabled={loading}
            style={{
              flex: 1,
              minWidth: 100,
              padding: "6px 8px",
              borderRadius: 6,
              border: "1px solid var(--border)",
              background: "transparent",
              color: "var(--text)",
            }}
          >
            Registrar
          </button>
        </div>
      </div>
      <nav style={{ flex: 1, overflowY: "auto", padding: 8 }}>
        {projects.length === 0 && (
          <p style={{ fontSize: 13, color: "var(--muted)", margin: 8 }}>Nenhum projeto.</p>
        )}
        <ul style={{ listStyle: "none", margin: 0, padding: 0 }}>
          {projects.map((p) => {
            const active = p.slug === selectedSlug;
            return (
              <li key={p.id} style={{ marginBottom: 4 }}>
                <button
                  type="button"
                  onClick={() => onSelect(p.slug)}
                  style={{
                    width: "100%",
                    textAlign: "left",
                    padding: "10px 12px",
                    borderRadius: 8,
                    border: "none",
                    background: active ? "var(--user-bubble)" : "transparent",
                    color: "var(--text)",
                  }}
                >
                  <div style={{ fontWeight: 600, fontSize: 14 }}>{p.name}</div>
                  <div style={{ fontSize: 11, color: "var(--muted)", marginTop: 2 }}>{p.slug}</div>
                </button>
              </li>
            );
          })}
        </ul>
      </nav>
    </aside>
  );
}
