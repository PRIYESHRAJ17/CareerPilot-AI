"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  BarChart3,
  BriefcaseBusiness,
  Building2,
  BellRing,
  CalendarDays,
  FileText,
  LayoutDashboard,
  Menu,
  MessageSquareText,
  Network,
  PackageCheck,
  Radar,
  Settings,
  Target,
  UserRound,
  X,
  PlugZap,
  Inbox,
  GraduationCap,
} from "lucide-react";
import { useEffect, useState } from "react";
import { ThemeToggle } from "@/lib/theme";
import { apiJson } from "@/lib/apiClient";

const NAV = [
  ["/dashboard", "Dashboard", LayoutDashboard],
  ["/opportunities", "Opportunities", BriefcaseBusiness],
  ["/providers", "Sources", Radar],
  ["/career-twin", "Career Twin", Target],
  ["/resume", "Resume", FileText],
  ["/companies", "Companies", Building2],
  ["/interviews", "Interviews", MessageSquareText],
  ["/applications", "Applications", CalendarDays],
  ["/packets", "Application Packets", PackageCheck],
  ["/career-plan", "Career Plan", BarChart3],
  ["/market", "Market Intelligence", Radar],
  ["/saved-jobs", "Saved Jobs", PackageCheck],
  ["/networking", "Networking", Network],
  ["/inbox", "Career Inbox", Inbox],
  ["/learning", "Learning Hub", GraduationCap],
  ["/alerts", "Alerts", BellRing],
  ["/integrations", "Integrations", PlugZap],
  ["/settings", "Settings", Settings],
] as const;

export function AppShell({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const router = useRouter();
  const [open, setOpen] = useState(false);

  async function logout() {
    try { await apiJson("/session/logout", { method: "POST" }); } finally { router.replace("/auth"); }
  }

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setOpen(false);
        return;
      }
      if (event.key !== "Tab" || !open) return;
      const drawer = document.querySelector("aside");
      if (!drawer) return;
      const focusable = drawer.querySelectorAll<HTMLElement>("a[href],button:not([disabled])");
      if (!focusable.length) return;
      const first = focusable[0]; const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    };

    document.addEventListener(
      "keydown",
      onKeyDown,
    );

    return () => {
      document.removeEventListener(
        "keydown",
        onKeyDown,
      );
    };
  }, [open]);

  return (
    <>
      <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-white/10 bg-[#080a0f]/95 px-4 backdrop-blur lg:hidden">
        <Link
          href="/dashboard"
          className="font-semibold"
        >
          CareerPilot
        </Link>

        <button
          type="button"
          aria-label={
            open
              ? "Close navigation"
              : "Open navigation"
          }
          onClick={() =>
            setOpen((value) => !value)
          }
          className="rounded-xl border border-white/10 p-2"
        >
          {open ? (
            <X size={18} />
          ) : (
            <Menu size={18} />
          )}
        </button>
      </header>

      <aside
        className={[
          "fixed inset-y-0 left-0 z-40 w-[260px] border-r border-white/10 bg-[#0b0e14] p-5 transition-transform",
          "lg:translate-x-0",
          open
            ? "translate-x-0"
            : "-translate-x-full",
        ].join(" ")}
      >
        <div className="flex items-center justify-between">
          <Link
            href="/dashboard"
            className="text-lg font-semibold"
          >
            CareerPilot
          </Link>

          <button
            type="button"
            aria-label="Close navigation"
            onClick={() => setOpen(false)}
            className="rounded-xl border border-white/10 p-2 lg:hidden"
          >
            <X size={17} />
          </button>
        </div>

        <nav
          className="mt-8 space-y-1"
          aria-label="Primary navigation"
        >
          {NAV.map(
            ([href, label, Icon]) => {
              const active =
                pathname === href ||
                pathname.startsWith(
                  `${href}/`,
                );

              return (
                <Link
                  key={href}
                  href={href}
                  onClick={() =>
                    setOpen(false)
                  }
                  aria-current={
                    active
                      ? "page"
                      : undefined
                  }
                  className={[
                    "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition",
                    active
                      ? "bg-white text-black"
                      : "text-white/55 hover:bg-white/[0.04] hover:text-white",
                  ].join(" ")}
                >
                  <Icon size={16} />
                  {label}
                </Link>
              );
            },
          )}
        </nav>

        <div className="mt-8 space-y-3">
          <ThemeToggle />

          <button
            type="button"
            onClick={() => void logout()}
            className="w-full rounded-2xl border border-white/10 px-3 py-2 text-xs text-white/60 transition hover:bg-white/5 hover:text-white"
          >
            Log out
          </button>

          <Link
            href="/career-twin"
            className="flex items-center gap-3 rounded-2xl border border-white/10 bg-white/[0.03] p-3 text-sm"
          >
            <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-white text-black">
              <UserRound size={15} />
            </span>

            <span className="flex-1">
              Career profile
            </span>

            <span aria-hidden>
              ›
            </span>
          </Link>
        </div>
      </aside>

      <div
        className={`fixed inset-0 z-30 bg-black/60 lg:hidden ${
          open
            ? "block"
            : "hidden"
        }`}
        onClick={() =>
          setOpen(false)
        }
        aria-hidden="true"
      />

      <div id="main-content" className="min-h-screen lg:pl-[260px]">
        <div className="sr-only" aria-label="Breadcrumb">CareerPilot / {pathname.replaceAll("/", " ").trim() || "Home"}</div>
        {children}
      </div>
    </>
  );
}
