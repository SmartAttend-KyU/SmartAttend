"use client";

import { useEffect, useRef, useState } from "react";

interface BarcodeDetectorResult {
  rawValue: string;
}

interface BarcodeDetectorLike {
  new (options?: { formats?: string[] }): BarcodeDetectorLikeInstance;
}

interface BarcodeDetectorLikeInstance {
  detect(source: HTMLVideoElement): Promise<BarcodeDetectorResult[]>;
}

declare global {
  interface Window {
    BarcodeDetector?: BarcodeDetectorLike;
  }
}

interface QRScannerProps {
  onDetected: (value: string) => void;
}

export default function QRScanner({ onDetected }: QRScannerProps) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const timerRef = useRef<number | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function stop() {
    if (timerRef.current !== null) {
      window.clearInterval(timerRef.current);
      timerRef.current = null;
    }
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    setRunning(false);
  }

  async function start() {
    setError(null);

    if (!window.BarcodeDetector) {
      setError("QR camera scanning is not supported by this browser. Use the manual QR token field below.");
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: { ideal: "environment" } },
        audio: false,
      });
      streamRef.current = stream;

      if (!videoRef.current) {
        stop();
        return;
      }

      videoRef.current.srcObject = stream;
      await videoRef.current.play();

      const Detector = window.BarcodeDetector;
      const detector = new Detector({ formats: ["qr_code"] });
      setRunning(true);

      timerRef.current = window.setInterval(async () => {
        if (!videoRef.current) return;
        try {
          const results = await detector.detect(videoRef.current);
          const value = results[0]?.rawValue;
          if (value) {
            onDetected(value);
            stop();
          }
        } catch {
          // Ignore individual frames while the camera is starting/stopping.
        }
      }, 250);
    } catch {
      setError("Camera access was unavailable. Check browser permissions or use the manual QR token field.");
      stop();
    }
  }

  useEffect(() => stop, []);

  return (
    <div>
      <div style={styles.cameraBox}>
        <video ref={videoRef} muted playsInline style={styles.video} />
        {!running && (
          <div style={styles.cameraPlaceholder}>
            <strong>QR scanner</strong>
            <span>Use the lecturer's live QR code.</span>
          </div>
        )}
      </div>

      <div style={styles.actions}>
        {!running ? (
          <button type="button" onClick={start} style={styles.primary}>
            Start camera
          </button>
        ) : (
          <button type="button" onClick={stop} style={styles.secondary}>
            Stop camera
          </button>
        )}
      </div>

      {error && <p style={styles.error}>{error}</p>}
    </div>
  );
}

const styles = {
  cameraBox: {
    position: "relative" as const,
    minHeight: 260,
    overflow: "hidden" as const,
    borderRadius: 16,
    background: "#101828",
  },
  video: {
    width: "100%",
    minHeight: 260,
    objectFit: "cover" as const,
  },
  cameraPlaceholder: {
    position: "absolute" as const,
    inset: 0,
    display: "grid",
    placeContent: "center",
    gap: 8,
    textAlign: "center" as const,
    color: "#ffffff",
    padding: 24,
  },
  actions: {
    display: "flex",
    gap: 10,
    marginTop: 12,
  },
  primary: {
    border: 0,
    borderRadius: 10,
    padding: "11px 16px",
    background: "#172033",
    color: "#ffffff",
    cursor: "pointer",
  },
  secondary: {
    border: "1px solid #d7dce5",
    borderRadius: 10,
    padding: "11px 16px",
    background: "#ffffff",
    cursor: "pointer",
  },
  error: {
    color: "#b42318",
    lineHeight: 1.5,
  },
};
