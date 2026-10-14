import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "../api/client";
import { Button, Card, ErrorText, Spinner } from "../components/ui";
import { useI18n } from "../i18n";
import type { LibraryFolder } from "../types";

export default function LibraryPage() {
  const queryClient = useQueryClient();
  const { t } = useI18n();
  const [folderId, setFolderId] = useState<number | null>(null);
  const [search, setSearch] = useState("");
  const [newFolderName, setNewFolderName] = useState("");
  const [rename, setRename] = useState("");
  const [folderParent, setFolderParent] = useState<string | null>(null);
  const [renamingMaterialId, setRenamingMaterialId] = useState<number | null>(null);
  const [materialTitle, setMaterialTitle] = useState("");
  const [error, setError] = useState("");

  const materials = useQuery({ queryKey: ["materials"], queryFn: api.listMaterials });
  const folders = useQuery({ queryKey: ["folders"], queryFn: api.listFolders });

  const refreshLibrary = () => {
    void queryClient.invalidateQueries({ queryKey: ["materials"] });
    void queryClient.invalidateQueries({ queryKey: ["folders"] });
  };
  const createFolder = useMutation({
    mutationFn: () => api.createFolder(newFolderName, folderId),
    onSuccess: () => {
      setNewFolderName("");
      setError("");
      refreshLibrary();
    },
    onError: (cause: Error) => setError(cause.message),
  });
  const updateFolder = useMutation({
    mutationFn: (payload: { id: number; name?: string; parent_id?: number | null }) =>
      api.updateFolder(payload.id, { name: payload.name, parent_id: payload.parent_id }),
    onSuccess: () => {
      setRename("");
      setFolderParent(null);
      setError("");
      refreshLibrary();
    },
    onError: (cause: Error) => setError(cause.message),
  });
  const deleteFolder = useMutation({
    mutationFn: api.deleteFolder,
    onSuccess: () => {
      setFolderId(null);
      setError("");
      refreshLibrary();
    },
    onError: (cause: Error) => setError(cause.message),
  });
  const moveMaterial = useMutation({
    mutationFn: ({ id, target }: { id: number; target: number | null }) =>
      api.moveMaterial(id, target),
    onSuccess: () => refreshLibrary(),
    onError: (cause: Error) => setError(cause.message),
  });
  const renameMaterial = useMutation({
    mutationFn: ({ id, title }: { id: number; title: string }) =>
      api.correctMaterial(id, { title }),
    onSuccess: () => {
      setRenamingMaterialId(null);
      refreshLibrary();
    },
    onError: (cause: Error) => setError(cause.message),
  });
  const removeMaterial = useMutation({
    mutationFn: api.deleteMaterial,
    onSuccess: () => refreshLibrary(),
    onError: (cause: Error) => setError(cause.message),
  });

  const folderById = useMemo(
    () => new Map((folders.data ?? []).map((folder) => [folder.id, folder])),
    [folders.data],
  );
  const currentFolder = folderId === null ? null : folderById.get(folderId) ?? null;
  const descendantIds = new Set<number>();
  if (currentFolder) {
    const pending = [currentFolder.id];
    while (pending.length) {
      const parent = pending.pop()!;
      for (const child of folders.data ?? []) {
        if (child.parent_id === parent && !descendantIds.has(child.id)) {
          descendantIds.add(child.id);
          pending.push(child.id);
        }
      }
    }
  }
  const childFolders = (folders.data ?? []).filter(
    (folder) => folder.parent_id === folderId,
  );
  const breadcrumbs: LibraryFolder[] = [];
  let ancestor = currentFolder;
  while (ancestor) {
    breadcrumbs.unshift(ancestor);
    ancestor = ancestor.parent_id === null ? null : folderById.get(ancestor.parent_id) ?? null;
  }

  const matchingMaterials = (materials.data ?? []).filter((material) => {
    const inFolder = search.trim()
      ? true
      : material.folder_id === folderId;
    const matchesSearch = `${material.title} ${material.filename ?? ""}`
      .toLocaleLowerCase()
      .includes(search.trim().toLocaleLowerCase());
    return inFolder && matchesSearch;
  });

  if (materials.isLoading || folders.isLoading) return <Spinner label="Loading your library…" />;

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">{t("library.title")}</h1>
          <p className="mt-1 text-slate-600">{t("library.subtitle")}</p>
        </div>
        <Link to="/upload">
          <Button>{t("library.upload")}</Button>
        </Link>
      </header>

      <ErrorText>
        {error || (materials.error instanceof Error ? materials.error.message : "") ||
          (folders.error instanceof Error ? folders.error.message : "")}
      </ErrorText>

      <Card className="space-y-4">
        <nav aria-label="Library folders" className="flex flex-wrap items-center gap-2 text-sm">
          <button
            type="button"
            onClick={() => {
              setFolderId(null);
              setFolderParent(null);
            }}
            className="text-indigo-700 hover:underline"
          >
            {t("library.root")}
          </button>
          {breadcrumbs.map((folder) => (
            <span key={folder.id} className="flex items-center gap-2">
              <span aria-hidden="true">/</span>
              <button
                type="button"
                onClick={() => {
                  setFolderId(folder.id);
                  setFolderParent(null);
                }}
                className="text-indigo-700 hover:underline"
              >
                {folder.name}
              </button>
            </span>
          ))}
        </nav>

        <div className="flex flex-wrap gap-2">
          <input
            value={newFolderName}
            onChange={(event) => setNewFolderName(event.target.value)}
            maxLength={120}
            aria-label={t("library.newFolder")}
            placeholder={t("library.newFolder")}
            className="min-h-11 min-w-48 flex-1 rounded-lg border border-slate-300 px-3 text-sm"
          />
          <Button
            variant="secondary"
            disabled={!newFolderName.trim() || createFolder.isPending}
            onClick={() => createFolder.mutate()}
          >
            {t("library.createFolder")}
          </Button>
          {currentFolder && (
            <>
              <input
                value={rename}
                onChange={(event) => setRename(event.target.value)}
                maxLength={120}
                aria-label={t("library.renameFolder")}
                placeholder={currentFolder.name}
                className="min-h-11 min-w-40 rounded-lg border border-slate-300 px-3 text-sm"
              />
              <Button
                variant="secondary"
                disabled={!rename.trim() || updateFolder.isPending}
                onClick={() => updateFolder.mutate({ id: currentFolder.id, name: rename })}
              >
                {t("library.rename")}
              </Button>
              <label className="flex min-h-11 items-center gap-2 text-sm text-slate-600">
                {t("library.moveFolder")}
                <select
                  aria-label="Move current folder"
                  value={folderParent ?? String(currentFolder.parent_id ?? "")}
                  onChange={(event) => setFolderParent(event.target.value)}
                  className="min-h-10 rounded-lg border border-slate-300 bg-white px-2"
                >
                  <option value="">My Library</option>
                  {(folders.data ?? [])
                    .filter(
                      (folder) =>
                        folder.id !== currentFolder.id &&
                        !descendantIds.has(folder.id),
                    )
                    .map((folder) => (
                      <option key={folder.id} value={folder.id}>
                        {folder.name}
                      </option>
                    ))}
                </select>
              </label>
              <Button
                variant="secondary"
                disabled={updateFolder.isPending}
                onClick={() =>
                  updateFolder.mutate({
                    id: currentFolder.id,
                    parent_id:
                      folderParent === null
                        ? currentFolder.parent_id
                        : folderParent
                          ? Number(folderParent)
                          : null,
                  })
                }
              >
                {t("library.move")}
              </Button>
              <Button
                variant="ghost"
                disabled={deleteFolder.isPending}
                onClick={() => deleteFolder.mutate(currentFolder.id)}
              >
                {t("library.deleteFolder")}
              </Button>
            </>
          )}
        </div>
        <p className="text-xs text-slate-500">
          {t("library.emptyHint")}
        </p>
      </Card>

      <div className="flex flex-wrap gap-3">
        <input
          type="search"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          aria-label={t("library.search")}
          placeholder={t("library.search")}
          className="min-h-11 min-w-56 flex-1 rounded-lg border border-slate-300 px-3 text-sm"
        />
      </div>

      {!search.trim() && childFolders.length > 0 && (
        <section aria-label="Subfolders" className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {childFolders.map((folder) => (
            <button
              key={folder.id}
              type="button"
              onClick={() => {
                setFolderId(folder.id);
                setFolderParent(null);
              }}
              className="rounded-xl border border-slate-200 bg-white p-4 text-start shadow-sm hover:border-indigo-300 hover:bg-indigo-50"
            >
              <span aria-hidden="true" className="me-2">📁</span>
              <span className="font-medium">{folder.name}</span>
            </button>
          ))}
        </section>
      )}

      <section className="space-y-3" aria-label="Materials">
        {matchingMaterials.map((material) => (
          <Card key={material.id} className="flex flex-wrap items-center gap-3">
            <div className="min-w-0 flex-1">
              <Link
                to={`/materials/${material.id}`}
                className="block truncate font-medium text-indigo-700 hover:underline"
              >
                {material.title}
              </Link>
              <p className="text-xs text-slate-500">
                {material.source_type.toUpperCase()} · {material.filename ?? "Pasted text"}
                {material.folder_id !== null && search.trim()
                  ? ` · ${folderById.get(material.folder_id)?.name ?? ""}`
                  : ""}
              </p>
              {renamingMaterialId === material.id && (
                <div className="mt-2 flex gap-2">
                  <input
                    value={materialTitle}
                    onChange={(event) => setMaterialTitle(event.target.value)}
                    maxLength={300}
                    aria-label={`${t("library.renameMaterial")}: ${material.title}`}
                    className="min-h-10 min-w-0 flex-1 rounded-lg border border-slate-300 px-2 text-sm"
                  />
                  <Button
                    variant="secondary"
                    disabled={!materialTitle.trim() || renameMaterial.isPending}
                    onClick={() =>
                      renameMaterial.mutate({
                        id: material.id,
                        title: materialTitle.trim(),
                      })
                    }
                  >
                    {t("library.save")}
                  </Button>
                </div>
              )}
              {material.error && <p className="text-xs text-red-600">{material.error}</p>}
            </div>
            <label className="text-sm text-slate-600">
              {t("library.moveMaterial")}
              <select
                aria-label={`Move ${material.title} to folder`}
                value={material.folder_id ?? ""}
                onChange={(event) => {
                  setError("");
                  moveMaterial.mutate({
                    id: material.id,
                    target: event.target.value ? Number(event.target.value) : null,
                  });
                }}
                className="ms-2 min-h-10 rounded-lg border border-slate-300 bg-white px-2"
              >
                <option value="">My Library</option>
                {(folders.data ?? []).map((folder) => (
                  <option key={folder.id} value={folder.id}>
                    {folder.name}
                  </option>
                ))}
              </select>
            </label>
            {renamingMaterialId !== material.id && (
              <Button
                variant="secondary"
                onClick={() => {
                  setRenamingMaterialId(material.id);
                  setMaterialTitle(material.title);
                }}
              >
                {t("library.renameMaterial")}
              </Button>
            )}
            <Button
              variant="ghost"
              disabled={removeMaterial.isPending}
              onClick={() => removeMaterial.mutate(material.id)}
            >
              {t("library.deleteMaterial")}
            </Button>
          </Card>
        ))}
        {!matchingMaterials.length && !childFolders.length && (
          <p className="rounded-xl border border-dashed p-8 text-center text-sm text-slate-500">
            {search ? t("library.noResults") : t("library.empty")}
          </p>
        )}
      </section>
    </div>
  );
}
