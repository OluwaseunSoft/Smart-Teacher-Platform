import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "../api/client";
import { Badge, Button, Card, ErrorText, Spinner } from "../components/ui";

export default function MaterialsPage() {
  const qc = useQueryClient();
  const navigate = useNavigate();
  const [tab, setTab] = useState<"file" | "text">("file");
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [text, setText] = useState("");
  const [error, setError] = useState("");

  const materials = useQuery({
    queryKey: ["materials"],
    queryFn: api.listMaterials,
    refetchInterval: (query) =>
      query.state.data?.some((m) => m.status === "processing") ? 2000 : false,
  });

  const create = useMutation({
    mutationFn: async () => {
      if (tab === "file") {
        if (!file) throw new Error("Choose a PDF or text file.");
        return api.uploadFile(file, title || undefined);
      }
      if (!text.trim()) throw new Error("Paste some text first.");
      return api.createTextMaterial(title || "Untitled material", text);
    },
    onSuccess: (material) => {
      setFile(null);
      setTitle("");
      setText("");
      setError("");
      qc.invalidateQueries({ queryKey: ["materials"] });
      navigate(`/materials/${material.id}`);
    },
    onError: (e: Error) => setError(e.message),
  });

  const process = useMutation({
    mutationFn: (id: number) => api.processMaterial(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["materials"] }),
    onError: (e: Error) => setError(e.message),
  });

  const remove = useMutation({
    mutationFn: (id: number) => api.deleteMaterial(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["materials"] }),
  });

  return (
    <div className="space-y-8">
      <section className="space-y-3">
        <h1 className="text-2xl font-semibold">Your study material</h1>
        <p className="text-slate-600">
          Upload a PDF or paste your notes. Suhail reads it, organizes it into
          concepts, and builds lessons to teach you.
        </p>
      </section>

      <Card className="space-y-4">
        <div role="tablist" aria-label="Material source" className="flex gap-2">
          {(["file", "text"] as const).map((t) => (
            <button
              key={t}
              role="tab"
              aria-selected={tab === t}
              onClick={() => setTab(t)}
              className={`rounded-lg px-3 py-1.5 text-sm font-medium ${
                tab === t
                  ? "bg-indigo-600 text-white"
                  : "bg-slate-100 text-slate-600 hover:bg-slate-200"
              }`}
            >
              {t === "file" ? "Upload file" : "Paste text"}
            </button>
          ))}
        </div>

        {tab === "file" ? (
          <div className="space-y-3">
            <input
              type="file"
              accept=".pdf,.txt,.md"
              aria-label="Choose a PDF or text file"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              className="block w-full text-sm text-slate-600 file:me-3 file:rounded-lg file:border-0 file:bg-indigo-50 file:px-4 file:py-2 file:text-sm file:font-medium file:text-indigo-700 hover:file:bg-indigo-100"
            />
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              aria-label="Title (optional)"
              placeholder="Title (optional)"
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-indigo-500"
            />
          </div>
        ) : (
          <div className="space-y-3">
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              aria-label="Title"
              placeholder="Title"
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-indigo-500"
            />
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              rows={7}
              aria-label="Study notes"
              placeholder="Paste your study notes here..."
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-indigo-500"
            />
          </div>
        )}

        <ErrorText>{error}</ErrorText>
        <Button onClick={() => create.mutate()} disabled={create.isPending}>
          {create.isPending ? "Adding..." : "Add material"}
        </Button>
      </Card>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold">Library</h2>
        {materials.isLoading && <Spinner label="Loading..." />}
        {materials.isError && (
          <ErrorText>{(materials.error as Error).message}</ErrorText>
        )}
        {!materials.isLoading &&
          !materials.isError &&
          materials.data?.length === 0 && (
            <p className="text-sm text-slate-500">Nothing here yet.</p>
          )}
        <div className="space-y-3">
          {materials.data?.map((m) => (
            <Card key={m.id} className="flex flex-wrap items-center gap-4">
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <Link
                    to={`/materials/${m.id}`}
                    className="truncate font-medium text-indigo-700 hover:underline"
                  >
                    {m.title}
                  </Link>
                  <Badge value={m.status} />
                </div>
                <p className="text-xs text-slate-500">
                  {m.source_type.toUpperCase()}
                  {m.filename ? ` · ${m.filename}` : ""}
                </p>
                {m.error && <p className="text-xs text-red-600">{m.error}</p>}
              </div>
              <div className="flex gap-2">
                {m.status !== "ready" && m.status !== "processing" && (
                  <Button
                    variant="secondary"
                    onClick={() => process.mutate(m.id)}
                    disabled={process.isPending}
                  >
                    Process
                  </Button>
                )}
                <Button
                  variant="ghost"
                  onClick={() => remove.mutate(m.id)}
                  disabled={remove.isPending}
                >
                  Delete
                </Button>
              </div>
            </Card>
          ))}
        </div>
      </section>
    </div>
  );
}
