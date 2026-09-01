"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";

function urlBase64ToUint8Array(base64String: string) {
  const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
  const rawData = atob(base64);
  return Uint8Array.from([...rawData].map((c) => c.charCodeAt(0)));
}

function isPushSupported() {
  return typeof navigator !== "undefined" && "serviceWorker" in navigator && "PushManager" in window;
}

export function PushManager() {
  const [status, setStatus] = useState<"unsupported" | "idle" | "subscribed" | "subscribing">(
    () => (isPushSupported() ? "idle" : "unsupported"),
  );

  useEffect(() => {
    if (!isPushSupported()) return;
    navigator.serviceWorker.ready.then(async (reg) => {
      const sub = await reg.pushManager.getSubscription();
      if (sub) setStatus("subscribed");
    });
  }, []);

  async function subscribe() {
    setStatus("subscribing");
    try {
      const keyRes = await fetch("/api/push/vapid-key");
      const { publicKey } = await keyRes.json();
      if (!publicKey) {
        setStatus("unsupported");
        return;
      }
      const reg = await navigator.serviceWorker.ready;
      const sub = await reg.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(publicKey),
      });
      await fetch("/api/push/subscribe", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(sub),
      });
      setStatus("subscribed");
    } catch (err) {
      console.error("Push subscription failed", err);
      setStatus("idle");
    }
  }

  if (status === "unsupported") {
    return <span className="text-xs text-white/30">Push not supported on this browser</span>;
  }
  if (status === "subscribed") {
    return <span className="text-xs text-emerald-400">Notifications on</span>;
  }
  return (
    <Button size="sm" variant="outline" onClick={subscribe} disabled={status === "subscribing"}>
      {status === "subscribing" ? "Enabling…" : "Enable notifications"}
    </Button>
  );
}
