import { useState } from "react";
import { DOMAINS, DOMAIN_ABBR } from "./Domains";

interface LandingPageProps {
  /** Navigate into the lobby. Pass a domain id to pre-select it there. */
  onStart: (domainId?: string) => void;
}

/* ---------------------------- icons ---------------------------- */

const IconCamera = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="6" width="13" height="12" rx="2" />
    <path d="M16 10.5 21 7v10l-5-3.5" />
  </svg>
);
const IconMic = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <rect x="9" y="3" width="6" height="11" rx="3" />
    <path d="M5 11a7 7 0 0 0 14 0" />
    <path d="M12 18v3" />
    <path d="M8.5 21h7" />
  </svg>
);
const IconBolt = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M13 2 4 14h6l-1 8 9-12h-6l1-8Z" />
  </svg>
);
const IconWaves = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M3 12h2.2l2-6 3 12 2.6-9 2 6h2.2" />
    <path d="M18 12h3" />
  </svg>
);
const IconTarget = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="8.5" />
    <circle cx="12" cy="12" r="4.5" />
    <circle cx="12" cy="12" r="0.6" fill="currentColor" stroke="none" />
  </svg>
);
const IconChevronDown = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="m6 9 6 6 6-6" />
  </svg>
);
const IconArrowRight = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M5 12h13" />
    <path d="m13 6 6 6-6 6" />
  </svg>
);

/* ---------------------------- content ---------------------------- */

const STEPS: { title: string; body: string }[] = [
  {
    title: "Turn on your camera & mic",
    body: "Grant access once in the lobby. Aptigrad checks both are working before your session starts.",
  },
  {
    title: "Pick your domain",
    body: "Choose from DSA, OOP, DBMS, OS, CN, or System Design — whichever round you're prepping for.",
  },
  {
    title: "Answer out loud",
    body: "Record your response by voice. Aptigrad listens, evaluates it, and replies like an interviewer would.",
  },
  {
    title: "Get pushed further",
    body: "Every answer adjusts the difficulty of the next question, for up to 25 questions in a session.",
  },
];

const FEATURES: { icon: React.ReactNode; title: string; body: string }[] = [
  {
    icon: <IconBolt />,
    title: "Adaptive difficulty",
    body: "There's no fixed script. Each question is generated from your last answer, so the round gets harder or eases off the way a real interviewer would probe.",
  },
  {
    icon: <IconWaves />,
    title: "Full voice interaction",
    body: "Speak your answers and hear the interviewer's questions read back to you — closer to a call than a form you fill in.",
  },
  {
    icon: <IconTarget />,
    title: "25-question sessions",
    body: "Long enough to build real stamina in one domain, instead of stopping after a handful of warm-up questions.",
  },
];

const FAQ_ITEMS: { q: string; a: string }[] = [
  {
    q: "Do I need to upload a resume?",
    a: "No. Pick a domain and start — there's no resume, signup form, or profile to fill out first.",
  },
  {
    q: "What do I need before I start?",
    a: "A working camera and microphone. The lobby checks both and won't let you start until they're ready.",
  },
  {
    q: "How many questions will I get?",
    a: "Each session runs up to 25 questions in your chosen domain, with difficulty adjusting as you answer.",
  },
  {
    q: "Is my camera feed sent anywhere?",
    a: "No — your video is only used for your own on-screen preview during the call. Only your recorded voice answers are sent for evaluation.",
  },
  {
    q: "Can I change domains mid-session?",
    a: "Not mid-interview. End the current session from the call screen and start a new one to pick a different domain.",
  },
  {
    q: "Which browser should I use?",
    a: "Any recent desktop browser with camera and microphone permissions — Chrome, Edge, and Firefox all work well.",
  },
];

/* ---------------------------- styles ---------------------------- */

