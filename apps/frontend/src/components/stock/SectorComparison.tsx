type Direction = "better" | "worse" | "neutral";

interface CompareRowProps {
  label: string;
  stockValue: number | null;
  sectorValue: number | null;
  lowerIsBetter?: boolean;
  suffix?: string;
  decimals?: number;
}

function getDirection(stock: number | null, sector: number | null, lowerIsBetter: boolean): Direction {
  if (stock === null || sector === null) return "neutral";
  if (lowerIsBetter) return stock < sector ? "better" : stock > sector ? "worse" : "neutral";
  return stock > sector ? "better" : stock < sector ? "worse" : "neutral";
}

function directionStyle(dir: Direction): { dot: string; text: string } {
  switch (dir) {
    case "better": return { dot: "bg-green-500", text: "text-green-700" };
    case "worse": return { dot: "bg-red-500", text: "text-red-700" };
    default: return { dot: "bg-gray-400", text: "text-gray-600" };
  }
}

function fmt(value: number | null | undefined, decimals = 2, suffix = ""): string {
  if (value === null || value === undefined) return "N/A";
  return `${value.toFixed(decimals)}${suffix}`;
}

function CompareRow({ label, stockValue, sectorValue, lowerIsBetter = false, suffix = "x", decimals = 2 }: CompareRowProps) {
  const dir = getDirection(stockValue, sectorValue, lowerIsBetter);
  const style = directionStyle(dir);
  return (
    <div className="flex items-center justify-between py-2.5 text-sm">
      <div className="flex items-center gap-2">
        <span className={`h-2 w-2 shrink-0 rounded-full ${style.dot}`} aria-hidden="true" />
        <span className="text-gray-600">{label}</span>
      </div>
      <div className="flex items-center gap-4 text-right">
        <div>
          <p className="text-xs text-gray-400">Emiten</p>
          <p className={`font-semibold ${stockValue === null ? "text-gray-400" : style.text}`}>
            {fmt(stockValue, decimals, suffix)}
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-400">Median Sektor</p>
          <p className={`font-medium ${sectorValue === null ? "text-gray-400" : "text-gray-700"}`}>
            {fmt(sectorValue, decimals, suffix)}
          </p>
        </div>
      </div>
    </div>
  );
}

export default function SectorComparison({ data }: { data: any }) {
  if (!data) {
    return (
      <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
        <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-gray-500">Perbandingan Sektor</h2>
        <p className="text-sm text-gray-400">Data sektor tidak cukup untuk perbandingan</p>
      </div>
    );
  }

  // Backend: { emiten: {per, pbv, roe, div_yield}, sektor: {median_per,...}, indicators: {...} }
  const stockPer = data.emiten?.per ?? data.stock_per ?? null;
  const stockPbv = data.emiten?.pbv ?? data.stock_pbv ?? null;
  const stockRoe = data.emiten?.roe ?? data.stock_roe ?? null;
  const stockDiv = data.emiten?.div_yield ?? data.stock_dividend_yield ?? null;
  const sectorPer = data.sektor?.median_per ?? data.sector_median_per ?? null;
  const sectorPbv = data.sektor?.median_pbv ?? data.sector_median_pbv ?? null;
  const sectorRoe = data.sektor?.median_roe ?? data.sector_median_roe ?? null;
  const sectorDiv = data.sektor?.median_div_yield ?? data.sector_median_dividend_yield ?? null;
  const stockCount = data.sektor?.stock_count ?? data.stock_count ?? null;

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-gray-500">Perbandingan Sektor</h2>
      </div>
      <div className="mb-3 flex gap-4 text-xs text-gray-500">
        <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-green-500" /> Lebih baik</span>
        <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-red-500" /> Lebih buruk</span>
        <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-gray-400" /> Netral</span>
      </div>
      <div className="divide-y divide-gray-100">
        <CompareRow label="PER" stockValue={stockPer} sectorValue={sectorPer} lowerIsBetter suffix="x" />
        <CompareRow label="PBV" stockValue={stockPbv} sectorValue={sectorPbv} lowerIsBetter suffix="x" />
        <CompareRow label="ROE" stockValue={stockRoe} sectorValue={sectorRoe} lowerIsBetter={false} suffix="%" />
        <CompareRow label="Dividend Yield" stockValue={stockDiv} sectorValue={sectorDiv} lowerIsBetter={false} suffix="%" />
      </div>
      {stockCount && (
        <p className="mt-3 text-xs text-gray-400">Berdasarkan {stockCount} emiten di sektor yang sama</p>
      )}
    </div>
  );
}
