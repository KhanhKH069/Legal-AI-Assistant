"use client";

import "./globals.css";

// metadata moved to app/metadata.ts so layout can remain a client component

export default function RootLayout({
  children
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="vi">
      <body className="para-app-root">
        <nav id="navbar">
          <a href="#home" className="nav-logo" aria-label="Paraline home">
            <svg width="165" height="40" viewBox="0 0 165 40" fill="none" xmlns="http://www.w3.org/2000/svg">
              <polygon points="19,3 34,11 19,19 4,11" fill="#2ecc71"/>
              <polygon points="4,11 19,19 19,36 4,28" fill="#1a9448"/>
              <polygon points="34,11 19,19 19,36 34,28" fill="#27ae60"/>
              <line x1="19" y1="3"  x2="34" y2="11" stroke="rgba(255,255,255,0.4)" strokeWidth="0.6"/>
              <line x1="19" y1="3"  x2="4"  y2="11" stroke="rgba(255,255,255,0.4)" strokeWidth="0.6"/>
              <line x1="4"  y1="11" x2="19" y2="19" stroke="rgba(255,255,255,0.25)" strokeWidth="0.6"/>
              <line x1="34" y1="11" x2="19" y2="19" stroke="rgba(255,255,255,0.15)" strokeWidth="0.6"/>
              <text x="46" y="28" fontFamily="'Josefin Sans', 'Trebuchet MS', Arial, sans-serif" fontSize="23" fontWeight="700" letterSpacing="1" fill="#27ae60">paraline</text>
            </svg>
          </a>

          <div className="nav-right">
            <ul className="nav-links">
              <li><a href="#home" className="active">Home</a></li>
              <li><a href="#service-section">Services</a></li>
              <li><a href="#about-section">About us</a></li>
              <li><a href="#contact-section">Contact</a></li>
            </ul>

            <div className="nav-flags">
              <button className="flag-btn" title="日本語">
                <svg width="24" height="16" viewBox="0 0 24 16"><rect width="24" height="16" fill="#fff"/><circle cx="12" cy="8" r="4.5" fill="#BC002D"/></svg>
              </button>
              <button className="flag-btn" title="Tiếng Việt">
                <svg width="24" height="16" viewBox="0 0 24 16"><rect width="24" height="16" fill="#DA251D"/><polygon points="12,3.5 13.5,8 18,8 14.3,10.5 15.7,15 12,12.5 8.3,15 9.7,10.5 6,8 10.5,8" fill="#FFFF00"/></svg>
              </button>
              <button className="flag-btn" title="English">
                <svg width="24" height="16" viewBox="0 0 24 16"><rect width="24" height="16" fill="#012169"/><path d="M0,0 L24,16 M24,0 L0,16" stroke="white" strokeWidth="2.5"/><path d="M0,0 L24,16 M24,0 L0,16" stroke="#C8102E" strokeWidth="1.5"/><path d="M12,0 V16 M0,8 H24" stroke="white" strokeWidth="4"/><path d="M12,0 V16 M0,8 H24" stroke="#C8102E" strokeWidth="2.5"/></svg>
              </button>
            </div>

            {/* Only one AI Chat icon, top right, larger and more prominent */}
            <a className="chat-nav-btn" id="chatFab" href="/chat" style={{ marginLeft: 32, display: 'flex', alignItems: 'center', padding: '0 18px', height: 54, borderRadius: 12, background: 'linear-gradient(135deg, #27ae60 60%, #1e8449 100%)', boxShadow: '0 4px 24px 0 rgba(39,174,96,0.18)' }}>
              <svg width="32" height="32" fill="none" stroke="#fff" strokeWidth="2.5" viewBox="0 0 24 24" style={{ marginRight: 12 }}>
                <rect x="2" y="7" width="20" height="10" rx="5" fill="#27ae60" stroke="#fff" strokeWidth="2.5"/>
                <path d="M7 17v2a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2v-2" stroke="#fff" strokeWidth="2.5"/>
                <circle cx="12" cy="12" r="3" fill="#fff"/>
              </svg>
              <span id="chatFabIcon" style={{ color: '#fff', fontWeight: 700, fontSize: 18, letterSpacing: 1 }}>AI Chat</span>
            </a>
          </div>

          <button className="hamburger" aria-label="Menu">
            <span></span><span></span><span></span>
          </button>
        </nav>

        <div className="para-layout">
          <main className="para-main-content">{children}</main>
        </div>

      </body>
    </html>
  );
}

