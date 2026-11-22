"use client";

import { useEffect, useRef, useState, useSyncExternalStore } from "react";

import { CloseIcon, DownloadIcon, ShareIcon } from "./icons";

/**
 * Installing ANSIT as an app.
 *
 * Chromium browsers fire `beforeinstallprompt` when the site is installable;
 * we keep that event and use it when the user asks. Safari on iOS has no such
 * event, so there we explain "Add to Home Screen" instead. When the app is
 * already running installed, nothing about installing is shown.
 */

interface BeforeInstallPromptEvent extends Event {
  prompt(): Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed" }>;
}

type InstallState = "unsupported" | "available" | "ios" | "installed";

let deferred: BeforeInstallPromptEvent | null = null;
let installedNow = false;
const listeners = new Set<() => void>();
const notify = () => listeners.forEach((listener) => listener());

if (typeof window !== "undefined") {
  // The event can fire before any component mounts, so listen at module load.
  window.addEventListener("beforeinstallprompt", (event) => {
    event.preventDefault(); // we show our own button instead of the mini-bar
    deferred = event as BeforeInstallPromptEvent;
    notify();
  });
  window.addEventListener("appinstalled", () => {
    deferred = null;
    installedNow = true;
    notify();
  });
}

function isStandalone(): boolean {
  return (
    window.matchMedia("(display-mode: standalone)").matches ||
    (navigator as Navigator & { standalone?: boolean }).standalone === true
  );
}

function isIosSafari(): boolean {
  const ua = navigator.userAgent;
  const ios =
    /iPhone|iPad|iPod/.test(ua) ||
    // iPadOS reports itself as a Mac, but has a touch screen.
    (ua.includes("Macintosh") && navigator.maxTouchPoints > 1);
  // Other iOS browsers cannot add to the home screen the same way.
  return ios && !/CriOS|FxiOS|EdgiOS/.test(ua);
}

function snapshot(): InstallState {
  if (installedNow || isStandalone()) return "installed";
  if (deferred) return "available";
  if (isIosSafari()) return "ios";
  return "unsupported";
}

function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  const media = window.matchMedia("(display-mode: standalone)");
  media.addEventListener("change", listener);
  return () => {
    listeners.delete(listener);
    media.removeEventListener("change", listener);
  };
}

export function useInstall() {
  const state = useSyncExternalStore<InstallState>(
    subscribe,
    snapshot,
    () => "unsupported", // on the server and before hydration
  );
  const [showIosHelp, setShowIosHelp] = useState(false);

  const install = async () => {
    if (state === "ios") {
      setShowIosHelp(true);
      return;
    }
    const event = deferred;
    if (!event) return;
    await event.prompt();
    const choice = await event.userChoice;
    // The event can only be used once, whatever the answer.
    deferred = null;
    if (choice.outcome === "accepted") installedNow = true;
    notify();
  };

  return {
    state,
    install,
    showIosHelp,
    closeIosHelp: () => setShowIosHelp(false),
  };
}

/** How to install from Safari on iPhone and iPad. */
function IosHelp({ onClose }: { onClose: () => void }) {
  const dialog = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    dialog.current?.showModal();
  }, []);
  return (
    <dialog
      ref={dialog}
      onClose={onClose}
      aria-labelledby="ios-install-title"
      className="install-dialog"
    >
      <div className="install-dialog-head">
        <h2 id="ios-install-title">تثبيت أنصِت على iPhone و iPad</h2>
        <button
          type="button"
          aria-label="إغلاق"
          onClick={() => dialog.current?.close()}
        >
          <CloseIcon size={18} />
        </button>
      </div>
      <ol>
        <li>
          اضغط زر المشاركة <ShareIcon size={16} /> في شريط Safari.
        </li>
        <li>اختر «إضافة إلى الصفحة الرئيسية».</li>
        <li>اضغط «إضافة»، وسيظهر أنصِت بين تطبيقاتك.</li>
      </ol>
      <p>التثبيت متاح من متصفح Safari فقط على هذه الأجهزة.</p>
    </dialog>
  );
}

/** A compact button for the header. Renders nothing when installing is not possible. */
export function InstallButton() {
  const { state, install, showIosHelp, closeIosHelp } = useInstall();
  if (state === "unsupported" || state === "installed") return null;
  return (
    <>
      <button
        type="button"
        className="btn btn-outline btn-small"
        onClick={install}
      >
        <DownloadIcon size={16} />
        تثبيت التطبيق
      </button>
      {showIosHelp && <IosHelp onClose={closeIosHelp} />}
    </>
  );
}

