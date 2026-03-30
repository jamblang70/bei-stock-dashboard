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
      <div className="flex min-h-screen items-center justify-center bg-gray-50">
        <Spinner size="lg" />
      </div>
    );
  }

  if (status === "unauthenticated") return null;

  const token = (session as any)?.access_token as string;

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="border-b border-gray-200 bg-white shadow-sm">
        <div className="mx-auto max-w-7xl px-4 py-4 sm:px-6 lg:px-8">
          <h1 className="text-xl font-bold text-gray-900">Watchlist Saya</h1>
          <p className="text-sm text-gray-500">
            Pantau saham pilihan Anda
          </p>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        {error && (
          <div className="mb-4 rounded-md bg-red-50 p-4 text-sm text-red-700">
            {error}
          </div>
        )}

        {!loading && items.length === 0 && !error ? (
          <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-gray-300 bg-white py-20 text-center">
            <p className="text-lg font-medium text-gray-500">
              Watchlist kosong
            </p>
            <p className="mt-1 text-sm text-gray-400">
              Tambahkan saham dari halaman profil emiten
            </p>
            <button
              onClick={() => router.push("/dashboard")}
              className="mt-4 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
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
