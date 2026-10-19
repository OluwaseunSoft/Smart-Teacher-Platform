import { useState, type ChangeEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { api } from "../api/client";
import { Button, Card, ErrorText } from "../components/ui";
import { useI18n } from "../i18n";

const MAX_UPLOAD_BYTES = 50 * 1024 * 1024;
const MAX_TEXT_CHARACTERS = 100_000;

export default function UploadPage() {
  const { t } = useI18n();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [method, setMethod] = useState<"file" | "text">("file");
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [titleEdited, setTitleEdited] = useState(false);
  const [text, setText] = useState("");
  const [error, setError] = useState("");
  const [uploadProgress, setUploadProgress] = useState<number | null>(null);

  const create = useMutation({
    mutationFn: async () => {
      if (method === "file") {
        if (!file) throw new Error("Choose a PDF, TXT, or Markdown file.");
        if (file.size > MAX_UPLOAD_BYTES) {
          throw new Error("File is too large. The maximum upload size is 50 MB.");
        }
        setUploadProgress(0);
        return api.uploadFile(file, title.trim() || file.name, setUploadProgress);
      }
      if (!text.trim()) throw new Error("Enter some study content first.");
      if (text.length > MAX_TEXT_CHARACTERS) {
        throw new Error("Text is too long. The maximum length is 100,000 characters.");
      }
      return api.createTextMaterial(title.trim() || "Untitled material", text);
    },
    onSuccess: async (material) => {
      await queryClient.invalidateQueries({ queryKey: ["materials"] });
      navigate(`/materials/${material.id}`);
    },
    onError: (cause: Error) => setError(cause.message),
    onSettled: () => setUploadProgress(null),
  });

  function onFileChange(event: ChangeEvent<HTMLInputElement>) {
    const selected = event.target.files?.[0] ?? null;
    setFile(selected);
    setError(
      selected && selected.size > MAX_UPLOAD_BYTES
        ? "File is too large. The maximum upload size is 50 MB."
        : "",
    );
    if (selected && !titleEdited) setTitle(selected.name);
    if (!selected && !titleEdited) setTitle("");
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <Link to="/library" className="text-sm text-indigo-700 hover:underline">
          {t("upload.back")}
        </Link>
        <h1 className="mt-2 text-2xl font-semibold">{t("upload.title")}</h1>
        <p className="mt-1 text-slate-600">{t("upload.subtitle")}</p>
      </div>

      <Card className="space-y-5">
        <div role="tablist" aria-label="Content input method" className="flex gap-2">
          {(["file", "text"] as const).map((value) => (
            <button
              key={value}
              type="button"
              role="tab"
              aria-selected={method === value}
              onClick={() => {
                setMethod(value);
                setError("");
              }}
              className={`min-h-11 rounded-lg px-4 text-sm font-medium ${
                method === value
                  ? "bg-indigo-600 text-white"
                  : "bg-slate-100 text-slate-700 hover:bg-slate-200"
              }`}
            >
              {value === "file" ? t("upload.fileTab") : t("upload.textTab")}
            </button>
          ))}
        </div>

        {method === "file" ? (
          <div className="space-y-3">
            <label htmlFor="content-file" className="block text-sm font-medium">
              {t("upload.fileHelp")}
            </label>
            <input
              id="content-file"
              type="file"
              accept=".pdf,.txt,.md,application/pdf,text/plain,text/markdown"
              onChange={onFileChange}
              className="block w-full rounded-lg border border-slate-300 p-3 text-sm"
            />
            {file && (
              <p className="text-sm text-slate-600">
                {file.name} · {(file.size / (1024 * 1024)).toFixed(2)} MB
              </p>
            )}
          </div>
        ) : (
          <div className="space-y-2">
            <label htmlFor="content-text" className="block text-sm font-medium">
              {t("upload.studyContent")}
            </label>
            <textarea
              id="content-text"
              dir="auto"
              value={text}
              onChange={(event) => {
                setText(event.target.value);
                setError("");
              }}
              rows={10}
              maxLength={MAX_TEXT_CHARACTERS + 1}
              aria-describedby="text-count"
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              placeholder={t("upload.placeholder")}
            />
            <p id="text-count" className="text-end text-xs text-slate-500">
              {t("upload.characters", {
                used: text.length.toLocaleString(),
                maximum: MAX_TEXT_CHARACTERS.toLocaleString(),
              })}
            </p>
            {text.length > MAX_TEXT_CHARACTERS && (
              <p role="alert" className="text-sm text-red-700">
                {t("upload.textLimit")}
              </p>
            )}
          </div>
        )}

        <div className="space-y-1">
          <label htmlFor="content-title" className="block text-sm font-medium">
            {t("upload.titleLabel")}
          </label>
          <input
            id="content-title"
            value={title}
            onChange={(event) => {
              setTitle(event.target.value);
              setTitleEdited(true);
            }}
            maxLength={300}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            placeholder="Enter a title"
          />
        </div>

        <ErrorText>{error}</ErrorText>
        {uploadProgress !== null && create.isPending && (
          <div aria-live="polite" className="space-y-1">
            <p className="text-sm text-slate-600">
              {uploadProgress >= 100
                ? t("upload.reading")
                : t("upload.progress", { n: uploadProgress })}
            </p>
            <progress
              aria-label="File upload progress"
              value={uploadProgress}
              max={100}
              className="w-full accent-indigo-600"
            />
          </div>
        )}
        <Button
          onClick={() => {
            setError("");
            create.mutate();
          }}
          disabled={
            create.isPending ||
            (method === "text" && text.length > MAX_TEXT_CHARACTERS)
          }
        >
          {create.isPending ? t("upload.adding") : t("upload.add")}
        </Button>
      </Card>
    </div>
  );
}