/** A full-width section that explains installing. Hidden once installed. */
export function InstallBand() {
  const { state, install, showIosHelp, closeIosHelp } = useInstall();
  if (state === "installed") return null;
  return (
    <section className="install-band" aria-labelledby="install-title">
      <div className="shell install-band-inner">
        <div>
          <p className="kicker">تطبيق على جهازك</p>
          <h2 id="install-title">ثبّت أنصِت وافتحه كأي تطبيق.</h2>
          <p>
            يفتح في نافذته الخاصة ومن أيقونته على الشاشة الرئيسية، ويبقى سجلّك
            والصفحات التي زرتها متاحة دون اتصال. التعرّف على التلاوة نفسه يحتاج
            اتصالًا بالإنترنت.
          </p>
        </div>
        {state === "unsupported" ? (
          <p className="install-band-note">
            للتثبيت افتح أنصِت في Chrome أو Edge، أو في Safari على iPhone و iPad.
          </p>
        ) : (
          <button type="button" className="btn btn-primary" onClick={install}>
            <DownloadIcon size={18} />
            {state === "ios" ? "طريقة التثبيت" : "تثبيت التطبيق"}
          </button>
        )}
      </div>
      {showIosHelp && <IosHelp onClose={closeIosHelp} />}
    </section>
  );
}

/** The install control for the Settings screen: always says where things stand. */
export function InstallRow() {
  const { state, install, showIosHelp, closeIosHelp } = useInstall();
  if (state === "installed") {
    return <p className="text-sm">أنصِت مثبّت على هذا الجهاز.</p>;
  }
  if (state === "unsupported") {
    return (
      <p className="text-sm leading-[1.8] text-muted">
        للتثبيت كتطبيق افتح أنصِت في Chrome أو Edge، أو في Safari على iPhone و
        iPad.
      </p>
    );
  }
  return (
    <>
      <button type="button" className="btn btn-primary" onClick={install}>
        <DownloadIcon size={18} />
        {state === "ios" ? "طريقة التثبيت" : "تثبيت التطبيق"}
      </button>
      {showIosHelp && <IosHelp onClose={closeIosHelp} />}
    </>
  );
}

/**
 * Tells the user when a new version has been downloaded and lets them switch
 * to it. Nothing reloads on its own: a recording in progress is never lost.
 */
export function UpdateToast() {
  const [waiting, setWaiting] = useState<ServiceWorker | null>(null);
  const updateRequested = useRef(false);

  useEffect(() => {
    if (!("serviceWorker" in navigator)) return;
    let cancelled = false;
    const watch = (registration: ServiceWorkerRegistration) => {
      const offer = (worker: ServiceWorker | null) => {
        // Only an update counts: the first install has no controller yet.
        if (worker && navigator.serviceWorker.controller && !cancelled) {
          setWaiting(worker);
        }
      };
      offer(registration.waiting);
      registration.addEventListener("updatefound", () => {
        const incoming = registration.installing;
        incoming?.addEventListener("statechange", () => {
          if (incoming.state === "installed") offer(incoming);
        });
      });
    };
    navigator.serviceWorker.getRegistration().then((registration) => {
      if (registration) watch(registration);
    });
    // Load the new version once the new worker takes over, but only when the
    // user asked for the update. The first install also changes the
    // controller, and must not reload the page under the user.
    const onChange = () => {
      if (!updateRequested.current) return;
      updateRequested.current = false;
      window.location.reload();
    };
    navigator.serviceWorker.addEventListener("controllerchange", onChange);
    return () => {
      cancelled = true;
      navigator.serviceWorker.removeEventListener("controllerchange", onChange);
    };
  }, []);

  if (!waiting) return null;
  return (
    <div className="update-toast" role="status">
      <span>نسخة جديدة من أنصِت جاهزة.</span>
      <button
        type="button"
        className="btn btn-primary btn-small"
        onClick={() => {
          updateRequested.current = true;
          waiting.postMessage({ type: "SKIP_WAITING" });
        }}
      >
        تحديث الآن
      </button>
      <button
        type="button"
        aria-label="لاحقًا"
        className="update-toast-close"
        onClick={() => setWaiting(null)}
      >
        <CloseIcon size={16} />
      </button>
    </div>
  );
}