const LANDING_STYLES = `
.apg-home { background: var(--apg-bg); }

.apg-home-nav { position: sticky; top: 0; z-index: 20; display: flex; align-items: center; justify-content: space-between; padding: 16px 28px; background: rgba(245,246,248,0.85); backdrop-filter: blur(8px); border-bottom: 1px solid var(--apg-line); }
.apg-home-nav-brand { display: flex; align-items: center; gap: 10px; }
.apg-home-nav-mark { width: 34px; height: 34px; border-radius: 50%; background: var(--apg-navy); color: var(--apg-gold); font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 0.95rem; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.apg-home-nav-name { font-family: 'Space Grotesk', sans-serif; font-weight: 600; font-size: 1rem; }
.apg-home-nav-cta { border: none; border-radius: 999px; background: var(--apg-navy); color: #fff; padding: 10px 20px; font-size: 0.88rem; font-weight: 600; cursor: pointer; transition: transform 0.12s ease; }
.apg-home-nav-cta:hover { transform: translateY(-1px); }

.apg-home-hero { padding: 64px 28px 32px; max-width: 1180px; margin: 0 auto; display: grid; grid-template-columns: 1.05fr 0.95fr; gap: 48px; align-items: center; }
@media (max-width: 960px) { .apg-home-hero { grid-template-columns: 1fr; padding-top: 40px; } }

.apg-home-eyebrow { display: inline-flex; align-items: center; gap: 6px; padding: 6px 14px; border-radius: 999px; background: rgba(232,163,61,0.14); color: #9a6a15; font-size: 0.8rem; font-weight: 600; margin-bottom: 18px; }
.apg-home-hero-title { margin: 0 0 18px; font-family: 'Space Grotesk', sans-serif; font-weight: 600; font-size: clamp(2rem, 4vw, 3rem); line-height: 1.15; }
.apg-home-hero-sub { margin: 0 0 26px; color: var(--apg-ink-soft); font-size: 1.05rem; line-height: 1.6; max-width: 52ch; }
.apg-home-hero-ctas { display: flex; align-items: center; gap: 16px; flex-wrap: wrap; }
.apg-home-btn { display: inline-flex; align-items: center; gap: 8px; border: none; border-radius: var(--apg-r-sm); padding: 15px 24px; font-size: 0.98rem; font-weight: 600; cursor: pointer; transition: transform 0.12s ease, box-shadow 0.12s ease; }
.apg-home-btn svg { width: 18px; height: 18px; }
.apg-home-btn--gold { background: var(--apg-gold); color: var(--apg-navy); }
.apg-home-btn--gold:hover { transform: translateY(-1px); box-shadow: 0 14px 26px -16px rgba(232,163,61,0.75); }
.apg-home-hero-note { margin: 14px 0 0; font-size: 0.85rem; color: var(--apg-ink-soft); }
.apg-home-hero-reqs { display: flex; gap: 18px; margin-top: 12px; }
.apg-home-hero-reqs span { display: inline-flex; align-items: center; gap: 6px; font-size: 0.82rem; color: var(--apg-ink-soft); }
.apg-home-hero-reqs svg { width: 15px; height: 15px; }

.apg-home-preview { position: relative; border-radius: var(--apg-r-lg); background: linear-gradient(180deg, var(--apg-navy-soft), var(--apg-navy)); border: 1px solid rgba(255,255,255,0.08); padding: 22px; box-shadow: 0 40px 80px -50px rgba(15,27,45,0.55); }
.apg-home-preview-top { display: flex; align-items: center; gap: 8px; color: rgba(255,255,255,0.6); font-size: 0.78rem; margin-bottom: 18px; }
.apg-home-preview-dot { width: 7px; height: 7px; border-radius: 50%; background: var(--apg-teal); box-shadow: 0 0 0 3px rgba(31,138,99,0.25); }
.apg-home-preview-stage { display: flex; flex-direction: column; align-items: center; gap: 14px; padding: 26px 10px; }
.apg-home-preview-badge { width: 76px; height: 76px; border-radius: 50%; background: var(--apg-navy); border: 2px solid rgba(232,163,61,0.55); color: var(--apg-gold); font-family: 'Space Grotesk', sans-serif; font-size: 1.7rem; font-weight: 700; display: flex; align-items: center; justify-content: center; }
.apg-home-preview-caption { margin: 0; color: rgba(255,255,255,0.72); font-size: 0.88rem; }
.apg-home-preview-bars { display: flex; align-items: flex-end; gap: 4px; height: 22px; }
.apg-home-preview-bars span { width: 4px; border-radius: 2px; background: var(--apg-gold); animation: apg-home-bar 1.1s ease-in-out infinite; }
.apg-home-preview-bars span:nth-child(1) { height: 40%; animation-delay: 0s; }
.apg-home-preview-bars span:nth-child(2) { height: 90%; animation-delay: 0.1s; }
.apg-home-preview-bars span:nth-child(3) { height: 60%; animation-delay: 0.2s; }
.apg-home-preview-bars span:nth-child(4) { height: 100%; animation-delay: 0.3s; }
.apg-home-preview-bars span:nth-child(5) { height: 55%; animation-delay: 0.4s; }
.apg-home-preview-subtitle { margin: 0; padding: 14px 16px; border-radius: var(--apg-r-md); background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.1); color: #f0f2f5; font-size: 0.9rem; line-height: 1.5; }
.apg-home-preview-float { position: absolute; top: -14px; right: -10px; display: flex; align-items: center; gap: 7px; background: var(--apg-surface); border: 1px solid var(--apg-line); border-radius: 999px; padding: 9px 14px; font-size: 0.8rem; font-weight: 600; color: var(--apg-ink); box-shadow: 0 16px 30px -18px rgba(15,27,45,0.4); animation: apg-home-float 3.2s ease-in-out infinite; }
.apg-home-preview-float svg { width: 15px; height: 15px; color: var(--apg-teal); }

.apg-home-section { max-width: 1180px; margin: 0 auto; padding: 72px 28px; }
.apg-home-section-head { max-width: 60ch; margin-bottom: 40px; }
.apg-home-section-title { margin: 0 0 12px; font-family: 'Space Grotesk', sans-serif; font-weight: 600; font-size: clamp(1.5rem, 2.6vw, 2.1rem); }
.apg-home-section-sub { margin: 0; color: var(--apg-ink-soft); font-size: 1rem; line-height: 1.6; }

.apg-home-domain-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 18px; }
@media (max-width: 960px) { .apg-home-domain-grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 640px) { .apg-home-domain-grid { grid-template-columns: 1fr; } }
.apg-home-domain-card { display: flex; flex-direction: column; gap: 14px; background: var(--apg-surface); border: 1px solid var(--apg-line); border-radius: var(--apg-r-md); padding: 22px; transition: transform 0.15s ease, box-shadow 0.15s ease; }
.apg-home-domain-card:hover { transform: translateY(-3px); box-shadow: 0 22px 40px -28px rgba(15,27,45,0.35); }
.apg-home-domain-tag { width: 40px; height: 40px; border-radius: 10px; background: rgba(15,27,45,0.06); color: var(--apg-navy); font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 0.85rem; display: flex; align-items: center; justify-content: center; }
.apg-home-domain-title { margin: 0; font-family: 'Space Grotesk', sans-serif; font-weight: 600; font-size: 1.05rem; }
.apg-home-domain-blurb { margin: 0; color: var(--apg-ink-soft); font-size: 0.88rem; line-height: 1.55; flex: 1; }
.apg-home-domain-cta { align-self: flex-start; display: inline-flex; align-items: center; gap: 6px; background: none; border: none; padding: 0; color: var(--apg-navy); font-weight: 600; font-size: 0.88rem; cursor: pointer; }
.apg-home-domain-cta svg { width: 15px; height: 15px; transition: transform 0.15s ease; }
.apg-home-domain-cta:hover svg { transform: translateX(3px); }

.apg-home-steps { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; }
@media (max-width: 960px) { .apg-home-steps { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 640px) { .apg-home-steps { grid-template-columns: 1fr; } }
.apg-home-step { display: flex; flex-direction: column; gap: 10px; }
.apg-home-step-num { font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 1.6rem; color: rgba(15,27,45,0.16); }
.apg-home-step-title { margin: 0; font-weight: 600; font-size: 1rem; }
.apg-home-step-body { margin: 0; color: var(--apg-ink-soft); font-size: 0.88rem; line-height: 1.55; }

.apg-home-feature-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 18px; }
@media (max-width: 820px) { .apg-home-feature-grid { grid-template-columns: 1fr; } }
.apg-home-feature-card { background: var(--apg-surface); border: 1px solid var(--apg-line); border-radius: var(--apg-r-md); padding: 24px; }
.apg-home-feature-icon { width: 42px; height: 42px; border-radius: 10px; background: rgba(31,138,99,0.12); color: var(--apg-teal); display: flex; align-items: center; justify-content: center; margin-bottom: 14px; }
.apg-home-feature-icon svg { width: 20px; height: 20px; }
.apg-home-feature-title { margin: 0 0 8px; font-family: 'Space Grotesk', sans-serif; font-weight: 600; font-size: 1rem; }
.apg-home-feature-body { margin: 0; color: var(--apg-ink-soft); font-size: 0.88rem; line-height: 1.6; }

.apg-home-faq-list { display: flex; flex-direction: column; gap: 10px; max-width: 760px; }
.apg-home-faq-item { border: 1px solid var(--apg-line); border-radius: var(--apg-r-md); background: var(--apg-surface); overflow: hidden; }
.apg-home-faq-q { width: 100%; display: flex; align-items: center; justify-content: space-between; gap: 16px; background: none; border: none; padding: 17px 20px; text-align: left; font-size: 0.95rem; font-weight: 600; color: var(--apg-ink); cursor: pointer; }
.apg-home-faq-q svg { width: 18px; height: 18px; flex-shrink: 0; color: var(--apg-ink-soft); transition: transform 0.2s ease; }
.apg-home-faq-item--open .apg-home-faq-q svg { transform: rotate(180deg); }
.apg-home-faq-a { margin: 0; padding: 0 20px 18px; color: var(--apg-ink-soft); font-size: 0.9rem; line-height: 1.6; }

.apg-home-cta-band { margin: 0 28px 72px; max-width: 1124px; margin-left: auto; margin-right: auto; background: linear-gradient(135deg, var(--apg-navy-soft), var(--apg-navy)); border-radius: var(--apg-r-lg); padding: 56px 40px; text-align: center; }
.apg-home-cta-title { margin: 0 0 12px; font-family: 'Space Grotesk', sans-serif; font-weight: 600; font-size: clamp(1.5rem, 3vw, 2rem); color: #fff; }
.apg-home-cta-sub { margin: 0 auto 28px; max-width: 48ch; color: rgba(255,255,255,0.7); font-size: 0.98rem; line-height: 1.6; }

.apg-home-footer { border-top: 1px solid var(--apg-line); padding: 28px; }
.apg-home-footer-inner { max-width: 1180px; margin: 0 auto; display: flex; align-items: center; justify-content: space-between; gap: 16px; flex-wrap: wrap; }
.apg-home-footer-brand { display: flex; align-items: center; gap: 10px; }
.apg-home-footer-name { margin: 0; font-family: 'Space Grotesk', sans-serif; font-weight: 600; font-size: 0.92rem; }
.apg-home-footer-tag { margin: 1px 0 0; font-size: 0.8rem; color: var(--apg-ink-soft); }
.apg-home-footer-copy { margin: 0; font-size: 0.8rem; color: var(--apg-ink-soft); }

@keyframes apg-home-bar { 0%, 100% { transform: scaleY(0.5); } 50% { transform: scaleY(1); } }
@keyframes apg-home-float { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-6px); } }
@media (prefers-reduced-motion: reduce) {
  .apg-home-preview-bars span { animation: none; }
  .apg-home-preview-float { animation: none; }
}
`;

