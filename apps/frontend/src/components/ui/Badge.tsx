import { ReactNode } from "react";

type BadgeVariant = "success" | "info" | "warning" | "danger" | "neutral";

interface BadgeProps {
  variant?: BadgeVariant;
  children: ReactNode;
  className?: string;
}

const variantClasses: Record<BadgeVariant, string> = {
  success: "bg-green-100 text-green-800",
  info: "bg-blue-100 text-blue-800",
  warning: "bg-yellow-100 text-yellow-800",
  danger: "bg-red-100 text-red-800",
  neutral: "bg-gray-100 text-gray-800",
};

export default function Badge({ variant = "neutral", children, className = "" }: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${variantClasses[variant]} ${className}`}
    >
      {children}
    </span>
  );
}

// Helper: konversi score ke variant Badge
export function scoreVariant(score: number): BadgeVariant {
  if (score >= 80) return "success";
  if (score >= 60) return "info";
  if (score >= 40) return "warning";
  return "danger";
}

// Helper: konversi rekomendasi ke variant Badge
export function recommendationVariant(
  recommendation: string | null | undefined
): BadgeVariant {
  switch (recommendation) {
    case "Beli Kuat":
      return "success";
    case "Beli":
      return "info";
    case "Tahan":
      return "warning";
    case "Jual":
      return "danger";
    default:
      return "neutral";
  }
}

// ScoreBadge — convenience wrapper
export function ScoreBadge({ score }: { score: number }) {
  const labels: Record<string, string> = {
    success: "Sangat Baik",
    info: "Baik",
    warning: "Cukup",
    danger: "Perlu Perhatian",
  };
  const variant = scoreVariant(score);
  return <Badge variant={variant}>{labels[variant]}</Badge>;
}
