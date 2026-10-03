"use client";
import { useEffect } from "react";
import { reportTelemetry } from "@/lib/telemetry";
export function WebVitals() {
  useEffect(() => {
    const observed: PerformanceObserver[] = [];
    try {
      const lcp = new PerformanceObserver((list) => { const last = list.getEntries().at(-1) as PerformanceEntry | undefined; if (last) reportTelemetry({name:"LCP",value:last.startTime}); });
      lcp.observe({ type: "largest-contentful-paint", buffered: true }); observed.push(lcp);
    } catch {}
    try {
      let cls = 0;
      const layout = new PerformanceObserver((list) => { for (const entry of list.getEntries() as Array<PerformanceEntry & { hadRecentInput?: boolean; value?: number }>) if (!entry.hadRecentInput) cls += entry.value ?? 0; reportTelemetry({name:"CLS",value:cls}); });
      layout.observe({ type: "layout-shift", buffered: true }); observed.push(layout);
    } catch {}
    return () => observed.forEach((observer) => observer.disconnect());
  }, []);
  return null;
}
