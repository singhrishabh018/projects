import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium",
  {
    variants: {
      variant: {
        default: "border-emerald-500/30 bg-emerald-500/10 text-emerald-400",
        outline: "border-white/15 text-white/70",
        amber: "border-amber-500/30 bg-amber-500/10 text-amber-400",
        blue: "border-blue-500/30 bg-blue-500/10 text-blue-400",
        red: "border-red-500/30 bg-red-500/10 text-red-400",
      },
    },
    defaultVariants: { variant: "default" },
  },
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, ...props }: BadgeProps) {
  return <span className={cn(badgeVariants({ variant }), className)} {...props} />;
}
