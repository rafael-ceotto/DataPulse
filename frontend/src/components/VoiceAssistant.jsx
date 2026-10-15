import React, { useEffect, useRef, useState } from "react";
import { theme } from "../theme";
import { askAI } from "../services/api";
import { needsDeviceLocation, getDeviceLocation } from "../services/geolocation";

const LANG_CONFIG = {
  US: { lang: "en-US", wakeWords: ["hello doctor"] },
  BR: { lang: "pt-BR", wakeWords: ["olá doutor", "ola doutor"] },
};

const SILENCE_MS = 1200;

function getRecognition() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  return SpeechRecognition ? new SpeechRecognition() : null;
}

function stripMarkdown(text) {
  return text
    .replace(/\|.*\|/g, " ")
    .replace(/^[\s]*(?:[-*_]\s*){3,}$/gm, " ")
    .replace(/[—–]/g, ", ")
    .replace(/^\s*[-*+]\s+/gm, "")
    .replace(/^\s*\d+\.\s+/gm, "")
    .replace(/\*\*(.*?)\*\*/g, "$1")
    .replace(/\*(.*?)\*/g, "$1")
    .replace(/#{1,6}\s/g, "")
    .replace(/`([^`]*)`/g, "$1")
    .replace(/\[([^\]]*)\]\([^)]*\)/g, "$1")
    .replace(/\n+/g, " ")
    .replace(/\s{2,}/g, " ")
    .trim();
}

export default function VoiceAssistant({ country, onAnswer }) {
  const config = LANG_CONFIG[country];
  const [supported, setSupported] = useState(true);
  const [enabled, setEnabled] = useState(false);
  const [status, setStatus] = useState("idle");
  const [liveTranscript, setLiveTranscript] = useState("");
  const [question, setQuestion] = useState("");
  const [aiError, setAiError] = useState(false);
  const [restartKey, setRestartKey] = useState(0);
  const [voices, setVoices] = useState([]);
  const [selectedVoiceURI, setSelectedVoiceURI] = useState(
    () => localStorage.getItem(`voiceAssistant.voice.${country}`) || ""
  );
  const recognitionRef = useRef(null);
  const statusRef = useRef("idle");
  const silenceTimerRef = useRef(null);
  const conversationIdRef = useRef(crypto.randomUUID());

  useEffect(() => { statusRef.current = status; }, [status]);
  useEffect(() => { setSupported(!!getRecognition()); }, []);

  useEffect(() => {
    if (!config || !window.speechSynthesis) return;
    const langPrefix = config.lang.split("-")[0];
    let retryTimer = null;
    function loadVoices() {
      const all = window.speechSynthesis.getVoices();
      const filtered = all.filter((v) => v.lang.toLowerCase().startsWith(langPrefix));
      setVoices(filtered);
      if (all.length === 0) { retryTimer = setTimeout(loadVoices, 300); }
    }
    loadVoices();
    window.speechSynthesis.onvoiceschanged = loadVoices;
    return () => {
      window.speechSynthesis.onvoiceschanged = null;
      if (retryTimer) clearTimeout(retryTimer);
    };
  }, [country]);

  useEffect(() => {
    if (selectedVoiceURI) {
      localStorage.setItem(`voiceAssistant.voice.${country}`, selectedVoiceURI);
    }
  }, [selectedVoiceURI, country]);

  useEffect(() => {
    if (!enabled || !config) {
      recognitionRef.current?.stop();
      window.speechSynthesis?.cancel();
      if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);
      setStatus("idle");
      return;
    }

    const recognition = getRecognition();
    if (!recognition) return;
    recognitionRef.current = recognition;
    recognition.lang = config.lang;
    recognition.continuous = true;
    recognition.interimResults = true;

    function armSilenceTimer(fn) {
      if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);
      silenceTimerRef.current = setTimeout(fn, SILENCE_MS);
    }

    function finalizeQuestion(text) {
      const trimmed = text.trim();
      if (!trimmed) return;
      setQuestion(trimmed);
      setStatus("heard");
      try { recognition.stop(); } catch (_) {}
    }

    recognition.onresult = (event) => {
      if (["heard", "processing", "speaking"].includes(statusRef.current)) return;

      let finalText = "";
      let interimText = "";
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) { finalText += transcript; } else { interimText += transcript; }
      }
      const combined = (finalText + " " + interimText).trim();
      if (!combined) return;

      const normalized = combined.toLowerCase();
      const matched = config.wakeWords.find((w) => normalized.includes(w));

      if (statusRef.current === "listening-wake") {
        if (!matched) { setLiveTranscript(combined); return; }
        setStatus("listening-question");
        setAiError(false);
      }

      const questionText = matched
        ? normalized.split(matched).slice(1).join(" ").trim()
        : normalized;

      setLiveTranscript(questionText);
      armSilenceTimer(() => finalizeQuestion(questionText));
    };

    recognition.onend = () => {
      if (enabled && !["heard", "processing", "speaking"].includes(statusRef.current)) {
        try { recognition.start(); } catch (_) {}
      }
    };

    recognition.onerror = (event) => { console.error("Voice recognition error:", event.error); };

    setStatus("listening-wake");
    setQuestion("");
    setLiveTranscript("");
    recognition.start();

    return () => {
      recognition.onend = null;
      recognition.stop();
      if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);
    };
  }, [enabled, country, restartKey]);

    useEffect(() => {
    if (!question) return;
    let cancelled = false;

    (async () => {
      setStatus("processing");
      setAiError(false);
      onAnswer?.(null);
      try {
        let lat = null, lng = null;
        if (needsDeviceLocation(question)) {
          const loc = await getDeviceLocation();
          if (loc) { lat = loc.lat; lng = loc.lng; }
        }
        const data = await askAI(question, conversationIdRef.current, country, lat, lng);
        if (cancelled) return;
        onAnswer?.(data);
        speakAnswer(data.explanation);
      } catch (err) {
        if (cancelled) return;
        console.error("Voice AI query failed:", err);
        setAiError(true);
        setQuestion("");
        setStatus("listening-wake");
        setRestartKey((k) => k + 1);
      }
    })();

    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [question]);

  function speakAnswer(text) {
    setStatus("speaking");
    if (!window.speechSynthesis) { resumeListening(); return; }
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(stripMarkdown(text));
    utterance.lang = config.lang;
    const chosenVoice = voices.find((v) => v.voiceURI === selectedVoiceURI) || voices[0];
    if (chosenVoice) utterance.voice = chosenVoice;
    utterance.onend = resumeListening;
    utterance.onerror = resumeListening;
    window.speechSynthesis.speak(utterance);
  }

  function resumeListening() {
    setQuestion("");
    setStatus("listening-wake");
    setRestartKey((k) => k + 1);
  }

  if (!config) return null;

  if (!supported) {
    return (
      <div style={{ fontFamily: theme.mono, fontSize: 11, color: "#6f8a95" }}>
        Voice not supported in this browser.
      </div>
    );
  }

  const isBR = country === "BR";
  const label = isBR ? "Olá Doutor" : "Hello Doctor";
  const statusLabel = {
    "listening-wake": isBR ? 'Esperando "Olá Doutor"...' : 'Waiting for "Hello Doctor"...',
    "listening-question": isBR ? "Ouvindo sua pergunta..." : "Listening to your question...",
    "heard": isBR ? "Ouvindo sua pergunta..." : "Listening to your question...",
    "processing": isBR ? "Pensando..." : "Thinking...",
    "speaking": isBR ? "Respondendo..." : "Answering...",
  }[status] || label;

  return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 10 }}>
      <button
        onClick={() => setEnabled((v) => !v)}
        style={{
          display: "flex", alignItems: "center", gap: 8,
          background: enabled ? "#0d5c73" : "#0F6F8C",
          border: "none",
          borderRadius: 10,
          padding: "10px 14px",
          fontSize: 14,
          fontWeight: 600,
          color: "#fff",
          cursor: "pointer",
          fontFamily: theme.sans,
          transition: "background 0.15s",
        }}
      >
        🎙 {enabled ? statusLabel : label}
      </button>

      {voices.length > 0 && (
        <select
          value={selectedVoiceURI || voices[0]?.voiceURI || ""}
          onChange={(e) => setSelectedVoiceURI(e.target.value)}
          onClick={(e) => e.stopPropagation()}
          title={isBR ? "Escolher voz" : "Choose voice"}
          style={{
            fontSize: 11, fontFamily: theme.mono, maxWidth: 160,
            background: "#f4f6f8", border: "1px solid #e0e5e8",
            borderRadius: 6, padding: "4px 6px", color: "#3d5566",
          }}
        >
          {voices.map((v) => (
            <option key={v.voiceURI} value={v.voiceURI}>{v.name}</option>
          ))}
        </select>
      )}

      {liveTranscript && status !== "heard" && status !== "processing" && status !== "speaking" && (
        <span style={{ fontFamily: theme.mono, fontSize: 11, color: "#6f8a95", fontStyle: "italic" }}>
          "{liveTranscript}"
        </span>
      )}
      {(status === "heard" || status === "processing" || status === "speaking") && question && (
        <span style={{ fontFamily: theme.mono, fontSize: 12, color: theme.mint }}>
          "{question}"
        </span>
      )}
      {aiError && (
        <span style={{ fontFamily: theme.mono, fontSize: 12, color: "#ff6b6b" }}>
          {isBR ? "Erro ao perguntar à IA." : "AI query failed."}
        </span>
      )}
    </div>
  );
}