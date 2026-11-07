"use client";

import React, { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, Check, X, RotateCcw, Search } from "lucide-react";

export interface FilterDropdownOption {
  value: string;
  label: string;
  count?: number;
  icon?: React.ReactNode;
}

export interface FilterDropdownProps {
  label: string;
  placeholder?: string;
  icon?: React.ReactNode;
  options: (string | FilterDropdownOption)[];
  value: string | string[];
  onChange: (value: string[]) => void;
  variant?: "indigo" | "emerald";
  searchable?: boolean;
  searchPlaceholder?: string;
  align?: "left" | "right";
  className?: string;
  dropdownWidth?: string;
}

const springTransition = {
  type: "spring" as const,
  stiffness: 500,
  damping: 30,
  mass: 0.5,
};

export const FilterDropdown: React.FC<FilterDropdownProps> = ({
  label,
  placeholder,
  icon,
  options,
  value,
  onChange,
  variant = "indigo",
  searchable = false,
  searchPlaceholder = "Search options...",
  align = "right",
  className = "",
  dropdownWidth = "w-[min(360px,calc(100vw-2rem))]",
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const dropdownRef = useRef<HTMLDivElement>(null);

  const normalizedOptions: FilterDropdownOption[] = options.map((opt) =>
    typeof opt === "string" ? { value: opt, label: opt } : opt
  );

  // Normalize current selections into an array of strings (excluding "all")
  const selectedValues: string[] = Array.isArray(value)
    ? value.filter((v) => v !== "all" && v !== "")
    : value && value !== "all" && value !== ""
    ? [value]
    : [];

  const isFiltered = selectedValues.length > 0;

  // Close dropdown on click outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
      return () => document.removeEventListener("mousedown", handleClickOutside);
    }
  }, [isOpen]);

  const handleToggle = (optVal: string) => {
    if (optVal === "all") {
      // Clicking "All" resets everything
      onChange([]);
      return;
    }

    if (selectedValues.includes(optVal)) {
      onChange(selectedValues.filter((v) => v !== optVal));
    } else {
      onChange([...selectedValues, optVal]);
    }
    // Note: Do NOT close dropdown on selection so user can select multiple!
  };

  const handleReset = (e?: React.MouseEvent) => {
    e?.stopPropagation();
    onChange([]);
  };

  const filteredOptions = searchable && searchTerm.trim()
    ? normalizedOptions.filter((opt) =>
        opt.label.toLowerCase().includes(searchTerm.toLowerCase())
      )
    : normalizedOptions;

  // Theme palettes
  const theme = {
    indigo: {
      activeTrigger:
        "border-indigo-400 dark:border-indigo-600 bg-indigo-50/80 dark:bg-indigo-950/40 text-indigo-700 dark:text-indigo-300 shadow-2xs font-semibold",
      activeIcon: "text-indigo-600 dark:text-indigo-400",
      activeChip:
        "bg-indigo-600/15 dark:bg-indigo-500/25 text-indigo-700 dark:text-indigo-300 ring-1 ring-indigo-500/40 dark:ring-indigo-400/50 font-semibold",
      activeBg: "rgba(99, 102, 241, 0.15)",
      activeHoverBg: "rgba(99, 102, 241, 0.22)",
      activeTapBg: "rgba(99, 102, 241, 0.28)",
      checkBg: "bg-indigo-600 dark:bg-indigo-400",
      checkIcon: "text-white dark:text-indigo-950",
      headerIcon: "text-indigo-600 dark:text-indigo-400",
      resetText:
        "text-indigo-600 dark:text-indigo-400 hover:text-indigo-800 dark:hover:text-indigo-300 hover:underline",
      focusRing:
        "focus:border-indigo-500 focus:ring-indigo-200 dark:focus:ring-indigo-900/50",
    },
    emerald: {
      activeTrigger:
        "border-emerald-400 dark:border-emerald-600 bg-emerald-50/80 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 shadow-2xs font-semibold",
      activeIcon: "text-emerald-600 dark:text-emerald-400",
      activeChip:
        "bg-emerald-600/15 dark:bg-emerald-500/25 text-emerald-700 dark:text-emerald-300 ring-1 ring-emerald-500/40 dark:ring-emerald-400/50 font-semibold",
      activeBg: "rgba(16, 185, 129, 0.15)",
      activeHoverBg: "rgba(16, 185, 129, 0.22)",
      activeTapBg: "rgba(16, 185, 129, 0.28)",
      checkBg: "bg-emerald-600 dark:bg-emerald-400",
      checkIcon: "text-white dark:text-emerald-950",
      headerIcon: "text-emerald-600 dark:text-emerald-400",
      resetText:
        "text-emerald-600 dark:text-emerald-400 hover:text-emerald-800 dark:hover:text-emerald-300 hover:underline",
      focusRing:
        "focus:border-emerald-500 focus:ring-emerald-200 dark:focus:ring-emerald-900/50",
    },
  }[variant];

  // Determine trigger button label
  const renderTriggerLabel = () => {
    if (selectedValues.length === 0) {
      return placeholder || label;
    }
    if (selectedValues.length === 1) {
      const match = normalizedOptions.find((opt) => opt.value === selectedValues[0]);
      return match ? match.label : selectedValues[0];
    }
    // If 2 or 3 items, try showing their labels if short
    const selectedLabels = selectedValues
      .map((val) => {
        const m = normalizedOptions.find((opt) => opt.value === val);
        return m ? m.label : val;
      })
      .filter(Boolean);

    const joined = selectedLabels.join(", ");
    if (joined.length <= 22) {
      return joined;
    }
    return `${label} (${selectedValues.length})`;
  };

  return (
    <div className={`relative inline-block ${className}`} ref={dropdownRef}>
      {/* Trigger Button */}
      <button
        type="button"
        onClick={() => setIsOpen((prev) => !prev)}
        aria-expanded={isOpen}
        className={`inline-flex h-9 items-center justify-between gap-2 rounded-xl border px-3 text-xs font-medium transition-all cursor-pointer whitespace-nowrap ${
          isFiltered
            ? theme.activeTrigger
            : isOpen
            ? "border-slate-300 dark:border-neutral-700 bg-slate-50 dark:bg-neutral-900 text-slate-800 dark:text-zinc-200 shadow-xs"
            : "border-slate-200 dark:border-neutral-800 bg-white dark:bg-black text-slate-700 dark:text-zinc-300 hover:border-slate-300 dark:hover:border-neutral-700 hover:bg-slate-50 dark:hover:bg-neutral-900/60"
        }`}
      >
        <div className="flex items-center gap-1.5 truncate max-w-[200px]">
          {icon && (
            <span className={`shrink-0 ${isFiltered ? theme.activeIcon : "text-slate-400"}`}>
              {icon}
            </span>
          )}
          <span className="truncate">{renderTriggerLabel()}</span>
          {selectedValues.length > 1 && (
            <span className="rounded-full bg-black/10 dark:bg-white/10 px-1.5 py-0.2 text-[10px] font-mono font-bold">
              {selectedValues.length}
            </span>
          )}
        </div>

        <div className="flex items-center gap-1 shrink-0 ml-1">
          {isFiltered && (
            <span
              role="button"
              tabIndex={0}
              onClick={handleReset}
              className="rounded-full p-0.5 text-slate-400 hover:bg-black/10 dark:hover:bg-white/10 hover:text-slate-600 dark:hover:text-slate-200 transition-colors"
              title="Clear selection"
            >
              <X className="h-3 w-3" />
            </span>
          )}
          <ChevronDown
            className={`h-3.5 w-3.5 text-slate-400 transition-transform duration-200 ${
              isOpen ? "rotate-180" : ""
            }`}
          />
        </div>
      </button>

      {/* Designated Dropdown Box Popover */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 4, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 4, scale: 0.98 }}
            transition={{ duration: 0.15, ease: "easeOut" }}
            className={`absolute ${align === "left" ? "left-0" : "right-0"} top-full z-[70] mt-1.5 ${dropdownWidth} min-w-[280px] max-w-[calc(100vw-2rem)] rounded-2xl border border-slate-200/90 dark:border-neutral-800 bg-white dark:bg-[#0c0c0e] p-3.5 text-slate-800 dark:text-zinc-200 shadow-2xl dark:shadow-black/90`}
          >
            {/* Popover Header with Title, Options Count, Reset, and Close */}
            <div className="flex items-center justify-between pb-2.5 border-b border-slate-100 dark:border-neutral-800">
              <div className="flex items-center gap-1.5">
                {icon && <span className={theme.headerIcon}>{icon}</span>}
                <h3 className="text-xs font-bold text-slate-900 dark:text-white">
                  Filter by {label}
                </h3>
                <span className="rounded-full bg-slate-100 dark:bg-neutral-900 px-1.5 py-0.2 text-[10px] font-semibold text-slate-600 dark:text-zinc-400">
                  {normalizedOptions.length}
                </span>
              </div>
              <div className="flex items-center gap-2.5">
                {isFiltered && (
                  <button
                    type="button"
                    onClick={handleReset}
                    className={`flex items-center gap-1 text-[11px] font-semibold ${theme.resetText} cursor-pointer transition-colors`}
                  >
                    <RotateCcw className="h-2.5 w-2.5" />
                    Reset
                  </button>
                )}
                <button
                  type="button"
                  onClick={() => setIsOpen(false)}
                  aria-label="Close"
                  className="rounded-lg p-1 text-slate-400 hover:bg-slate-100 dark:hover:bg-neutral-800 hover:text-slate-600 dark:hover:text-zinc-300 transition-colors cursor-pointer"
                >
                  <X className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>

            {/* Optional Search Input */}
            {searchable && (
              <div className="relative mt-2.5 mb-2">
                <Search className="absolute left-2.5 top-1/2 h-3 w-3 -translate-y-1/2 text-slate-400 dark:text-zinc-500" />
                <input
                  type="text"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder={searchPlaceholder}
                  className={`w-full rounded-lg border border-slate-200 dark:border-neutral-800 bg-slate-50/80 dark:bg-neutral-900/80 py-1.5 pl-8 pr-7 text-xs text-slate-800 dark:text-zinc-200 placeholder-slate-400 dark:placeholder-zinc-500 focus:bg-white dark:focus:bg-black focus:outline-none focus:ring-1 ${theme.focusRing}`}
                />
                {searchTerm && (
                  <button
                    type="button"
                    onClick={() => setSearchTerm("")}
                    className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-zinc-200 cursor-pointer"
                  >
                    <X className="h-3 w-3" />
                  </button>
                )}
              </div>
            )}

            {/* Animated Chips Container inside the designated dropdown box */}
            <div className="mt-2.5 max-h-56 min-h-[84px] overflow-y-auto pr-1 custom-scrollbar flex flex-col justify-center">
              {filteredOptions.length === 0 ? (
                <motion.div
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ duration: 0.15 }}
                  className="py-5 px-3 text-center flex flex-col items-center justify-center my-auto"
                >
                  <div className="w-8 h-8 rounded-full bg-slate-100 dark:bg-neutral-900 flex items-center justify-center text-slate-400 dark:text-zinc-500 mb-2">
                    <Search className="w-4 h-4" />
                  </div>
                  <p className="text-xs font-semibold text-slate-700 dark:text-zinc-300">
                    No matching {label.toLowerCase()} found
                  </p>
                  <p className="text-[11px] text-slate-400 dark:text-zinc-500 mt-0.5">
                    {searchTerm ? `No results for "${searchTerm}"` : `No options available`}
                  </p>
                  {searchTerm && (
                    <button
                      type="button"
                      onClick={() => setSearchTerm("")}
                      className={`mt-2 inline-flex items-center gap-1 text-[11px] font-semibold ${theme.resetText} hover:underline cursor-pointer`}
                    >
                      <RotateCcw className="h-2.5 w-2.5" />
                      Clear search
                    </button>
                  )}
                </motion.div>
              ) : (
                <motion.div
                  className="flex flex-wrap gap-1.5 overflow-visible"
                  layout
                  transition={springTransition}
                >
                  {filteredOptions.map((opt) => {
                    const isSelected = selectedValues.includes(opt.value);
                    return (
                      <motion.button
                        key={opt.value}
                        type="button"
                        onClick={() => handleToggle(opt.value)}
                        layout
                        initial={false}
                        animate={{
                          backgroundColor: isSelected
                            ? theme.activeBg
                            : "rgba(255, 255, 255, 0.05)",
                        }}
                        whileHover={{
                          backgroundColor: isSelected
                            ? theme.activeHoverBg
                            : "rgba(255, 255, 255, 0.1)",
                        }}
                        whileTap={{
                          backgroundColor: isSelected
                            ? theme.activeTapBg
                            : "rgba(255, 255, 255, 0.15)",
                        }}
                        transition={{
                          type: "spring",
                          stiffness: 500,
                          damping: 30,
                          mass: 0.5,
                          backgroundColor: { duration: 0.1 },
                        }}
                        className={`
                          inline-flex items-center px-3 py-1.5 rounded-full text-xs font-medium
                          whitespace-nowrap overflow-hidden ring-1 ring-inset cursor-pointer transition-shadow
                          ${
                            isSelected
                              ? theme.activeChip
                              : "bg-slate-100/80 dark:bg-white/[0.06] text-slate-600 dark:text-zinc-300 ring-slate-200 dark:ring-white/[0.08] hover:text-slate-900 dark:hover:text-white"
                          }
                        `}
                      >
                        <motion.div
                          className="relative flex items-center gap-1.5"
                          animate={{
                            width: isSelected ? "auto" : "100%",
                            paddingRight: isSelected ? "1.35rem" : "0",
                          }}
                          transition={{
                            ease: [0.175, 0.885, 0.32, 1.275],
                            duration: 0.3,
                          }}
                        >
                          {opt.icon && <span className="shrink-0">{opt.icon}</span>}
                          <span>{opt.label}</span>
                          {opt.count !== undefined && (
                            <span
                              className={`rounded-full px-1.5 py-0.2 text-[10px] font-mono leading-none ${
                                isSelected
                                  ? "bg-white/20 dark:bg-black/20 text-current font-bold"
                                  : "bg-slate-200/70 dark:bg-slate-700/70 text-slate-600 dark:text-slate-400"
                              }`}
                            >
                              {opt.count}
                            </span>
                          )}
                          <AnimatePresence>
                            {isSelected && (
                              <motion.span
                                initial={{ scale: 0, opacity: 0 }}
                                animate={{ scale: 1, opacity: 1 }}
                                exit={{ scale: 0, opacity: 0 }}
                                transition={springTransition}
                                className="absolute right-0 flex items-center justify-center"
                              >
                                <div
                                  className={`w-4 h-4 rounded-full ${theme.checkBg} flex items-center justify-center`}
                                >
                                  <Check
                                    className={`w-3 h-3 ${theme.checkIcon}`}
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
                </motion.div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default FilterDropdown;