/* ---------------------------- component ---------------------------- */

export default function LandingPage({ onStart }: LandingPageProps) {
  const [openFaq, setOpenFaq] = useState<number | null>(0);

  return (
    <div className="apg-home">
      <style>{LANDING_STYLES}</style>

      <nav className="apg-home-nav">
        <div className="apg-home-nav-brand">
          <span className="apg-home-nav-mark">A</span>
          <span className="apg-home-nav-name">Aptigrad</span>
        </div>
        <button className="apg-home-nav-cta" onClick={() => onStart()}>
          Start Free Mock Interview
        </button>
      </nav>

      <header className="apg-home-hero">
        <div>
          <span className="apg-home-eyebrow">Free · No signup · No resume needed</span>
          <h1 className="apg-home-hero-title">Practice technical interviews with an AI that actually talks back</h1>
          <p className="apg-home-hero-sub">
            Aptigrad runs a real, voice-based mock interview across six core CS domains, asking follow-up questions
            that get harder or easier depending on how you answer, live.
          </p>
          <div className="apg-home-hero-ctas">
            <button className="apg-home-btn apg-home-btn--gold" onClick={() => onStart()}>
              Start Free Mock Interview <IconArrowRight />
            </button>
          </div>
          <p className="apg-home-hero-note">Just a camera and a mic. Takes under a minute to set up.</p>
          <div className="apg-home-hero-reqs">
            <span><IconCamera /> Camera</span>
            <span><IconMic /> Microphone</span>
          </div>
        </div>

        <div className="apg-home-preview">
          <div className="apg-home-preview-top">
            <span className="apg-home-preview-dot" />
            Live mock interview
          </div>
          <div className="apg-home-preview-stage">
            <div className="apg-home-preview-badge">A</div>
            <p className="apg-home-preview-caption">Aptigrad is speaking&hellip;</p>
            <div className="apg-home-preview-bars" aria-hidden="true">
              <span /><span /><span /><span /><span />
            </div>
          </div>
          <p className="apg-home-preview-subtitle">
            &ldquo;Can you walk me through how a hash map resolves collisions?&rdquo;
          </p>
          <div className="apg-home-preview-float">
            <IconBolt /> Adaptive difficulty
          </div>
        </div>
      </header>

      <section className="apg-home-section">
        <div className="apg-home-section-head">
          <span className="apg-home-eyebrow">Six domains</span>
          <h2 className="apg-home-section-title">Pick a domain, Aptigrad adapts to you</h2>
          <p className="apg-home-section-sub">
            Every question is generated live and judged on how you actually answer, not matched against a canned
            script.
          </p>
        </div>
        <div className="apg-home-domain-grid">
          {DOMAINS.map((d) => (
            <div className="apg-home-domain-card" key={d.id}>
              <span className="apg-home-domain-tag">{DOMAIN_ABBR[d.id] ?? d.id.slice(0, 2).toUpperCase()}</span>
              <h3 className="apg-home-domain-title">{d.label}</h3>
              <p className="apg-home-domain-blurb">{d.blurb}</p>
              <button className="apg-home-domain-cta" onClick={() => onStart(d.id)}>
                Start practicing <IconArrowRight />
              </button>
            </div>
          ))}
        </div>
      </section>

      <section className="apg-home-section" style={{ paddingTop: 0 }}>
        <div className="apg-home-section-head">
          <span className="apg-home-eyebrow">How it works</span>
          <h2 className="apg-home-section-title">From cold start to interview-ready in four steps</h2>
        </div>
        <div className="apg-home-steps">
          {STEPS.map((s, i) => (
            <div className="apg-home-step" key={s.title}>
              <span className="apg-home-step-num">{String(i + 1).padStart(2, "0")}</span>
              <h3 className="apg-home-step-title">{s.title}</h3>
              <p className="apg-home-step-body">{s.body}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="apg-home-section" style={{ paddingTop: 0 }}>
        <div className="apg-home-section-head">
          <span className="apg-home-eyebrow">Why it works</span>
          <h2 className="apg-home-section-title">Built to feel like the real thing</h2>
        </div>
        <div className="apg-home-feature-grid">
          {FEATURES.map((f) => (
            <div className="apg-home-feature-card" key={f.title}>
              <span className="apg-home-feature-icon">{f.icon}</span>
              <h3 className="apg-home-feature-title">{f.title}</h3>
              <p className="apg-home-feature-body">{f.body}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="apg-home-section" style={{ paddingTop: 0 }}>
        <div className="apg-home-section-head">
          <span className="apg-home-eyebrow">FAQ</span>
          <h2 className="apg-home-section-title">Good to know before you start</h2>
        </div>
        <div className="apg-home-faq-list">
          {FAQ_ITEMS.map((item, i) => {
            const isOpen = openFaq === i;
            return (
              <div className={`apg-home-faq-item ${isOpen ? "apg-home-faq-item--open" : ""}`} key={item.q}>
                <button
                  className="apg-home-faq-q"
                  onClick={() => setOpenFaq(isOpen ? null : i)}
                  aria-expanded={isOpen}
                >
                  {item.q}
                  <IconChevronDown />
                </button>
                {isOpen && <p className="apg-home-faq-a">{item.a}</p>}
              </div>
            );
          })}
        </div>
      </section>

      <section className="apg-home-cta-band">
        <h2 className="apg-home-cta-title">Your next interview starts here</h2>
        <p className="apg-home-cta-sub">
          No scheduling, no resume upload &mdash; just your camera, your mic, and a question waiting.
        </p>
        <button className="apg-home-btn apg-home-btn--gold" onClick={() => onStart()}>
          Start Free Mock Interview <IconArrowRight />
        </button>
      </section>

      <footer className="apg-home-footer">
        <div className="apg-home-footer-inner">
          <div className="apg-home-footer-brand">
            <span className="apg-home-nav-mark">A</span>
            <div>
              <p className="apg-home-footer-name">Aptigrad</p>
              <p className="apg-home-footer-tag">AI mock interviews for technical rounds</p>
            </div>
          </div>
          <p className="apg-home-footer-copy">&copy; {new Date().getFullYear()} Aptigrad</p>
        </div>
      </footer>
    </div>
  );
}