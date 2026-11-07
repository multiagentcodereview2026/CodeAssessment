"use client";

import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Check, X, RotateCcw } from "lucide-react";

export interface FilterChipOption {
  value: string;
  label: string;
  count?: number;
  icon?: React.ReactNode;
}

export interface FilterChipsProps {
  options: (string | FilterChipOption)[];
  value?: string | string[];
  onChange?: (value: any) => void;
  multiple?: boolean;
  variant?: "indigo" | "emerald" | "warm" | "zinc" | "cyan";
  size?: "xs" | "sm" | "md";
  className?: string;
  label?: string;
  showClear?: boolean;
  onClear?: () => void;
  clearLabel?: string;
}

const springTransition = {
  type: "spring" as const,
  stiffness: 500,
  damping: 30,
  mass: 0.5,
};

export const FilterChips: React.FC<FilterChipsProps> = ({
  options,
  value,
  onChange,
  multiple = false,
  variant = "indigo",
  size = "sm",
  className = "",
  label,
  showClear = false,
  onClear,
  clearLabel = "Clear",
}) => {
  const normalizedOptions: FilterChipOption[] = options.map((opt) =>
    typeof opt === "string" ? { value: opt, label: opt } : opt
  );

  const isSelected = (optVal: string) => {
    if (multiple) {
      return Array.isArray(value) && value.includes(optVal);
    }
    return value === optVal;
  };

  const handleToggle = (optVal: string) => {
    if (!onChange) return;
    if (multiple) {
      const arr = Array.isArray(value) ? [...value] : [];
      const idx = arr.indexOf(optVal);
      if (idx > -1) {
        arr.splice(idx, 1);
      } else {
        arr.push(optVal);
      }
      onChange(arr);
    } else {
      onChange(optVal);
    }
  };

  // Color theme definitions
  const themeStyles = {
    indigo: {
      active:
        "bg-indigo-500/15 text-indigo-600 dark:text-indigo-300 ring-1 ring-indigo-500/30 dark:ring-indigo-400/40 shadow-xs",
      activeBg: "rgba(99, 102, 241, 0.15)",
      activeHoverBg: "rgba(99, 102, 241, 0.22)",
      activeTapBg: "rgba(99, 102, 241, 0.28)",
      checkBg: "bg-indigo-600 dark:bg-indigo-400",
      checkIcon: "text-white dark:text-indigo-950",
      inactive:
        "bg-slate-100/80 dark:bg-slate-800/60 text-slate-600 dark:text-slate-300 ring-1 ring-slate-200 dark:ring-slate-700/60 hover:text-slate-900 dark:hover:text-white",
      inactiveBg: "rgba(148, 163, 184, 0.12)",
      inactiveHoverBg: "rgba(148, 163, 184, 0.22)",
      inactiveTapBg: "rgba(148, 163, 184, 0.28)",
    },
    emerald: {
      active:
        "bg-emerald-500/15 text-emerald-600 dark:text-emerald-300 ring-1 ring-emerald-500/30 dark:ring-emerald-400/40 shadow-xs",
      activeBg: "rgba(16, 185, 129, 0.15)",
      activeHoverBg: "rgba(16, 185, 129, 0.22)",
      activeTapBg: "rgba(16, 185, 129, 0.28)",
      checkBg: "bg-emerald-600 dark:bg-emerald-400",
      checkIcon: "text-white dark:text-emerald-950",
      inactive:
        "bg-slate-100/80 dark:bg-slate-800/60 text-slate-600 dark:text-slate-300 ring-1 ring-slate-200 dark:ring-slate-700/60 hover:text-slate-900 dark:hover:text-white",
      inactiveBg: "rgba(148, 163, 184, 0.12)",
      inactiveHoverBg: "rgba(148, 163, 184, 0.22)",
      inactiveTapBg: "rgba(148, 163, 184, 0.28)",
    },
    warm: {
      active:
        "bg-[#2a1711] text-[#ff9066] ring-1 ring-[#ff9066]/30 shadow-xs",
      activeBg: "#2a1711",
      activeHoverBg: "#331c15",
      activeTapBg: "#1f1209",
      checkBg: "bg-[#ff9066]",
      checkIcon: "text-[#2a1711]",
      inactive:
        "bg-zinc-800/50 text-zinc-400 ring-1 ring-white/10 hover:text-zinc-200",
      inactiveBg: "rgba(39, 39, 42, 0.5)",
      inactiveHoverBg: "rgba(39, 39, 42, 0.8)",
      inactiveTapBg: "rgba(39, 39, 42, 0.9)",
    },
    zinc: {
      active:
        "bg-slate-900 text-white dark:bg-white dark:text-slate-950 ring-1 ring-slate-900 dark:ring-white shadow-xs",
      activeBg: "rgba(15, 23, 42, 0.95)",
      activeHoverBg: "rgba(15, 23, 42, 1)",
      activeTapBg: "rgba(15, 23, 42, 0.85)",
      checkBg: "bg-white text-slate-900 dark:bg-slate-950 dark:text-white",
      checkIcon: "text-slate-900 dark:text-white",
      inactive:
        "bg-slate-100/80 dark:bg-slate-800/60 text-slate-600 dark:text-slate-400 ring-1 ring-slate-200 dark:ring-slate-700/60 hover:text-slate-900 dark:hover:text-white",
      inactiveBg: "rgba(148, 163, 184, 0.12)",
      inactiveHoverBg: "rgba(148, 163, 184, 0.2)",
      inactiveTapBg: "rgba(148, 163, 184, 0.25)",
    },
    cyan: {
      active:
        "bg-cyan-500/15 text-cyan-600 dark:text-cyan-300 ring-1 ring-cyan-500/30 dark:ring-cyan-400/40 shadow-xs",
      activeBg: "rgba(6, 182, 212, 0.15)",
      activeHoverBg: "rgba(6, 182, 212, 0.22)",
      activeTapBg: "rgba(6, 182, 212, 0.28)",
      checkBg: "bg-cyan-600 dark:bg-cyan-400",
      checkIcon: "text-white dark:text-cyan-950",
      inactive:
        "bg-slate-100/80 dark:bg-slate-800/60 text-slate-600 dark:text-slate-300 ring-1 ring-slate-200 dark:ring-slate-700/60 hover:text-slate-900 dark:hover:text-white",
      inactiveBg: "rgba(148, 163, 184, 0.12)",
      inactiveHoverBg: "rgba(148, 163, 184, 0.22)",
      inactiveTapBg: "rgba(148, 163, 184, 0.28)",
    },
  }[variant];

  const sizeStyles = {
    xs: {
      button: "px-2.5 py-1 text-[11px] gap-1",
      checkContainer: "w-3.5 h-3.5",
      checkIcon: "w-2.5 h-2.5",
      paddingRight: "1.1rem",
    },
    sm: {
      button: "px-3 py-1.5 text-xs gap-1.5",
      checkContainer: "w-4 h-4",
      checkIcon: "w-3 h-3",
      paddingRight: "1.35rem",
    },
    md: {
      button: "px-4 py-2 text-sm gap-2",
      checkContainer: "w-4.5 h-4.5",
      checkIcon: "w-3.5 h-3.5",
      paddingRight: "1.6rem",
    },
  }[size];

  const hasSelection = multiple
    ? Array.isArray(value) && value.length > 0
    : value !== undefined && value !== "all" && value !== "";

  return (
    <div className={`flex flex-wrap items-center gap-2 ${className}`}>
      {label && (
        <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 whitespace-nowrap mr-1">
          {label}
        </span>
      )}

      <motion.div
        className="flex flex-wrap items-center gap-1.5 overflow-visible"
        layout
        transition={springTransition}
      >
        {normalizedOptions.map((opt) => {
          const selected = isSelected(opt.value);

          return (
            <motion.button
              key={opt.value}
              type="button"
              onClick={() => handleToggle(opt.value)}
              layout
              initial={false}
              animate={{
                backgroundColor: selected ? themeStyles.activeBg : themeStyles.inactiveBg,
              }}
              whileHover={{
                backgroundColor: selected
                  ? themeStyles.activeHoverBg
                  : themeStyles.inactiveHoverBg,
              }}
              whileTap={{
                backgroundColor: selected
                  ? themeStyles.activeTapBg
                  : themeStyles.inactiveTapBg,
              }}
              transition={{
                type: "spring",
                stiffness: 500,
                damping: 30,
                mass: 0.5,
                backgroundColor: { duration: 0.1 },
              }}
              className={`
                inline-flex items-center rounded-full font-medium
                whitespace-nowrap overflow-hidden transition-shadow cursor-pointer
                ${sizeStyles.button}
                ${selected ? themeStyles.active : themeStyles.inactive}
              `}
            >
              <motion.div
                className="relative flex items-center gap-1.5"
                animate={{
                  width: selected ? "auto" : "100%",
                  paddingRight: selected ? sizeStyles.paddingRight : "0",
                }}
                transition={{
                  ease: [0.175, 0.885, 0.32, 1.275],
                  duration: 0.3,
                }}
              >
                {opt.icon && <span className="shrink-0">{opt.icon}</span>}
                <span className="truncate">{opt.label}</span>
                {opt.count !== undefined && (
                  <span
                    className={`ml-0.5 rounded-full px-1.5 py-0.2 text-[10px] font-mono leading-none ${
                      selected
                        ? "bg-white/20 dark:bg-black/20 text-current"
                        : "bg-slate-200/70 dark:bg-slate-700/70 text-slate-600 dark:text-slate-400"
                    }`}
                  >
                    {opt.count}
                  </span>
                )}
                <AnimatePresence>
                  {selected && (
                    <motion.span
                      initial={{ scale: 0, opacity: 0 }}
                      animate={{ scale: 1, opacity: 1 }}
                      exit={{ scale: 0, opacity: 0 }}
                      transition={{
                        type: "spring",
                        stiffness: 500,
                        damping: 30,
                        mass: 0.5,
                      }}
                      className="absolute right-0 flex items-center justify-center"
                    >
                      <div
                        className={`${sizeStyles.checkContainer} rounded-full ${themeStyles.checkBg} flex items-center justify-center`}
                      >
                        <Check
                          className={`${sizeStyles.checkIcon} ${themeStyles.checkIcon}`}
                          strokeWidth={2}
                        />
                      </div>
                    </motion.span>
                  )}
                </AnimatePresence>
              </motion.div>
            </motion.button>
          );
        })}

        {/* Clear filter button */}
        <AnimatePresence>
          {showClear && hasSelection && onClear && (
            <motion.button
              type="button"
              onClick={onClear}
              initial={{ scale: 0.8, opacity: 0, width: 0 }}
              animate={{ scale: 1, opacity: 1, width: "auto" }}
              exit={{ scale: 0.8, opacity: 0, width: 0 }}
              transition={springTransition}
              className="inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-[11px] font-semibold text-rose-600 dark:text-rose-400 bg-rose-50 dark:bg-rose-950/40 hover:bg-rose-100 dark:hover:bg-rose-900/40 ring-1 ring-rose-200 dark:ring-rose-800/40 transition-colors cursor-pointer overflow-hidden whitespace-nowrap ml-1"
            >
              <RotateCcw className="w-3 h-3 shrink-0" />
              <span>{clearLabel}</span>
            </motion.button>
          )}
        </AnimatePresence>
      </motion.div>
    </div>
  );
};

export default FilterChips;
