import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import { motion, HTMLMotionProps } from "motion/react";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface GlassCardProps extends HTMLMotionProps<"div"> {
  variant?: "base" | "active-warm" | "active-cool";
  children: React.ReactNode;
  className?: string;
}

export function GlassCard({
  variant = "base",
  children,
  className,
  ...props
}: GlassCardProps) {
  const variants = {
    base: "bg-white/5 border-white/10 hover:border-white/20 hover:bg-white/10",
    "active-warm": "bg-orange-500/10 border-orange-500/30 shadow-[0_0_30px_-5px_rgba(249,115,22,0.3)]",
    "active-cool": "bg-blue-500/10 border-blue-500/30 shadow-[0_0_30px_-5px_rgba(59,130,246,0.3)]",
  };

  return (
    <motion.div
      className={cn(
        "backdrop-blur-md border rounded-2xl p-6 transition-all duration-300",
        variants[variant],
        className
      )}
      {...props}
    >
      {children}
    </motion.div>
  );
}
