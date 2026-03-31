import { useEffect, useState } from "react";
import { X, Database, FileText, Loader2 } from "lucide-react";
import { useChatStore } from "@/store/chatStore";

interface DataSource {
  filename: string;
  type: string;
  table_name?: string;
  created_at?: string;
}

function uuidToInt53(uuid: string): number {
  let hash = 0;
  for (let i = 0; i < uuid.length; i++) {
    hash = (hash << 5) - hash + uuid.charCodeAt(i);
    hash |= 0;
  }
  return Math.abs(hash);
}

const SettingsModal = ({ onClose }: { onClose: () => void }) => {
  const { authUser, currentUser } = useChatStore();
  const [data, setData] = useState<{ csvs: DataSource[]; documents: DataSource[] } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const activeUserId = authUser ? uuidToInt53(authUser.id) : currentUser.id;
  const baseUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";

  useEffect(() => {
    fetch(`${baseUrl}/data-sources?user_id=${activeUserId}`)
      .then((res) => res.json())
      .then((res) => {
        if (res.status === "success") {
          setData(res.data);
        } else {
          setError(res.message);
        }
      })
      .catch((err) => setError("Failed to fetch data sources: " + err.message))
      .finally(() => setLoading(false));
  }, [activeUserId, baseUrl]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-black/60 backdrop-blur-sm">
      <div className="w-full max-w-3xl max-h-[85vh] bg-qm-surface border border-border rounded-2xl shadow-2xl flex flex-col md:flex-row overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        
        {/* Settings Sidebar */}
        <div className="w-full md:w-64 border-b md:border-b-0 md:border-r border-border bg-qm-base p-4">
          <h2 className="text-xl font-bold text-qm-text mb-6">Settings</h2>
          <nav className="flex flex-col gap-1">
            <button className="flex items-center gap-3 px-3 py-2.5 rounded-lg bg-qm-elevated text-qm-text font-medium text-sm transition-colors border-l-4 border-qm-accent">
              <Database size={16} className="text-qm-accent" />
              Data Dashboard
            </button>
            {/* Future settings tabs can go here */}
          </nav>
        </div>

        {/* Settings Content */}
        <div className="flex-1 flex flex-col min-h-0 bg-qm-surface relative">
          <div className="flex items-center justify-between p-6 border-b border-border">
            <div>
              <h3 className="text-lg font-semibold text-qm-text">Your Data Sources</h3>
              <p className="text-sm text-qm-text-sec mt-1">
                View the datasets and documents BizBot is using to answer your questions.
              </p>
            </div>
            <button
              onClick={onClose}
              className="p-2 -mr-2 text-qm-text-muted hover:text-qm-text rounded-full hover:bg-qm-elevated transition-colors"
            >
              <X size={20} />
            </button>
          </div>

          <div className="p-6 overflow-y-auto scrollbar-thin flex-1">
            {loading ? (
              <div className="flex flex-col items-center justify-center h-48 text-qm-text-muted">
                <Loader2 size={24} className="animate-spin mb-3 text-qm-accent" />
                <p className="text-sm">Fetching sources...</p>
              </div>
            ) : error ? (
              <div className="p-4 bg-red-500/10 border border-red-500/20 text-red-500 rounded-xl text-sm">
                {error}
              </div>
            ) : (
              <div className="space-y-8">
                {/* CSV Section */}
                <div>
                  <h4 className="flex items-center gap-2 text-sm font-semibold text-qm-text uppercase tracking-wider mb-3">
                    <Database size={16} className="text-qm-accent" />
                    Structured Databases (SQL)
                  </h4>
                  {data?.csvs.length === 0 ? (
                    <p className="text-sm text-qm-text-sec p-4 bg-qm-base rounded-xl border border-dashed border-border text-center">
                      No databases uploaded yet.
                    </p>
                  ) : (
                    <div className="grid gap-3">
                      {data?.csvs.map((csv, i) => (
                        <div key={i} className="flex items-center justify-between p-4 bg-qm-base border border-border rounded-xl">
                          <div>
                            <p className="text-sm font-medium text-qm-text">{csv.filename}</p>
                            <p className="text-[12px] text-qm-text-muted mt-0.5 font-mono">
                              sys_table: {csv.table_name}
                            </p>
                          </div>
                          <span className="px-2.5 py-1 bg-qm-elevated text-qm-text-sec text-[11px] font-medium rounded-full border border-border">
                            CSV
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Documents Section */}
                <div>
                  <h4 className="flex items-center gap-2 text-sm font-semibold text-qm-text uppercase tracking-wider mb-3">
                    <FileText size={16} className="text-qm-accent" />
                    Knowledge Documents (RAG)
                  </h4>
                  {data?.documents.length === 0 ? (
                    <p className="text-sm text-qm-text-sec p-4 bg-qm-base rounded-xl border border-dashed border-border text-center">
                      No documents uploaded yet.
                    </p>
                  ) : (
                    <div className="grid gap-3">
                      {data?.documents.map((doc, i) => (
                        <div key={i} className="flex items-center justify-between p-4 bg-qm-base border border-border rounded-xl">
                          <p className="text-sm font-medium text-qm-text">{doc.filename}</p>
                          <span className="px-2.5 py-1 bg-qm-elevated text-qm-text-sec text-[11px] font-medium rounded-full border border-border uppercase">
                            {doc.type}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsModal;
