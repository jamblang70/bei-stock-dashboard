"use client";

import { useRouter } from "next/navigation";
import type { Stock } from "@/types";

interface SearchResultsProps {
  results: Stock[];
  query: string;
  onClose: () => void;
}

export default function SearchResults({ results, query, onClose }: SearchResultsProps) {
  const router = useRouter();

  const handleSelect = (code: string) => {
    router.push(`/stock/${code}`);
    onClose();
  };

  if (!query) return null;

  return (
    <ul
      role="listbox"
      className="absolute top-full left-0 right-0 z-50 mt-1 max-h-80 overflow-y-auto rounded-lg border border-dark-border bg-dark-surface shadow-2xl shadow-black/50"
    >
      {results.length === 0 ? (
        <li className="px-4 py-3 text-sm text-text-muted">Saham tidak ditemukan</li>
      ) : (
        results.map((stock) => (
          <li key={stock.code}>
            <button
              role="option"
              aria-selected={false}
              onClick={() => handleSelect(stock.code)}
              className="flex w-full items-center gap-3 px-4 py-3 text-left text-sm hover:bg-dark-hover focus:bg-dark-hover focus:outline-none transition-colors"
            >
              <span className="min-w-[56px] rounded bg-emerald-500/20 px-2 py-0.5 text-xs font-semibold text-emerald-400">
                {stock.code}
              </span>
              <span className="flex-1 truncate text-text-primary">{stock.name}</span>
              {stock.sector && (
                <span className="truncate text-xs text-text-muted">{stock.sector}</span>
              )}
            </button>
          </li>
        ))
      )}
    </ul>
  );
}
