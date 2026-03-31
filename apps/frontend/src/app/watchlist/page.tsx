"use client";

import { useEffect, useState } from "react";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { apiGet } from "@/lib/api";
import type { WatchlistItem } from "@/types";
import WatchlistTable from "@/components/watchlist/WatchlistTable";
import Spinner from "@/components/ui/Spinner";

export default function WatchlistPage() {
  const { data: session, status } = useSession();
  const router = useRouter();

  const [items, setItems] = useState<WatchlistItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (status === "loading") return;
    if (status === "unauthenticated") {
      router.replace("/login");
      return;
    }

    const token = (session as any)?.access_token as string | undefined;
    if (!token) {
      router.replace("/login");
      return;
    }

    setLoading(true);
    setError(null);
    apiGet<{ data: WatchlistItem[]; total: number } | WatchlistItem[]>("/watchlist", {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => {
        // Backend returns { data: [...], total: N }
        const items = Array.isArray(res) ? res : (res as any).data ?? [];
        setItems(items);
      })
      .catch(() => setError("Gagal memuat watchlist. Silakan coba lagi."))
      .finally(() => setLoading(false));
  }, [status, session, router]);

  if (status === "loading" || (status === "authenticated" && loading)) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-dark-bg">
        <Spinner size="lg" />
      </div>
    );
  }

  if (status === "unauthenticated") return null;

  const token = (session as any)?.access_token as string;

  return (
    <div className="min-h-screen bg-dark-bg">
      <header className="border-b border-dark-border bg-dark-surface">
        <div className="mx-auto max-w-7xl px-4 py-4 sm:px-6 lg:px-8">
          <h1 className="text-xl font-bold text-text-primary">Watchlist Saya</h1>
          <p className="text-sm text-text-secondary">
            Pantau saham pilihan Anda
          </p>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        {error && (
          <div className="mb-4 rounded-md bg-red-500/10 border border-red-500/20 p-4 text-sm text-red-400">
            {error}
          </div>
        )}

        {!loading && items.length === 0 && !error ? (
          <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-dark-border bg-dark-surface py-20 text-center">
            <p className="text-lg font-medium text-text-secondary">
              Watchlist kosong
            </p>
            <p className="mt-1 text-sm text-text-muted">
              Tambahkan saham dari halaman profil emiten
            </p>
            <button
              onClick={() => router.push("/dashboard")}
              className="mt-4 rounded-md bg-emerald-500 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-600 transition-colors"
            >
              Lihat Ranking Saham
            </button>
          </div>
        ) : (
          !loading && (
            <WatchlistTable
              items={items}
              token={token}
              onItemsChange={setItems}
            />
          )
        )}
      </main>
    </div>
  );
}
