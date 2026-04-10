"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import { listGalleryForms, toggleGalleryLike, deleteGalleryForm, type GalleryForm } from "@/lib/api";
import {
  FileText, Heart, Download, Search, ChevronLeft,
  Loader2, Sparkles, Trash2,
} from "lucide-react";
import LoginModal from "@/components/ui/LoginModal";

const CATEGORIES = [
  { id: "", label: "전체" },
  { id: "사업계획서", label: "사업계획서" },
  { id: "이력서", label: "이력서" },
  { id: "견적서", label: "견적서" },
  { id: "보고서", label: "보고서" },
  { id: "계약서", label: "계약서" },
  { id: "공문", label: "공문" },
  { id: "회의록", label: "회의록" },
  { id: "수료증", label: "수료증" },
  { id: "기타", label: "기타" },
];

const SORTS = [
  { id: "popular", label: "인기순" },
  { id: "recent", label: "최신순" },
  { id: "downloads", label: "다운로드순" },
];

function timeAgo(dateStr: string) {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return `${mins}분 전`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}시간 전`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `${days}일 전`;
  return `${Math.floor(days / 30)}개월 전`;
}

const CATEGORY_COLORS: Record<string, string> = {
  "사업계획서": "bg-blue-100 text-blue-700",
  "이력서": "bg-emerald-100 text-emerald-700",
  "견적서": "bg-amber-100 text-amber-700",
  "보고서": "bg-purple-100 text-purple-700",
  "계약서": "bg-red-100 text-red-700",
  "공문": "bg-gray-100 text-gray-700",
  "회의록": "bg-cyan-100 text-cyan-700",
  "수료증": "bg-pink-100 text-pink-700",
  "기타": "bg-gray-100 text-gray-600",
};

export default function GalleryPage() {
  const { user } = useAuth();
  const [forms, setForms] = useState<GalleryForm[]>([]);
  const [loading, setLoading] = useState(true);
  const [category, setCategory] = useState("");
  const [sort, setSort] = useState("popular");
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(1);
  const [showLogin, setShowLogin] = useState(false);

  const fetchForms = async () => {
    setLoading(true);
    try {
      const res = await listGalleryForms({
        category: category || undefined,
        sort,
        q: query || undefined,
        page,
      });
      setForms(res.forms || []);
    } catch {
      setForms([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchForms();
  }, [category, sort, page]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchForms();
  };

  const handleLike = async (formId: number) => {
    if (!user) {
      setShowLogin(true);
      return;
    }
    try {
      const res = await toggleGalleryLike(formId);
      setForms((prev) =>
        prev.map((f) =>
          f.id === formId ? { ...f, likes: res.likes, liked: res.liked } : f
        )
      );
    } catch { /* ignore */ }
  };

  const handleUseForm = (formId: number) => {
    if (!user) {
      setShowLogin(true);
      return;
    }
    window.location.href = `/tool?gallery_id=${formId}`;
  };

  const handleDelete = async (formId: number) => {
    if (!confirm("이 양식을 삭제하시겠습니까?")) return;
    try {
      await deleteGalleryForm(formId);
      setForms((prev) => prev.filter((f) => f.id !== formId));
    } catch {
      alert("삭제에 실패했습니다.");
    }
  };

  return (
    <div className="min-h-screen bg-[#f9f9f6]">
      {/* 헤더 */}
      <header className="sticky top-0 z-50 bg-[#f9f9f6]/80 backdrop-blur-xl border-b border-[#93C5FD]/50">
        <div className="max-w-screen-xl mx-auto px-6 lg:px-10 py-3.5 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/" className="flex items-center gap-1 text-[#57423c] hover:text-[#1E40AF] transition-colors">
              <ChevronLeft size={16} />
            </Link>
            <Link href="/" className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-lg bg-[#1a1c1b] flex items-center justify-center">
                <FileText size={14} className="text-white" strokeWidth={2.2} />
              </div>
              <span className="text-lg font-extrabold tracking-tighter text-[#1a1c1b]">Eazy HWPX</span>
            </Link>
            <span className="text-sm font-bold text-[#1a1c1b]">양식 갤러리</span>
          </div>
          <div className="flex items-center gap-3">
            <Link
              href="/tool"
              className="text-sm font-semibold text-[#2563EB] hover:text-[#1E40AF] transition-colors"
            >
              도구로 이동
            </Link>
          </div>
        </div>
      </header>

      <div className="max-w-screen-xl mx-auto px-6 lg:px-10 py-8">
        {/* 타이틀 */}
        <div className="mb-8">
          <h1 className="text-2xl font-extrabold text-[#1a1c1b] mb-2">
            다른 사람들이 쓰는 양식, 바로 사용하세요
          </h1>
          <p className="text-base text-[#57423c]">
            양식 구하러 돌아다닐 필요 없이, 여기서 선택하면 AI가 채워드립니다
          </p>
        </div>

        {/* 검색 + 필터 */}
        <div className="flex flex-col sm:flex-row gap-3 mb-6">
          <form onSubmit={handleSearch} className="flex-1 relative">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#57423c]/60" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="양식 검색..."
              className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-[#93C5FD]/40 bg-white text-sm focus:outline-none focus:border-[#2563EB]/50 transition-colors"
            />
          </form>
          <div className="flex gap-2">
            {SORTS.map((s) => (
              <button
                key={s.id}
                onClick={() => { setSort(s.id); setPage(1); }}
                className={`px-3 py-2 rounded-xl text-xs font-semibold transition-colors ${
                  sort === s.id
                    ? "bg-[#1a1c1b] text-white"
                    : "bg-white border border-[#93C5FD]/40 text-[#57423c] hover:bg-[#f4f4f1]"
                }`}
              >
                {s.label}
              </button>
            ))}
          </div>
        </div>

        {/* 카테고리 */}
        <div className="flex flex-wrap gap-2 mb-6">
          {CATEGORIES.map((c) => (
            <button
              key={c.id}
              onClick={() => { setCategory(c.id); setPage(1); }}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                category === c.id
                  ? "bg-[#2563EB] text-white"
                  : "bg-white border border-[#93C5FD]/30 text-[#57423c] hover:bg-[#DBEAFE]/50"
              }`}
            >
              {c.label}
            </button>
          ))}
        </div>

        {/* 양식 목록 */}
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 size={24} className="animate-spin text-[#2563EB]" />
          </div>
        ) : forms.length === 0 ? (
          <div className="text-center py-20">
            <FileText size={40} className="mx-auto text-[#57423c]/40 mb-3" />
            <p className="text-base text-[#57423c]/50">아직 공유된 양식이 없습니다</p>
            <Link href="/tool" className="text-sm text-[#2563EB] hover:underline mt-2 inline-block">
              첫 번째 양식을 공유해보세요
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {forms.map((form) => (
              <div
                key={form.id}
                className="bg-white rounded-2xl border border-[#93C5FD]/30 p-5 hover:border-[#2563EB]/40 hover:shadow-md transition-all group"
              >
                {/* 카테고리 + 시간 + 삭제 */}
                <div className="flex items-center justify-between mb-3">
                  <span className={`text-xs font-bold px-2 py-0.5 rounded-md ${
                    CATEGORY_COLORS[form.category] || CATEGORY_COLORS["기타"]
                  }`}>
                    {form.category}
                  </span>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-[#57423c]/60">{timeAgo(form.created_at)}</span>
                    {user && form.user_id === user.user_id && (
                      <button
                        onClick={() => handleDelete(form.id)}
                        className="text-[#57423c]/50 hover:text-red-500 transition-colors"
                        title="삭제"
                      >
                        <Trash2 size={13} />
                      </button>
                    )}
                  </div>
                </div>

                {/* 제목 */}
                <h3 className="text-sm font-bold text-[#1a1c1b] mb-1 line-clamp-2 group-hover:text-[#2563EB] transition-colors">
                  {form.title}
                </h3>

                {/* 필드 수 */}
                <p className="text-sm text-[#57423c]/50 mb-4">
                  {form.field_count}개 필드
                  {form.doc_type && form.doc_type !== form.category ? ` · ${form.doc_type}` : ""}
                </p>

                {/* 좋아요 + 다운로드 + CTA */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <button
                      onClick={() => handleLike(form.id)}
                      className={`flex items-center gap-1 text-xs transition-colors ${
                        form.liked ? "text-red-500" : "text-[#57423c]/60 hover:text-red-400"
                      }`}
                    >
                      <Heart size={14} fill={form.liked ? "currentColor" : "none"} />
                      {form.likes}
                    </button>
                    <span className="flex items-center gap-1 text-xs text-[#57423c]/60">
                      <Download size={12} /> {form.downloads}
                    </span>
                  </div>
                  <button
                    onClick={() => handleUseForm(form.id)}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-gradient-to-r from-[#2563EB] to-[#1E40AF] text-white text-xs font-bold hover:opacity-90 transition-opacity"
                  >
                    <Sparkles size={12} /> 바로 사용
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* 페이지네이션 */}
        {forms.length >= 20 && (
          <div className="flex justify-center mt-8 gap-2">
            {page > 1 && (
              <button
                onClick={() => setPage(page - 1)}
                className="px-4 py-2 rounded-xl text-sm font-semibold bg-white border border-[#93C5FD]/40 text-[#57423c] hover:bg-[#f4f4f1]"
              >
                이전
              </button>
            )}
            <button
              onClick={() => setPage(page + 1)}
              className="px-4 py-2 rounded-xl text-sm font-semibold bg-white border border-[#93C5FD]/40 text-[#57423c] hover:bg-[#f4f4f1]"
            >
              다음
            </button>
          </div>
        )}
      </div>

      {/* 로그인 모달 */}
      {showLogin && <LoginModal onClose={() => setShowLogin(false)} />}
    </div>
  );
}
