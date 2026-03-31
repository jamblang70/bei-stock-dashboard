"use client";

import { useEffect, useState } from "react";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { apiGet, apiPost } from "@/lib/api";
import type { WatchlistItem } from "@/types";
import axios from "axios";

interface AddToWatchlistButtonProps {
  stockCode: string;
}

export default function AddToWatchlistButton({
  stockCode,
}: AddToWatchlistButtonProps) {
  const { data: session, status } = useSession();
  const router = useRouter();

  const [inWatchlist, setInWatchlist] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [checking, setChecking] = useState(true);

  // Check if stock is already in watchlist
  useEffect(() => {
    if (status !== "authenticated") {
      setChecking(false);
      return;
    }

    const token = (session as any)?.access_token as string | undefined;
    if (!token) {
      setChecking(false);
      return;
    }

    apiGet<WatchlistItem[]>("/watchlist", {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res: any) => {
        const items = Array.isArray(res) ? res : res?.data ?? [];
        setInWatchlist(items.some((item: any) => (item.code ?? item.stock?.code) === stockCode));
      })
      .catch(() => {
        // silently ignore — user can still try to add
      })
      .finally(() => setChecking(false));
  }, [status, session, stockCode]);

  if (status === "loading" || checking) {
    return (
      <button
        disabled
        className="inline-flex items-center gap-2 rounded-md border border-dark-border bg-dark-surface px-4 py-2 text-sm font-medium text-text-muted opacity-60"
      >
        <span className="h-4 w-4 animate-spin rounded-full border-2 border-dark-border border-t-emerald-500" />
        Memuat...
      </button>
    );
  }

  if (status !== "authenticated") {
    return (
      <button
        onClick={() => router.push("/login")}
        className="inline-flex items-center gap-2 rounded-md border border-dark-border bg-dark-surface px-4 py-2 text-sm font-medium text-text-secondary hover:bg-dark-hover hover:text-text-primary transition-colors"
      >
        🔒 Login untuk Watchlist
      </button>
    );
  }

  async function handleAdd() {
    setLoading(true);
    setError(null);
    const token = (session as any)?.access_token as string | undefined;
    try {
      await apiPost(
        "/watchlist",
        { code: stockCode },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setInWatchlist(true);
    } catch (err) {
      if (axios.isAxiosError(err)) {
        if (err.response?.status === 409) {
          setError("Saham sudah ada di watchlist");
          setInWatchlist(true);
        } else if (err.response?.status === 400) {
          const msg =
            err.response.data?.detail ?? "Tidak dapat menambahkan saham";
          setError(msg);
        } else {
          setError("Gagal menambahkan ke watchlist");
        }
      } else {
        setError("Gagal menambahkan ke watchlist");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col items-start gap-1">
      <button
        onClick={inWatchlist ? undefined : handleAdd}
        disabled={loading || inWatchlist}
        className={`inline-flex items-center gap-2 rounded-md px-4 py-2 text-sm font-medium transition-colors ${
          inWatchlist
            ? "cursor-default border border-emerald-500/30 bg-emerald-500/10 text-emerald-400"
            : "border border-emerald-500 bg-emerald-500 text-white hover:bg-emerald-600 disabled:opacity-60"
        }`}
      >
        {loading ? (
          <>
            <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
            Menambahkan...
          </>
        ) : inWatchlist ? (
          "✓ Di Watchlist"
        ) : (
          "+ Tambah ke Watchlist"
        )}
      </button>
      {error && <p className="text-xs text-red-400">{error}</p>}
    </div>
  );
}
