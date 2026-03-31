export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-dark-bg flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-text-primary">BEI Stock Dashboard</h1>
          <p className="text-sm text-text-secondary mt-1">Analisa saham Bursa Efek Indonesia</p>
        </div>
        <div className="bg-dark-surface rounded-2xl border border-dark-border p-8">
          {children}
        </div>
      </div>
    </div>
  );
}
