<!-- version: 4.1 (Optimized) -->
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
    <title>skawiskawi.pl - skawiskawiskawiskawi</title>
    <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'><defs><linearGradient id='grad' x1='0%' y1='100%' x2='100%' y2='0%'><stop offset='0%' stop-color='%236366f1'/><stop offset='50%' stop-color='%23d946ef'/><stop offset='100%' stop-color='%2306b6d4'/></linearGradient></defs><rect width='64' height='64' rx='16' fill='%23090a0f'/><path d='M16 40V24M24 48V16M32 44V20M40 52V12M48 38V26' stroke='url(%23grad)' stroke-width='5' stroke-linecap='round'/></svg>">
    <script defer src="https://cloud.umami.is/script.js" data-website-id="f37d28ec-ae34-4c10-8203-84ead5f71cbd"></script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-dark: #050608;
            --card-bg: rgba(255, 255, 255, 0.035);
            --card-border: rgba(255, 255, 255, 0.08);
            --card-hover-bg: rgba(255, 255, 255, 0.07);
            --text-main: #f8fafc;
            --text-muted: #64748b;
            --dynamic-accent: #1ed760;
            --dynamic-accent-2: #6366f1;
            --bpm-speed-mult: 1;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            -webkit-tap-highlight-color: transparent;
        }


        html, body {
            width: 100%;
            min-height: 100dvh;
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
            background-color: var(--bg-dark);
            color: var(--text-main);
            overflow-y: auto;
            overflow-x: hidden;
        }

        .spotify-bg-blur {
            position: fixed; top: -10%; left: -10%; width: 120vw; height: 120vh;
            background-size: cover; background-position: center; background-repeat: no-repeat;
            filter: blur(50px) saturate(120%); opacity: 0; z-index: 0; pointer-events: none;
            transition: opacity 1.5s ease; will-change: opacity; transform: translateZ(0);
        }

        #interactive-bg, #strobe-container {
            position: fixed; top: 0; left: 0; width: 100vw; height: 100dvh; pointer-events: none;
        }

        #interactive-bg { z-index: 1; }
        
        #strobe-container { z-index: 2; overflow: hidden; }

        .strobe-flash {
            position: absolute; border-radius: 50%;
            background: radial-gradient(circle at center, rgba(255, 255, 255, 0.28) 0%, rgba(255, 255, 255, 0.12) 35%, rgba(255, 255, 255, 0.03) 65%, transparent 100%);
            filter: blur(18px); opacity: 0; mix-blend-mode: screen; transform: translate(-50%, -50%);
            transition: opacity 0.06s ease-out; will-change: opacity;
        }

        .noise-overlay {
            position: fixed; top: 0; left: 0; width: 100vw; height: 100dvh; pointer-events: none;
            z-index: 3; opacity: 0.035; mix-blend-mode: overlay; background-repeat: repeat;
            background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E");
        }

        .container {
            position: relative; z-index: 5; width: 100%; min-height: 100dvh; display: flex;
            flex-direction: column; justify-content: space-between; align-items: center;
            padding: clamp(16px, 2.5vh, 28px) 20px;
            padding-top: max(clamp(16px, 2.5vh, 28px), env(safe-area-inset-top));
            padding-bottom: max(clamp(16px, 2.5vh, 28px), env(safe-area-inset-bottom));
            perspective: 1000px;
        }

        .header-spacer { height: 1px; }

        .main-content {
            width: 100%; max-width: 310px; display: flex; flex-direction: column;
            align-items: center; gap: clamp(12px, 2vh, 18px); margin: auto 0;
        }

        .sound-wave-container {
            width: 100%; height: 52px; display: flex; align-items: center; justify-content: center;
            position: relative; user-select: none; transition: opacity 0.5s ease;
            animation: stagger-in 0.8s cubic-bezier(0.16, 1, 0.3, 1) both; animation-delay: 0.05s; overflow: visible;
        }

        #soundwave-canvas { width: 100%; height: 100%; display: block; }

        .links-wrapper { width: 100%; display: flex; flex-direction: column; gap: 8px; }

        .link-btn {
            position: relative; display: flex; align-items: center; justify-content: center; gap: 10px;
            width: 100%; min-height: 40px; padding: 9px 16px; background: var(--card-bg);
            border: 1px solid var(--card-border); border-radius: 12px; color: var(--text-main);
            text-decoration: none; font-size: 0.86rem; font-weight: 600; letter-spacing: 0.3px;
            backdrop-filter: blur(24px) saturate(140%); -webkit-backdrop-filter: blur(24px) saturate(140%);
            transition: transform 0.18s cubic-bezier(0.25, 1, 0.5, 1), background 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25); transform-style: preserve-3d; will-change: transform;
            animation: stagger-in 0.7s cubic-bezier(0.16, 1, 0.3, 1) both;
        }

        .link-btn svg { width: 17px; height: 17px; fill: currentColor; flex-shrink: 0; transition: transform 0.2s ease; }

        .links-wrapper a:nth-child(1) { animation-delay: 0.10s; }
        .links-wrapper a:nth-child(2) { animation-delay: 0.16s; }
        .links-wrapper a:nth-child(3) { animation-delay: 0.22s; }
        .links-wrapper div:nth-child(4) { animation-delay: 0.26s; }
        .links-wrapper a:nth-child(5) { animation-delay: 0.30s; }
        .links-wrapper div:nth-child(6) { animation-delay: 0.34s; }
        .links-wrapper a:nth-child(7) { animation-delay: 0.38s; }

        @keyframes stagger-in {
            0% { opacity: 0; transform: translateY(18px) scale(0.96); }
            100% { opacity: 1; transform: translateY(0) scale(1); }
        }

        @media (hover: hover) {
            .link-btn:hover { background: var(--card-hover-bg); }
            .link-btn.spotify:hover { border-color: rgba(30, 215, 96, 0.4); box-shadow: 0 0 18px rgba(30, 215, 96, 0.2); }
            .link-btn.genius:hover { border-color: rgba(255, 225, 0, 0.4); box-shadow: 0 0 18px rgba(255, 225, 0, 0.2); }
            .link-btn.statsfm:hover { border-color: rgba(168, 85, 247, 0.4); box-shadow: 0 0 18px rgba(168, 85, 247, 0.2); }
            .link-btn.fortnite:hover { border-color: rgba(56, 189, 248, 0.4); box-shadow: 0 0 18px rgba(56, 189, 248, 0.2); }
            .link-btn.github:hover { border-color: rgba(255, 255, 255, 0.4); box-shadow: 0 0 18px rgba(255, 255, 255, 0.2); }
            .link-btn:active { transform: scale(0.97) !important; }
        }

        .section-divider {
            display: flex; align-items: center; justify-content: center; width: 100%;
            margin: 4px 0 2px 0; gap: 12px; animation: stagger-in 0.7s cubic-bezier(0.16, 1, 0.3, 1) both;
        }

        .section-divider::before, .section-divider::after {
            content: ''; flex: 1; height: 1px; background: rgba(255, 255, 255, 0.08);
        }

        .section-divider span {
            font-size: 0.6rem; font-weight: 700; text-transform: uppercase;
            letter-spacing: 1.5px; color: rgba(255, 255, 255, 0.3);
        }

        .spotify-widget {
            width: 100%; margin-top: 2px; padding: 9px 13px 11px 13px;
            background: rgba(255, 255, 255, 0.025); border: 1px solid rgba(255, 255, 255, 0.07);
            border-radius: 16px; backdrop-filter: blur(28px) saturate(150%);
            -webkit-backdrop-filter: blur(28px) saturate(150%); display: flex; align-items: center; gap: 12px;
            text-decoration: none; color: inherit; transition: transform 0.18s cubic-bezier(0.25, 1, 0.5, 1), background 0.3s ease, border-color 0.3s ease, box-shadow 0.3s ease;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.35); position: relative; overflow: hidden;
            will-change: transform; transform-style: preserve-3d;
            animation: stagger-in 0.7s cubic-bezier(0.16, 1, 0.3, 1) both; animation-delay: 0.44s;
        }

        .spotify-widget::before {
            content: ''; position: absolute; top: -50%; left: -50%; width: 200%; height: 200%;
            background: conic-gradient(transparent, var(--dynamic-accent), transparent, var(--dynamic-accent-2));
            animation: border-beam 4s linear infinite; z-index: 0; opacity: 0.4; pointer-events: none;
        }

        .spotify-widget::after {
            content: ''; position: absolute; inset: 1px; background: #090a0f;
            border-radius: 15px; z-index: 0; pointer-events: none;
        }

        @keyframes border-beam {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .spotify-widget-content { position: relative; z-index: 1; display: flex; align-items: center; gap: 12px; width: 100%; }

        .album-cover-wrapper {
            position: relative; width: 40px; height: 40px; flex-shrink: 0; border-radius: 8px;
            overflow: hidden; background: rgba(255, 255, 255, 0.05);
            box-shadow: 0 0 16px var(--dynamic-accent); transition: box-shadow 0.8s ease;
        }

        .album-cover { width: 100%; height: 100%; object-fit: cover; border-radius: 8px; }

        .track-info { display: flex; flex-direction: column; justify-content: center; min-width: 0; flex: 1; }

        .status-badge {
            display: flex; align-items: center; gap: 5px; font-size: 0.62rem; font-weight: 600;
            text-transform: uppercase; letter-spacing: 0.8px; color: var(--dynamic-accent);
            margin-bottom: 2px; transition: color 0.8s ease;
        }

        .eq-mini {
            display: flex; align-items: flex-end; gap: 1.5px; height: 12px; overflow: visible;
        }

        .eq-bar {
            width: 1.5px; height: 100%; background-color: var(--dynamic-accent);
            transform-origin: bottom; will-change: transform; transform: scaleY(0.2);
            animation: eq-bounce 0.8s ease-in-out infinite alternate; transition: background-color 0.8s ease;
        }

        .eq-bar:nth-child(1) { animation-duration: 0.5s; }
        .eq-bar:nth-child(2) { animation-duration: 0.7s; }
        .eq-bar:nth-child(3) { animation-duration: 0.4s; }

        @keyframes eq-bounce {
            0% { transform: scaleY(0.2); }
            100% { transform: scaleY(1); }
        }

        .track-title {
            font-size: 0.80rem; font-weight: 700; color: var(--text-main);
            white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
        }

        .track-artist {
            font-size: 0.70rem; color: var(--text-muted); white-space: nowrap;
            overflow: hidden; text-overflow: ellipsis; margin-top: 1px;
        }

        .progress-bar-container {
            position: absolute; bottom: 0; left: 0; width: 100%; height: 2.5px;
            background: rgba(255, 255, 255, 0.08); z-index: 2;
        }

        .progress-bar {
            height: 100%; width: 0%; background: linear-gradient(90deg, var(--dynamic-accent), var(--dynamic-accent-2));
            transition: width 0.4s linear;
        }

        .contact-wrapper {
            margin-top: 6px; margin-bottom: 2px; animation: stagger-in 0.7s cubic-bezier(0.16, 1, 0.3, 1) both; animation-delay: 0.48s;
        }

        .contact-icon-btn {
            display: inline-flex; align-items: center; justify-content: center; width: 36px; height: 36px;
            border-radius: 50%; background: var(--card-bg); border: 1px solid var(--card-border);
            color: var(--text-muted); text-decoration: none; backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
            box-shadow: 0 4px 14px rgba(0, 0, 0, 0.2);
            transition: transform 0.18s cubic-bezier(0.25, 1, 0.5, 1), background 0.2s ease, border-color 0.2s ease, color 0.2s ease, box-shadow 0.2s ease;
            will-change: transform; transform-style: preserve-3d;
        }

        .contact-icon-btn svg { width: 16px; height: 16px; fill: currentColor; transition: transform 0.2s ease; }

        @media (hover: hover) {
            .contact-icon-btn:hover {
                background: var(--card-hover-bg); color: var(--text-main); border-color: var(--dynamic-accent);
                box-shadow: 0 0 16px var(--dynamic-accent); transform: scale(1.08) translateY(-2px);
            }
            .contact-icon-btn:active { transform: scale(0.94) !important; }
        }

        footer { text-align: center; margin-top: 10px; animation: stagger-in 0.7s cubic-bezier(0.16, 1, 0.3, 1) both; animation-delay: 0.52s; }

        .footer-text {
            font-size: clamp(0.75rem, 2vw, 0.85rem); font-weight: 500; letter-spacing: 6px;
            background: linear-gradient(135deg, #94a3b8, #cbd5e1); -webkit-background-clip: text;
            -webkit-text-fill-color: transparent; text-transform: lowercase; user-select: none; padding-left: 6px;
        }

        @media (max-width: 768px) {
            #interactive-bg { opacity: 0.95; filter: saturate(1.1); }
        }

        @media (max-height: 600px) {
            .sound-wave-container { display: none; }
        }
    </style>
</head>
<body>
    <div class="spotify-bg-blur" id="spotify-bg-1"></div>
    <div class="spotify-bg-blur" id="spotify-bg-2"></div>
    <div class="noise-overlay"></div>
    <canvas id="interactive-bg"></canvas>
    <div id="strobe-container"></div>
    <div class="container">
        <div class="header-spacer"></div>
        <div class="main-content">
            <div class="sound-wave-container" id="sound-wave-wrapper">
                <canvas id="soundwave-canvas"></canvas>
            </div>
            <main class="links-wrapper">
                <a href="https://open.spotify.com/user/313sruf6nyv7gp4wo5bnyon5wqf4" target="_blank" rel="noopener noreferrer" class="link-btn spotify tilt-card" data-umami-event="click-spotify">
                    <svg viewBox="0 0 24 24"><path d="M12 0C5.376 0 0 5.376 0 12s5.376 12 12 12 12-5.376 12-12S18.624 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.899 4.62-1.02 8.58-.6 11.7 1.32.42.18.48.66.24 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141 C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.18-1.38-.72-.18-.6.18-1.2.72-1.38 4.26-1.26 11.28-1.02 15.72 1.621.539.3.719 1.02.419 1.56-.299.421-1.02.599-1.559.3z"/></svg> Spotify
                </a>
                <a href="https://genius.com/skawi" target="_blank" rel="noopener noreferrer" class="link-btn genius tilt-card" data-umami-event="click-genius">
                    <svg viewBox="0 0 24 24"><path d="M24 0H0v24h24V0zM4.8 19.2V4.8h4.8v14.4H4.8zm9.6 0h-3.6V4.8h3.6v14.4zm4.8 0h-3.6V4.8h3.6v14.4z"/></svg> Genius
                </a>
                <a href="https://stats.fm/skawi" target="_blank" rel="noopener noreferrer" class="link-btn statsfm tilt-card" data-umami-event="click-statsfm">
                    <svg viewBox="0 0 24 24"><path d="M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z"/></svg> Stats.fm
                </a>
                <div class="section-divider"> <span>gaming</span> </div>
                <a href="https://fortnitetracker.com/profile/all/skawi" target="_blank" rel="noopener noreferrer" class="link-btn fortnite tilt-card" data-umami-event="click-fortnite">
                    <svg viewBox="0 0 24 24"><path d="M21 6H3c-1.1 0-2 .9-2 2v8c0 1.1.9 2 2 2h18c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2zm-10 7H9v2H7v-2H5v-2h2V9h2v2h2v2zm4.5 1c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5zm3-3c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5z"/></svg> Fortnite Tracker
                </a>
                <div class="section-divider"> <span>code</span> </div>
                <a href="https://github.com/skawiskawi" target="_blank" rel="noopener noreferrer" class="link-btn github tilt-card" data-umami-event="click-github">
                    <svg viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg> GitHub
                </a>
            </main>
            <a id="spotify-card" href="#" target="_blank" class="spotify-widget tilt-card" data-umami-event="click-spotify-widget">
                <div class="spotify-widget-content">
                    <div class="album-cover-wrapper">
                        <img id="spotify-cover" class="album-cover" src="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%2364748b'><path d='M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z'/></svg>" alt="Album Cover">
                    </div>
                    <div class="track-info">
                        <div class="status-badge">
                            <!-- Poprawka: startowo przezroczyste i gotowe na płynne pojawienie się -->
                            <div class="eq-mini" id="eq-icon" style="display: none; opacity: 0; transition: opacity 0.3s ease;">
                                <div class="eq-bar"></div>
                                <div class="eq-bar"></div>
                                <div class="eq-bar"></div>
                            </div>
                            <span id="spotify-status-text">Spotify</span>
                        </div>
                        <div id="spotify-title" class="track-title">Sprawdzanie...</div>
                        <div id="spotify-artist" class="track-artist">Ładowanie odtwarzacza</div>
                    </div>
                </div>
                <div class="progress-bar-container">
                    <div id="spotify-progress" class="progress-bar"></div>
                </div>
            </a>
            <div class="contact-wrapper">
                <a href="https://t.me/pawulonrulon" target="_blank" rel="noopener noreferrer" class="contact-icon-btn tilt-card" title="Napisz na Telegramie" aria-label="Telegram" data-umami-event="click-telegram">
                    <svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.64 6.8c-.15 1.58-.8 5.42-1.13 7.19-.14.75-.42 1-.68 1.03-.58.05-1.02-.38-1.58-.75-.88-.58-1.38-.94-2.23-1.5-.99-.65-.35-1.01.22-1.59.15-.15 2.71-2.48 2.76-2.69.01-.03.01-.14-.05-.2-.06-.05-.16-.03-.24-.02-.11.02-1.79 1.14-5.06 3.35-.48.33-.91.49-1.3.48-.43-.01-1.25-.24-1.86-.44-.75-.24-1.35-.37-1.3-.78.03-.21.32-.43.89-.66 3.5-1.52 5.83-2.53 7-3.01 3.33-1.39 4.02-1.63 4.48-1.64.1 0 .32.02.47.14.12.1.16.24.17.34 0 .07.01.21 0 .28z"/></svg>
                </a>
            </div>
        </div>
        <footer>
            <div class="footer-text">come stai</div>
        </footer>
    </div>
    <script>
        document.addEventListener('DOMContentLoaded', () => {
            let targetHue1 = 200;
            let targetHue2 = 300;
            let currentHue1 = 200;
            let currentHue2 = 300;
            let isGrayscale = false;
            let lastTrackId = null;
            let currentBpm = 120;
            let isMusicActive = false;
            let activeBgBuffer = 1;
            let currentBgUrl = '';

            /* ==========================================================================
               INTERACTIVE BACKGROUND CANVAS
               ========================================================================== */
            const canvas = document.getElementById('interactive-bg');
            if (canvas) {
                const ctx = canvas.getContext('2d');
                let width = canvas.width = window.innerWidth;
                let height = canvas.height = window.innerHeight;
                let mouse = { x: width / 2, y: height / 2, targetX: width / 2, targetY: height / 2 };
                let isTouching = false;
                let blobs = [];

                function initBlobs() {
                    const isMobile = width < 768;
                    const baseDim = Math.min(width, height);
                    const baseRadius = isMobile ? baseDim * 0.76 : Math.max(520, baseDim * 0.65);
                    blobs = [
                        { xRatio: 0.3, yRatio: 0.3, radius: baseRadius * 1.25, type: 1, speed: 0.0008, factor: isMobile ? 0.25 : 0.25 },
                        { xRatio: 0.7, yRatio: 0.65, radius: baseRadius * 1.35, type: 2, speed: 0.00065, factor: isMobile ? -0.25 : -0.25 },
                        { xRatio: 0.5, yRatio: 0.45, radius: baseRadius * 1.15, type: 1, speed: 0.0010, factor: isMobile ? 0.30 : 0.30 },
                        { xRatio: 0.25, yRatio: 0.8, radius: baseRadius * 1.20, type: 2, speed: 0.00055, factor: isMobile ? -0.20 : -0.20 }
                    ];
                }
                
                initBlobs();
                
                window.addEventListener('resize', () => {
                    width = canvas.width = window.innerWidth;
                    height = canvas.height = window.innerHeight;
                    initBlobs();
                });

                function updatePointer(e) {
                    let touch = e.touches ? e.touches[0] : null;
                    const x = touch ? touch.clientX : e.clientX;
                    const y = touch ? touch.clientY : e.clientY;
                    if (x !== undefined && y !== undefined) {
                        mouse.targetX = x;
                        mouse.targetY = y;
                        isTouching = true;
                    }
                }
                
                window.addEventListener('mousemove', updatePointer);
                window.addEventListener('touchstart', updatePointer, { passive: true });
                window.addEventListener('touchmove', updatePointer, { passive: true });

                function lerpHue(current, target, factor) {
                    let diff = (target - current) % 360;
                    if (diff < -180) diff += 360;
                    if (diff > 180) diff -= 360;
                    return (current + diff * factor + 360) % 360;
                }
                
                let time = 0;
                
                function renderCanvas() {
                    time += 1;
                    const isMobile = width < 768;
                    const orbitMultiplierX = isMobile ? 0.30 : 0.25;
                    const orbitMultiplierY = isMobile ? 0.30 : 0.25;
                    
                    if (!isTouching) {
                        mouse.targetX = width / 2 + Math.sin(time * 0.007) * (width * (isMobile ? 0.35 : 0.35));
                        mouse.targetY = height / 2 + Math.cos(time * 0.005) * (height * (isMobile ? 0.35 : 0.35));
                    }
                    
                    mouse.x += (mouse.targetX - mouse.x) * 0.05;
                    mouse.y += (mouse.targetY - mouse.y) * 0.05;
                    
                    currentHue1 = lerpHue(currentHue1, targetHue1, 0.02);
                    currentHue2 = lerpHue(currentHue2, targetHue2, 0.02);
                    
                    ctx.clearRect(0, 0, width, height);
                    
                    blobs.forEach((blob, index) => {
                        const baseX = width * blob.xRatio;
                        const baseY = height * blob.yRatio;
                        const orbitX = Math.sin(time * blob.speed + index * 2) * (width * orbitMultiplierX);
                        const orbitY = Math.cos(time * blob.speed * 0.8 + index) * (height * orbitMultiplierY);
                        const mouseOffsetX = (mouse.x - width / 2) * blob.factor;
                        const mouseOffsetY = (mouse.y - height / 2) * blob.factor;
                        const currentX = (baseX + orbitX + mouseOffsetX);
                        const currentY = (baseY + orbitY + mouseOffsetY);
                        const hue = blob.type === 1 ? currentHue1 : currentHue2;
                        
                        let colorCenter, colorEdge;
                        if (isGrayscale) {
                            colorCenter = `hsla(0, 0%, 35%, 0.30)`;
                            colorEdge = `hsla(0, 0%, 35%, 0)`;
                        } else {
                            colorCenter = `hsla(${hue}, 85%, 55%, 0.48)`;
                            colorEdge = `hsla(${hue}, 85%, 55%, 0)`;
                        }
                        
                        const gradient = ctx.createRadialGradient(currentX, currentY, 0, currentX, currentY, blob.radius);
                        gradient.addColorStop(0, colorCenter);
                        gradient.addColorStop(1, colorEdge);
                        
                        ctx.fillStyle = gradient;
                        ctx.beginPath();
                        ctx.arc(currentX, currentY, blob.radius, 0, Math.PI * 2);
                        ctx.fill();
                    });
                    
                    requestAnimationFrame(renderCanvas);
                }
                
                renderCanvas();
            }

            /* ==========================================================================
               STROBE FLASHES
               ========================================================================== */
            const strobeContainer = document.getElementById('strobe-container');
            let strobeTimeoutId = null;
            
            function triggerMultiFlash() {
                if (!strobeContainer) return;
                const count = (Math.floor(Math.random() * 3) + 2) * 2;
                const elements = [];
                for (let i = 0; i < count; i++) {
                    const flash = document.createElement('div');
                    flash.className = 'strobe-flash';
                    const size = Math.floor(Math.random() * 250) + 350;
                    const posX = Math.random() * window.innerWidth;
                    const posY = Math.random() * window.innerHeight;
                    flash.style.width = `${size}px`;
                    flash.style.height = `${size}px`;
                    flash.style.left = `${posX}px`;
                    flash.style.top = `${posY}px`;
                    strobeContainer.appendChild(flash);
                    elements.push(flash);
                }
                
                requestAnimationFrame(() => {
                    const targetOpacity = (Math.random() * 0.15 + 0.12).toFixed(2);
                    elements.forEach(el => el.style.opacity = targetOpacity);
                    const speedMult = Math.max(0.45, Math.min(1.8, 120 / currentBpm));
                    const flashDuration = (Math.random() * 60 + 50) * speedMult;
                    
                    setTimeout(() => {
                        elements.forEach(el => {
                            el.style.opacity = '0';
                            setTimeout(() => el.remove(), 120);
                        });
                    }, flashDuration);
                    
                    const nextInterval = (60000 / Math.max(50, Math.min(220, currentBpm))) * (Math.random() * 0.4 + 1.2);
                    strobeTimeoutId = setTimeout(triggerMultiFlash, nextInterval);
                });
            }
            
            setTimeout(triggerMultiFlash, 750);

            /* ==========================================================================
               ORGANIC LIQUID WAVEFORM & EKG ENGINE (CANVAS)
               ========================================================================== */
            const waveCanvas = document.getElementById('soundwave-canvas');
            if (waveCanvas) {
                const wCtx = waveCanvas.getContext('2d');
                let cssWidth = 310;
                let waveBufferPadding = 60;
                let wWidth = cssWidth + waveBufferPadding;
                let wHeight = 52;
                let dpr = window.devicePixelRatio || 1;
                let isMobileCanvas = false;

                function resizeWaveCanvas() {
                    // Mobile optimization: Cap devicePixelRatio na 1.5 na telefonach żeby ratować GPU Canvas
                    isMobileCanvas = window.innerWidth < 768;
                    dpr = isMobileCanvas ? Math.min(window.devicePixelRatio || 1, 1.5) : (window.devicePixelRatio || 1);
                    
                    const rect = waveCanvas.getBoundingClientRect();
                    cssWidth = rect.width || 310;
                    wWidth = cssWidth + waveBufferPadding;
                    wHeight = rect.height || 52;
                    waveCanvas.width = Math.round(wWidth * dpr);
                    waveCanvas.height = Math.round(wHeight * dpr);
                    wCtx.setTransform(dpr, 0, 0, dpr, waveBufferPadding / 2 * dpr, 0);
                }
                
                window.addEventListener('resize', resizeWaveCanvas);
                resizeWaveCanvas();
                
                let wavePhase1 = 0;
                let wavePhase2 = 0;
                let wavePhase3 = 0;
                let currentAmp = 0;
                let ekgTime = 0;
                
                function getEkgSpike(norm) {
                    if (Math.abs(norm) > 1) return 0;
                    const r = Math.exp(-(norm * norm) * 140) * 18;
                    const q = -Math.exp(-((norm + 0.09) * (norm + 0.09)) * 200) * 4.5;
                    const s = -Math.exp(-((norm - 0.09) * (norm - 0.09)) * 180) * 6.5;
                    const p = Math.exp(-((norm + 0.32) * (norm + 0.32)) * 40) * 2.8;
                    const t = Math.exp(-((norm - 0.35) * (norm - 0.35)) * 28) * 3.5;
                    return r + q + s + p + t;
                }
                
                function renderLiquidWave() {
                    const targetAmp = isMusicActive ? 1 : 0;
                    currentAmp += (targetAmp - currentAmp) * 0.05;
                    const bpmFactor = Math.max(0.6, Math.min(2.0, currentBpm / 120));
                    wavePhase1 += 0.045 * bpmFactor;
                    wavePhase2 += 0.032 * bpmFactor;
                    wavePhase3 += 0.058 * bpmFactor;
                    ekgTime += 0.016;
                    
                    wCtx.clearRect(-waveBufferPadding, 0, wWidth + waveBufferPadding, wHeight);
                    const centerY = wHeight / 2;
                    const accent1 = isGrayscale ? 'hsl(0, 0%, 70%)' : `hsl(${currentHue1}, 85%, 60%)`;
                    const accent2 = isGrayscale ? 'hsl(0, 0%, 55%)' : `hsl(${currentHue2}, 85%, 60%)`;
                    const drawStart = -waveBufferPadding / 2;
                    const drawEnd = cssWidth + waveBufferPadding / 2;
                    
                    if (currentAmp > 0.01) {
                        wCtx.save();
                        // Mobile optimization: Wyłączenie renderowania cieni na mobile (wymagają masy passów GPU w canvasie)
                        if (!isMobileCanvas) {
                            wCtx.shadowColor = accent1;
                            wCtx.shadowBlur = 8;
                        }
                        
                        wCtx.beginPath();
                        for (let x = drawStart; x <= drawEnd; x += 2) {
                            const normX = (x - drawStart) / (drawEnd - drawStart);
                            const envelope = Math.sin(normX * Math.PI) ** 1.3;
                            const y = centerY - (Math.sin(x * 0.032 + wavePhase3) * 8 + Math.cos(x * 0.015 - wavePhase3 * 0.7) * 5) * envelope * currentAmp;
                            if (x === drawStart) wCtx.moveTo(x, y);
                            else wCtx.lineTo(x, y);
                        }
                        
                        const grad3 = wCtx.createLinearGradient(0, 0, cssWidth, 0);
                        grad3.addColorStop(0, 'rgba(0, 0, 0, 0)');
                        grad3.addColorStop(0.18, isGrayscale ? 'rgba(200, 200, 200, 0.25)' : `hsla(${currentHue1}, 90%, 75%, ${0.35 * currentAmp})`);
                        grad3.addColorStop(0.82, isGrayscale ? 'rgba(200, 200, 200, 0.25)' : `hsla(${currentHue1}, 90%, 75%, ${0.35 * currentAmp})`);
                        grad3.addColorStop(1, 'rgba(0, 0, 0, 0)');
                        wCtx.strokeStyle = grad3;
                        wCtx.lineWidth = 1.6;
                        wCtx.stroke();
                        wCtx.restore();
                        
                        wCtx.save();
                        if (!isMobileCanvas) {
                            wCtx.shadowColor = accent2;
                            wCtx.shadowBlur = 12;
                        }
                        
                        wCtx.beginPath();
                        for (let x = drawStart; x <= drawEnd; x += 2) {
                            const normX = (x - drawStart) / (drawEnd - drawStart);
                            const envelope = Math.sin(normX * Math.PI) ** 1.2;
                            const y = centerY - (Math.sin(x * 0.020 - wavePhase2 + 1.2) * 12 + Math.cos(x * 0.035 + wavePhase2 * 0.6) * 6) * envelope * currentAmp;
                            if (x === drawStart) wCtx.moveTo(x, y);
                            else wCtx.lineTo(x, y);
                        }
                        const grad2 = wCtx.createLinearGradient(0, 0, cssWidth, 0);
                        grad2.addColorStop(0, 'rgba(0, 0, 0, 0)');
                        grad2.addColorStop(0.15, isGrayscale ? 'rgba(255, 255, 255, 0.4)' : `hsla(${currentHue2}, 85%, 65%, ${0.65 * currentAmp})`);
                        grad2.addColorStop(0.85, isGrayscale ? 'rgba(255, 255, 255, 0.4)' : `hsla(${currentHue2}, 85%, 65%, ${0.65 * currentAmp})`);
                        grad2.addColorStop(1, 'rgba(0, 0, 0, 0)');
                        wCtx.strokeStyle = grad2;
                        wCtx.lineWidth = 2.2;
                        wCtx.stroke();
                        wCtx.restore();
                        
                        wCtx.save();
                        if (!isMobileCanvas) {
                            wCtx.shadowColor = accent1;
                            wCtx.shadowBlur = 16;
                        }
                        
                        const waveGrad = wCtx.createLinearGradient(0, 0, cssWidth, 0);
                        waveGrad.addColorStop(0, 'rgba(0, 0, 0, 0)');
                        waveGrad.addColorStop(0.15, accent1);
                        waveGrad.addColorStop(0.5, '#ffffff');
                        waveGrad.addColorStop(0.85, accent2);
                        waveGrad.addColorStop(1, 'rgba(0, 0, 0, 0)');
                        
                        wCtx.beginPath();
                        for (let x = drawStart; x <= drawEnd; x += 2) {
                            const normX = (x - drawStart) / (drawEnd - drawStart);
                            const envelope = Math.sin(normX * Math.PI) ** 1.1;
                            const y = centerY - (Math.sin(x * 0.024 + wavePhase1) * Math.cos(x * 0.012 + wavePhase1 * 0.6) * 16 + Math.sin(x * 0.048 - wavePhase1 * 1.1) * 3) * envelope * currentAmp;
                            if (x === drawStart) wCtx.moveTo(x, y);
                            else wCtx.lineTo(x, y);
                        }
                        wCtx.strokeStyle = waveGrad;
                        wCtx.lineWidth = 2.8;
                        wCtx.stroke();
                        wCtx.restore();
                    }
                    
                    if (currentAmp < 0.99) {
                        const flatlineWeight = 1 - currentAmp;
                        const cycle = ekgTime % 3.6;
                        const pulseDuration = 1.1;
                        let pulseX = -100;
                        let isPulsing = false;
                        if (cycle < pulseDuration) {
                            isPulsing = true;
                            const progress = cycle / pulseDuration;
                            pulseX = progress * (cssWidth + 80) - 40;
                        }
                        
                        wCtx.save();
                        if (!isMobileCanvas) {
                            wCtx.shadowColor = accent1;
                            wCtx.shadowBlur = 10;
                        }
                        
                        wCtx.beginPath();
                        let activePeakX = -1;
                        let activePeakY = centerY;
                        for (let x = drawStart; x <= drawEnd; x += 2) {
                            let ekgOffset = 0;
                            if (isPulsing) {
                                const dx = x - pulseX;
                                const windowHalf = 28;
                                if (Math.abs(dx) <= windowHalf) {
                                    const norm = dx / windowHalf;
                                    ekgOffset = getEkgSpike(norm) * flatlineWeight;
                                    if (ekgOffset > 10) {
                                        activePeakX = x;
                                        activePeakY = centerY - ekgOffset;
                                    }
                                }
                            }
                            const tremor = Math.sin(ekgTime * 10 + x * 0.08) * 0.4 * flatlineWeight;
                            const y = centerY - ekgOffset + tremor;
                            if (x === drawStart) wCtx.moveTo(x, y);
                            else wCtx.lineTo(x, y);
                        }
                        
                        const flatGrad = wCtx.createLinearGradient(0, 0, cssWidth, 0);
                        flatGrad.addColorStop(0, 'rgba(0, 0, 0, 0)');
                        flatGrad.addColorStop(0.18, `hsla(${currentHue1}, 70%, 55%, ${0.25 * flatlineWeight})`);
                        flatGrad.addColorStop(0.5, `hsla(0, 0%, 100%, ${0.85 * flatlineWeight})`);
                        flatGrad.addColorStop(0.82, `hsla(${currentHue2}, 70%, 55%, ${0.25 * flatlineWeight})`);
                        flatGrad.addColorStop(1, 'rgba(0, 0, 0, 0)');
                        wCtx.strokeStyle = flatGrad;
                        wCtx.lineWidth = 1.8;
                        wCtx.stroke();
                        
                        if (activePeakX > drawStart && activePeakX < drawEnd) {
                            wCtx.beginPath();
                            wCtx.arc(activePeakX, activePeakY, 2.5, 0, Math.PI * 2);
                            wCtx.fillStyle = '#ffffff';
                            wCtx.shadowColor = '#ffffff';
                            wCtx.shadowBlur = isMobileCanvas ? 0 : 14;
                            wCtx.fill();
                        }
                        wCtx.restore();
                    }
                    
                    requestAnimationFrame(renderLiquidWave);
                }
                
                renderLiquidWave();
            }

            /* ==========================================================================
               PALETTE EXTRACTION
               ========================================================================== */
            function extractPaletteFromUrl(imageUrl) {
                return new Promise((resolve) => {
                    if (!imageUrl) return resolve(null);
                    const img = new Image();
                    img.crossOrigin = 'Anonymous';
                    img.src = imageUrl;
                    img.onload = () => {
                        try {
                            const c = document.createElement('canvas');
                            const ctx = c.getContext('2d');
                            c.width = 64;
                            c.height = 64;
                            ctx.drawImage(img, 0, 0, 64, 64);
                            const data = ctx.getImageData(0, 0, 64, 64).data;
                            
                            const buckets = {};
                            let totalSat = 0, sampleCount = 0;
                            for (let i = 0; i < data.length; i += 16) {
                                const r = data[i], g = data[i+1], b = data[i+2];
                                const max = Math.max(r, g, b) / 255;
                                const min = Math.min(r, g, b) / 255;
                                const lum = (max + min) / 2;
                                if (lum < 0.12 || lum > 0.90) continue;
                                let sat = 0;
                                if (max !== min) {
                                    sat = lum > 0.5 ? (max - min) / (2 - max - min) : (max - min) / (max + min);
                                }
                                totalSat += sat;
                                sampleCount++;
                                let hue = 0;
                                if (max !== min) {
                                    const d = max - min;
                                    const rN = r / 255, gN = g / 255, bN = b / 255;
                                    switch (max) {
                                        case rN: hue = (gN - bN) / d + (gN < bN ? 6 : 0); break;
                                        case gN: hue = (bN - rN) / d + 2; break;
                                        case bN: hue = (rN - gN) / d + 4; break;
                                    }
                                    hue = Math.round(hue * 60);
                                }
                                const hBucket = Math.round(hue / 25) * 25;
                                const score = 1 + (sat * 3);
                                buckets[hBucket] = (buckets[hBucket] || 0) + score;
                            }
                            const avgSat = sampleCount > 0 ? (totalSat / sampleCount) : 0;
                            if (avgSat < 0.12) {
                                return resolve({ isGrayscale: true, c1: 200, c2: 300 });
                            }
                            const sorted = Object.entries(buckets).sort((a, b) => b[1] - a[1]);
                            if (sorted.length === 0) return resolve(null);
                            const primaryHue = parseInt(sorted[0][0], 10);
                            let secondaryHue = (primaryHue + 60) % 360;
                            for (let j = 1; j < sorted.length; j++) {
                                const cand = parseInt(sorted[j][0], 10);
                                const diff = Math.abs(cand - primaryHue);
                                if (diff > 35 && diff < 325) {
                                    secondaryHue = cand;
                                    break;
                                }
                            }
                            resolve({ isGrayscale: false, c1: primaryHue, c2: secondaryHue });
                        } catch (err) {
                            resolve(null);
                        }
                    };
                    img.onerror = () => resolve(null);
                });
            }

            /* ==========================================================================
               3D TILT EFFECT
               ========================================================================== */
            const tiltCards = document.querySelectorAll('.tilt-card');
            tiltCards.forEach(card => {
                card.addEventListener('mousemove', (e) => {
                    const rect = card.getBoundingClientRect();
                    const x = e.clientX - rect.left;
                    const y = e.clientY - rect.top;
                    const centerX = rect.width / 2;
                    const centerY = rect.height / 2;
                    const rotateX = ((y - centerY) / centerY) * -7;
                    const rotateY = ((x - centerX) / centerX) * 7;
                    const transX = ((x - centerX) / centerX) * 4;
                    const transY = ((y - centerY) / centerY) * 4;
                    card.style.transform = `perspective(1000px) translate3d(${transX}px, ${transY}px, 0) rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
                });
                card.addEventListener('mouseleave', () => {
                    card.style.transform = `perspective(1000px) translate3d(0px, 0px, 0) rotateX(0deg) rotateY(0deg)`;
                });
            });

            /* ==========================================================================
               SPOTIFY API INTEGRATION (Zabezpieczone przez Cloudflare Pages)
               ========================================================================== */
            async function getSpotifyStatus() {
                try {
                    const res = await fetch('/api/spotify');
                    if (res.ok) {
                        return await res.json();
                    }
                    return { isPlaying: false, isRecentlyPlayed: false };
                } catch (err) {
                    return { isPlaying: false, isRecentlyPlayed: false };
                }
            }

            async function updateSpotifyCard() {
                const track = await getSpotifyStatus();
                const card = document.getElementById('spotify-card');
                const cover = document.getElementById('spotify-cover');
                const title = document.getElementById('spotify-title');
                const artist = document.getElementById('spotify-artist');
                const statusText = document.getElementById('spotify-status-text');
                const eqIcon = document.getElementById('eq-icon');
                const progressBar = document.getElementById('spotify-progress');
                
                if (!card || !cover || !title || !artist || !statusText || !eqIcon || !progressBar) return;
                
                if (track.title) {
                    if (track.id && track.id !== lastTrackId) {
                        lastTrackId = track.id;
                        currentBpm = track.tempo || 120;
                        const speedMultiplier = Math.max(0.45, Math.min(1.8, 120 / currentBpm));
                        document.documentElement.style.setProperty('--bpm-speed-mult', speedMultiplier.toFixed(2));
                    }
                    if (cover.dataset.rawSrc !== track.albumImageUrl) {
                        cover.dataset.rawSrc = track.albumImageUrl;
                        cover.src = track.albumImageUrl;
                        
                        // LOGIKA DOUBLE BUFFER
                        if (currentBgUrl !== track.albumImageUrl) {
                            currentBgUrl = track.albumImageUrl;
                            const nextBuffer = activeBgBuffer === 1 ? 2 : 1;
                            const bgNext = document.getElementById(`spotify-bg-${nextBuffer}`);
                            const bgCurrent = document.getElementById(`spotify-bg-${activeBgBuffer}`);
                            
                            if (bgNext && bgCurrent) {
                                bgNext.style.backgroundImage = `url('${track.albumImageUrl}')`;
                                bgNext.style.opacity = '0.15'; // Pokazujemy nowy bufor
                                bgCurrent.style.opacity = '0'; // Ukrywamy stary bufor
                                activeBgBuffer = nextBuffer; // Aktualizujemy wskazanie na aktywny bufor
                            }
                        }
                        
                        extractPaletteFromUrl(track.albumImageUrl).then(colors => {
                            if (!colors) return;
                            if (colors.isGrayscale) {
                                isGrayscale = true;
                                document.documentElement.style.setProperty('--dynamic-accent', '#94a3b8');
                                document.documentElement.style.setProperty('--dynamic-accent-2', '#cbd5e1');
                            } else {
                                isGrayscale = false;
                                targetHue1 = colors.c1;
                                targetHue2 = colors.c2;
                                document.documentElement.style.setProperty('--dynamic-accent', `hsl(${colors.c1}, 70%, 55%)`);
                                document.documentElement.style.setProperty('--dynamic-accent-2', `hsl(${colors.c2}, 70%, 55%)`);
                            }
                        });
                    }
                    
                    title.innerText = track.title;
                    artist.innerText = track.artist;
                    card.href = track.songUrl || 'https://open.spotify.com';
                    
                    if (track.isPlaying) {
                        statusText.innerText = 'Now Playing';
                        eqIcon.style.display = 'flex';
                        setTimeout(() => { eqIcon.style.opacity = '1'; }, 10);
                        isMusicActive = true;
                        
                        if (track.progressMs && track.durationMs) {
                            const pct = (track.progressMs / track.durationMs) * 100;
                            progressBar.style.width = `${pct}%`;
                        }
                    } else {
                        statusText.innerText = 'Ostatnio słuchane';
                        eqIcon.style.opacity = '0';
                        setTimeout(() => { eqIcon.style.display = 'none'; }, 300);
                        progressBar.style.width = '0%';
                        isMusicActive = false;
                    }
                } else {
                    title.innerText = 'Brak aktywności';
                    artist.innerText = 'Nic obecnie nie leci';
                    card.href = 'https://open.spotify.com';
                    statusText.innerText = 'Spotify';
                    eqIcon.style.opacity = '0';
                    setTimeout(() => { eqIcon.style.display = 'none'; }, 300);
                    progressBar.style.width = '0%';
                    currentBpm = 120;
                    document.documentElement.style.setProperty('--bpm-speed-mult', '1');
                    isMusicActive = false;
                    
                    // Ukrycie obu tła przy braku aktywności
                    const bg1 = document.getElementById('spotify-bg-1');
                    const bg2 = document.getElementById('spotify-bg-2');
                    if (bg1) bg1.style.opacity = '0';
                    if (bg2) bg2.style.opacity = '0';
                    currentBgUrl = ''; // reset, żeby nowy utwór załadował się poprawnie
                }
            }
            
            updateSpotifyCard();
            setInterval(updateSpotifyCard, 5000);
        });
    </script>
</body>
</html>