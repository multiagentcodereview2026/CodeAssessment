"use client";

import { cn } from "@/lib/utils";
import Link, { LinkProps } from "next/link";
import React, { useState, createContext, useContext } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Menu, X } from "lucide-react";

export interface Links {
  label: string;
  href?: string;
  icon: React.JSX.Element | React.ReactNode;
  onClick?: (e?: React.MouseEvent) => void;
  active?: boolean;
  badge?: number | string;
}

export interface SidebarContextProps {
  open: boolean;
  setOpen: React.Dispatch<React.SetStateAction<boolean>>;
  animate: boolean;
}

const SidebarContext = createContext<SidebarContextProps | undefined>(
  undefined
);

export const useSidebar = () => {
  const context = useContext(SidebarContext);
  if (!context) {
    throw new Error("useSidebar must be used within a SidebarProvider");
  }
  return context;
};

export const SidebarProvider = ({
  children,
  open: openProp,
  setOpen: setOpenProp,
  animate = true,
}: {
  children: React.ReactNode;
  open?: boolean;
  setOpen?: React.Dispatch<React.SetStateAction<boolean>>;
  animate?: boolean;
}) => {
  const [openState, setOpenState] = useState(false);

  const open = openProp !== undefined ? openProp : openState;
  const setOpen = setOpenProp !== undefined ? setOpenProp : setOpenState;

  return (
    <SidebarContext.Provider value={{ open, setOpen, animate }}>
      {children}
    </SidebarContext.Provider>
  );
};

export const Sidebar = ({
  children,
  open,
  setOpen,
  animate,
}: {
  children: React.ReactNode;
  open?: boolean;
  setOpen?: React.Dispatch<React.SetStateAction<boolean>>;
  animate?: boolean;
}) => {
  return (
    <SidebarProvider open={open} setOpen={setOpen} animate={animate}>
      {children}
    </SidebarProvider>
  );
};

export const SidebarBody = (props: React.ComponentProps<typeof motion.div>) => {
  return (
    <>
      <DesktopSidebar {...props} />
      <MobileSidebar {...(props as React.ComponentProps<"div">)} />
    </>
  );
};

export const DesktopSidebar = ({
  className,
  children,
  ...props
}: React.ComponentProps<typeof motion.div>) => {
  const { open, setOpen, animate } = useSidebar();
  return (
    <motion.div
      className={cn(
        "h-full px-3 py-4 hidden md:flex md:flex-col bg-neutral-100 dark:bg-black border-r border-slate-200/80 dark:border-white/10 flex-shrink-0 select-none overflow-hidden",
        className
      )}
      animate={{
        width: animate ? (open ? "300px" : "68px") : "300px",
      }}
      transition={{
        duration: 0.28,
        ease: [0.25, 0.1, 0.25, 1.0],
      }}
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
      {...props}
    >
      {children}
    </motion.div>
  );
};

export const MobileSidebar = ({
  className,
  children,
  ...props
}: React.ComponentProps<"div">) => {
  const { open, setOpen } = useSidebar();
  return (
    <>
      <div
        className={cn(
          "h-10 px-4 py-4 flex flex-row md:hidden items-center justify-between bg-neutral-100 dark:bg-black w-full"
        )}
        {...props}
      >
        <div className="flex justify-end z-20 w-full">
          <Menu
            className="text-neutral-800 dark:text-neutral-200 cursor-pointer"
            onClick={() => setOpen(!open)}
          />
        </div>
        <AnimatePresence>
          {open && (
            <motion.div
              initial={{ x: "-100%", opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ x: "-100%", opacity: 0 }}
              transition={{
                duration: 0.3,
                ease: "easeInOut",
              }}
              className={cn(
                "fixed h-full w-full inset-0 bg-white dark:bg-black p-10 z-[100] flex flex-col justify-between",
                className
              )}
            >
              <div
                className="absolute right-10 top-10 z-50 text-neutral-800 dark:text-neutral-200 cursor-pointer"
                onClick={() => setOpen(!open)}
              >
                <X />
              </div>
              {children}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </>
  );
};

export const SidebarLink = ({
  link,
  className,
  ...props
}: {
  link: Links;
  className?: string;
  props?: LinkProps;
}) => {
  const { open, animate } = useSidebar();
  const isButton = link.onClick && (!link.href || link.href === "#");

  const baseClassName = cn(
    "flex items-center justify-start gap-3 py-2 px-2 rounded-xl transition-colors duration-150 cursor-pointer w-full text-left overflow-hidden select-none",
    link.active
      ? "bg-indigo-600 text-white font-semibold shadow-sm"
      : "text-neutral-700 dark:text-neutral-200 hover:bg-neutral-200/60 dark:hover:bg-white/[0.08]",
    className
  );

  if (isButton) {
    return (
      <button
        type="button"
        onClick={(e) => link.onClick?.(e)}
        className={baseClassName}
      >
        <div className="w-6 h-6 flex items-center justify-center shrink-0">{link.icon}</div>
        <motion.span
          animate={{
            display: animate ? (open ? "inline-block" : "none") : "inline-block",
            opacity: animate ? (open ? 1 : 0) : 1,
          }}
          transition={{
            duration: 0.18,
            ease: "easeInOut",
          }}
          className={cn(
            "text-sm whitespace-pre inline-block !p-0 !m-0 flex-1 truncate",
            link.active ? "text-white" : "text-neutral-700 dark:text-neutral-200"
          )}
        >
          {link.label}
        </motion.span>
        {link.badge && open && (
          <span className="ml-auto text-[10px] font-bold px-1.5 py-0.5 rounded-full bg-rose-500 text-white shrink-0">
            {link.badge}
          </span>
        )}
      </button>
    );
  }

  return (
    <Link
      href={link.href || "#"}
      className={baseClassName}
      onClick={link.onClick ? (e) => link.onClick?.(e) : undefined}
      {...props}
    >
      <div className="w-6 h-6 flex items-center justify-center shrink-0">{link.icon}</div>
      <motion.span
        animate={{
          display: animate ? (open ? "inline-block" : "none") : "inline-block",
          opacity: animate ? (open ? 1 : 0) : 1,
        }}
        transition={{
          duration: 0.18,
          ease: "easeInOut",
        }}
        className={cn(
          "text-sm whitespace-pre inline-block !p-0 !m-0 flex-1 truncate",
          link.active ? "text-white" : "text-neutral-700 dark:text-neutral-200"
        )}
      >
        {link.label}
      </motion.span>
      {link.badge && open && (
        <span className="ml-auto text-[10px] font-bold px-1.5 py-0.5 rounded-full bg-rose-500 text-white shrink-0">
          {link.badge}
        </span>
      )}
    </Link>
  );
};
