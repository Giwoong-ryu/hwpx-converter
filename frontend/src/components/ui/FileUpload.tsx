"use client";

import { useCallback, useRef, useState } from "react";
import { Upload, FileCheck } from "lucide-react";

interface Props {
  accept?: string;
  multiple?: boolean;
  label?: string;
  onFiles: (files: File[]) => void;
}

export default function FileUpload({ accept, multiple, label, onFiles }: Props) {
  const ref = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [names, setNames] = useState<string[]>([]);

  const handle = useCallback(
    (files: FileList | null) => {
      if (!files) return;
      const arr = Array.from(files);
      setNames(arr.map((f) => f.name));
      onFiles(arr);
    },
    [onFiles]
  );

  return (
    <div
      className={`border border-[#93C5FD]/400 bg-white rounded-xl p-2.5 text-center cursor-pointer transition-all hover:border-[#1E40AF]/30 hover:bg-[#f4f4f1] ${
        dragging ? "border-[#1E40AF]/40 bg-[#DBEAFE]/10" : ""
      }`}
      onClick={() => ref.current?.click()}
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => { e.preventDefault(); setDragging(false); handle(e.dataTransfer.files); }}
    >
      <input
        ref={ref}
        type="file"
        accept={accept}
        multiple={multiple}
        className="hidden"
        onChange={(e) => handle(e.target.files)}
      />
      {names.length > 0 ? (
        <div className="flex items-center gap-2 justify-center">
          <FileCheck size={18} className="text-emerald-600" />
          <div className="text-sm text-[#1a1c1b]">
            {names.map((n, i) => (
              <span key={i} className="font-medium">{n}{i < names.length - 1 ? ", " : ""}</span>
            ))}
          </div>
        </div>
      ) : (
        <div className="flex flex-col items-center gap-2 py-2">
          <Upload size={20} className="text-[#57423c]/80" />
          <span className="text-xs text-[#57423c]/80">{label || "파일을 여기에 드롭하거나 클릭"}</span>
        </div>
      )}
    </div>
  );
}
