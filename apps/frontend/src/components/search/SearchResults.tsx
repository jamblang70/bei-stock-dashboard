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
      className="absolute top-full left-0 right-0 z-50 mt-1 max-h-80 overflow-y-auto rounded-lg border border-gray-200 bg-white shadow-lg"
    >
      {results.length === 0 ? (
        <li className="px-4 py-3 text-sm text-gray-500">Saham tidak ditemukan</li>
      ) : (
        results.map((stock) => (
          <li key={stock.code}>
            <button
              role="option"
              aria-selected={false}
              onClick={() => handleSelect(stock.code)}
              className="flex w-full items-center gap-3 px-4 py-3 text-left text-sm hover:bg-gray-50 focus:bg-gray-50 focus:outline-none"
            >
              <span className="min-w-[56px] rounded bg-blue-100 px-2 py-0.5 text-xs font-semibold text-blue-800">
                {stock.code}
              </span>
              <span className="flex-1 truncate text-gray-900">{stock.name}</span>
              {stock.sector && (
                <span className="truncate text-xs text-gray-400">{stock.sector}</span>
              )}
            </button>
          </li>
        ))
      )}
    </ul>
  );
}
