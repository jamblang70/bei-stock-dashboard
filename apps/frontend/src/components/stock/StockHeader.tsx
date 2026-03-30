import type { StockProfile } from "@/types";

interface StockHeaderProps {
  stock: StockProfile;
}

function formatNumber(value: number | null | undefined, decimals = 0): string {
  if (value === null || value === undefined) return "N/A";
  return value.toLocaleString("id-ID", { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
}

function formatVolume(volume: number | null | undefined): string {
  if (volume === null || volume === undefined) return "N/A";
  if (volume >= 1_000_000_000) return `${(volume / 1_000_000_000).toFixed(2)}M lot`;
  if (volume >= 1_000_000) return `${(volume / 1_000_000).toFixed(2)}jt`;
  if (volume >= 1_000) return `${(volume / 1_000).toFixed(1)}rb`;
  return volume.toString();
}

export default function StockHeader({ stock }: StockHeaderProps) {
  // Backend returns price as nested object: stock.price.price, stock.price.change_nominal, etc.
  const priceData = (stock as any).price;
  const lastPrice = priceData?.price ?? priceData?.close ?? stock.last_price ?? null;
  const changeNominal = priceData?.change_nominal ?? stock.change_nominal ?? null;
  const changePct = priceData?.change_pct ?? stock.change_pct ?? null;
  const volume = priceData?.volume ?? stock.volume ?? null;

  const isPositive = (changeNominal ?? 0) >= 0;
  const changeColor = isPositive ? "text-green-600" : "text-red-600";
  const changeBg = isPositive ? "bg-green-50" : "bg-red-50";

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-4">
        {/* Left: identity */}
        <div>
          <div className="flex items-center gap-3">
            <span className="rounded-lg bg-blue-600 px-3 py-1 text-lg font-bold text-white">
              {stock.code}
            </span>
            {stock.sector && (
              <span className="rounded-full bg-gray-100 px-3 py-1 text-xs text-gray-600">
                {stock.sector}
              </span>
            )}
          </div>
          <h1 className="mt-2 text-xl font-semibold text-gray-900">{stock.name}</h1>
          {stock.sub_sector && (
            <p className="mt-0.5 text-sm text-gray-500">{stock.sub_sector}</p>
          )}
        </div>

        {/* Right: price */}
        <div className={`rounded-xl px-5 py-3 text-right ${changeBg}`}>
          <p className="text-3xl font-bold text-gray-900">
            Rp {formatNumber(lastPrice, 0)}
          </p>
          <div className={`mt-1 flex items-center justify-end gap-2 text-sm font-medium ${changeColor}`}>
            <span>
              {isPositive ? "+" : ""}
              {formatNumber(changeNominal, 0)}
            </span>
            <span>
              ({isPositive ? "+" : ""}
              {changePct !== null && changePct !== undefined ? Number(changePct).toFixed(2) : "N/A"}%)
            </span>
          </div>
          <p className="mt-1 text-xs text-gray-500">
            Vol: {formatVolume(volume)}
          </p>
        </div>
      </div>
    </div>
  );
}
