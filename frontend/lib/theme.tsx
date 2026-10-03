"use client";

import { Moon, Sun } from "lucide-react";
import { useEffect, useSyncExternalStore } from "react";
const KEY = "careerpilot.theme";
function subscribe(callback: () => void) { window.addEventListener("storage", callback); return () => window.removeEventListener("storage", callback); }
function getSnapshot() { return typeof window !== "undefined" && window.localStorage.getItem(KEY) === "light"; }
function getServerSnapshot() { return false; }
export function ThemeToggle() {
  const light = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
  useEffect(() => { document.documentElement.dataset.theme = light ? "light" : "dark"; }, [light]);
  function toggle() { const next=!light; const value=next?"light":"dark"; window.localStorage.setItem(KEY,value); document.documentElement.dataset.theme=value; window.dispatchEvent(new StorageEvent("storage", {key:KEY,newValue:value})); }
  return <button type="button" onClick={toggle} aria-label={light?"Switch to dark theme":"Switch to light theme"} className="inline-flex items-center gap-2 rounded-xl border border-white/10 px-3 py-2 text-xs text-white/65 hover:text-white">{light?<Sun size={15}/>:<Moon size={15}/>} {light?"Light":"Dark"}</button>;
}
