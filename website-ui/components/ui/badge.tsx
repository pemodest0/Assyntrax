import * as React from "react";

type BadgeProps = React.HTMLAttributes<HTMLSpanElement> & {
  variant?: "secondary" | "outline" | "destructive";
};

const styles: Record<string, string> = {
  secondary: "bg-gray-100 text-gray-800 border border-gray-200",
  outline: "border border-gray-300 text-gray-700",
  destructive: "bg-red-600 text-white",
};

export function Badge({ className = "", variant = "secondary", ...props }: BadgeProps) {
  const base = "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium";
  return <span className={`${base} ${styles[variant]} ${className}`} {...props} />;
}
