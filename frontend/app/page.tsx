"use client";
import React, { useState, useEffect } from "react";

export default function HomePage() {
  const [activeTab, setActiveTab] = useState(0);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      const nav = document.getElementById("navbar");
      if (nav) nav.classList.toggle("scrolled", window.scrollY > 30);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <>
      {mobileMenuOpen && (
        <div style={{ position: "fixed", top: 70, left: 0, right: 0, background: "white", zIndex: 9998, borderBottom: "1px solid #e5e5e5", padding: "8px 0" }}>
          <a href="#home" style={{ display: "block", padding: "14px 28px", fontFamily: "'Josefin Sans',sans-serif", fontSize: "13px", fontWeight: 700, letterSpacing: "1.5px", textTransform: "uppercase", textDecoration: "none", color: "#2c2c2c", borderBottomWidth: 1, borderBottomColor: "#f0f0f0" }} onClick={() => setMobileMenuOpen(false)}>Home</a>
          <a href="#service-section" style={{ display: "block", padding: "14px 28px", fontFamily: "'Josefin Sans',sans-serif", fontSize: "13px", fontWeight: 700, letterSpacing: "1.5px", textTransform: "uppercase", textDecoration: "none", color: "#2c2c2c", borderBottomWidth: 1, borderBottomColor: "#f0f0f0" }} onClick={() => setMobileMenuOpen(false)}>Services</a>
          <a href="#about-section" style={{ display: "block", padding: "14px 28px", fontFamily: "'Josefin Sans',sans-serif", fontSize: "13px", fontWeight: 700, letterSpacing: "1.5px", textTransform: "uppercase", textDecoration: "none", color: "#2c2c2c", borderBottomWidth: 1, borderBottomColor: "#f0f0f0" }} onClick={() => setMobileMenuOpen(false)}>About us</a>
          <a href="#contact-section" style={{ display: "block", padding: "14px 28px", fontFamily: "'Josefin Sans',sans-serif", fontSize: "13px", fontWeight: 700, letterSpacing: "1.5px", textTransform: "uppercase", textDecoration: "none", color: "#2c2c2c" }} onClick={() => setMobileMenuOpen(false)}>Contact</a>
        </div>
      )}

      {/* HERO */}
      <section id="home">
        <div className="hero-inner">
          <div className="hero-text">
            <h1>Welcome to<br /><span>Paraline</span> VietNam</h1>
            <h2>Paraline was founded by members who had studied and worked in Japan, Australia. We promise to provide customers products with 「International Quality」 in Vietnam. With the goal of becoming one of the leading companies in Vietnam in software and IT services.</h2>
            <a href="#service-section" className="btn-explore">
              Explore
              <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
                <path d="M5 12h14M12 5l7 7-7 7" />
              </svg>
            </a>
          </div>
          <div className="hero-illustration">
            <div className="hero-svg-wrap">
              <svg viewBox="0 0 380 380" fill="none" xmlns="http://www.w3.org/2000/svg">
                <rect x="60" y="80" width="260" height="175" rx="12" fill="#2c2c2c" />
                <rect x="72" y="92" width="236" height="155" rx="6" fill="#27ae60" opacity="0.15" />
                <rect x="72" y="92" width="236" height="155" rx="6" fill="url(#screenGrad)" />
                <rect x="90" y="115" width="100" height="8" rx="4" fill="white" opacity="0.7" />
                <rect x="90" y="133" width="70" height="8" rx="4" fill="#27ae60" opacity="0.8" />
                <rect x="90" y="151" width="120" height="8" rx="4" fill="white" opacity="0.5" />
                <rect x="90" y="169" width="80" height="8" rx="4" fill="#27ae60" opacity="0.6" />
                <rect x="90" y="187" width="110" height="8" rx="4" fill="white" opacity="0.4" />
                <rect x="90" y="205" width="60" height="8" rx="4" fill="#27ae60" opacity="0.5" />
                <rect x="178" y="255" width="24" height="30" rx="3" fill="#2c2c2c" />
                <rect x="148" y="282" width="84" height="10" rx="5" fill="#2c2c2c" />
                <ellipse cx="295" cy="230" rx="28" ry="28" fill="#FFD4B2" />
                <rect x="267" y="255" width="56" height="60" rx="10" fill="#27ae60" />
                <path d="M323 260 Q355 235 358 210" stroke="#FFD4B2" strokeWidth="14" strokeLinecap="round" />
                <circle cx="358" cy="207" r="10" fill="#FFD4B2" />
                <path d="M267 265 Q250 280 248 295" stroke="#FFD4B2" strokeWidth="12" strokeLinecap="round" />
                <rect x="272" y="310" width="16" height="45" rx="8" fill="#2c2c2c" />
                <rect x="296" y="310" width="16" height="45" rx="8" fill="#2c2c2c" />
                <circle cx="285" cy="225" r="3" fill="#2c2c2c" />
                <circle cx="305" cy="225" r="3" fill="#2c2c2c" />
                <path d="M285 238 Q295 246 305 238" stroke="#2c2c2c" strokeWidth="2.5" strokeLinecap="round" fill="none" />
                <circle cx="50" cy="160" r="16" fill="#27ae60" opacity="0.15" />
                <defs>
                  <linearGradient id="screenGrad" x1="72" y1="92" x2="308" y2="247" gradientUnits="userSpaceOnUse">
                    <stop offset="0%" stopColor="#1a3a5c" />
                    <stop offset="100%" stopColor="#0d1f33" />
                  </linearGradient>
                </defs>
              </svg>
            </div>
          </div>
        </div>
      </section>

      {/* SERVICES */}
      <div id="service-section" style={{ background: "var(--bg)" }}>
        <div className="section-wrap">
          <div className="section-tag">Services</div>
          <h2 className="section-title">The services we provide</h2>
          <div className="divider"></div>

          <div className="services-tabs">
            {["01 Web Development", "02 Mobile Application", "03 System Integration", "04 Labor Service"].map((label, i) => (
              <button key={i} className={`tab-btn ${activeTab === i ? "active" : ""}`} onClick={() => setActiveTab(i)}>
                {label}
              </button>
            ))}
          </div>

          {activeTab === 0 && (
            <div className="service-content active">
              <div className="service-layout">
                <div className="service-icon-wrap">
                  <div className="service-num-big">01</div>
                </div>
                <div className="service-details">
                  <h3>Web Development</h3>
                  <p>
                    We apply new technologies to develop websites and web applications on a variety of platforms, aiming to bring the best user experience and business value.
                  </p>
                  <h4>Main services</h4>
                  <ul>
                    <li>Corporate website design & development</li>
                    <li>E-commerce website development</li>
                    <li>Custom web application development</li>
                    <li>Performance optimization & maintenance</li>
                    <li>System migration & integration</li>
                  </ul>
                  <div className="service-cols">
                    <div className="service-col">
                      <h4>Programming Languages</h4>
                      <ul>
                        <li>PHP</li>
                        <li>.NET (C#)</li>
                        <li>Ruby</li>
                        <li>Node.js</li>
                        <li>Java</li>
                        <li>Python</li>
                      </ul>
                    </div>
                    <div className="service-col">
                      <h4>Database</h4>
                      <ul>
                        <li>MySQL</li>
                        <li>SQL Server</li>
                        <li>PostgreSQL</li>
                        <li>MongoDB</li>
                        <li>Oracle</li>
                      </ul>
                    </div>
                    <div className="service-col">
                      <h4>Frameworks / CMS</h4>
                      <ul>
                        <li>Laravel</li>
                        <li>CakePHP</li>
                        <li>Ruby on Rails</li>
                        <li>Spring</li>
                        <li>Magento</li>
                        <li>WordPress</li>
                        <li>Next.js</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
          {activeTab === 1 && (
            <div className="service-content active">
              <div className="service-layout">
                <div className="service-icon-wrap">
                  <div className="service-num-big">02</div>
                </div>
                <div className="service-details">
                  <h3>Mobile Application Development</h3>
                  <p>
                    We have extensive experience in developing both public and enterprise mobile applications for iOS and Android platforms, ensuring high quality and user-friendly interfaces.
                  </p>
                  <h4>Main services</h4>
                  <ul>
                    <li>Native iOS & Android app development</li>
                    <li>Cross-platform app development (React Native, Flutter)</li>
                    <li>UI/UX design for mobile</li>
                    <li>App store publishing & management</li>
                    <li>Maintenance, bug fixing & updates</li>
                  </ul>
                  <div className="service-cols">
                    <div className="service-col">
                      <h4>Platforms</h4>
                      <ul>
                        <li>iOS (iPhone, iPad)</li>
                        <li>Android (Smartphone, Tablet)</li>
                      </ul>
                    </div>
                    <div className="service-col">
                      <h4>Technologies</h4>
                      <ul>
                        <li>Swift</li>
                        <li>Kotlin</li>
                        <li>Java</li>
                        <li>Objective-C</li>
                        <li>Dart</li>
                        <li>JavaScript/TypeScript</li>
                      </ul>
                    </div>
                    <div className="service-col">
                      <h4>Frameworks</h4>
                      <ul>
                        <li>React Native</li>
                        <li>Flutter</li>
                        <li>Android SDK</li>
                        <li>iOS SDK</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
          {activeTab === 2 && (
            <div className="service-content active">
              <div className="service-layout">
                <div className="service-icon-wrap">
                  <div className="service-num-big">03</div>
                </div>
                <div className="service-details">
                  <h3>System Integration</h3>
                  <p>
                    We provide end-to-end integration for enterprise systems, collaborating with leading partners to deliver reliable and secure IT infrastructure solutions.
                  </p>
                  <h4>Main services</h4>
                  <ul>
                    <li>Network design & deployment</li>
                    <li>Server & storage solutions</li>
                    <li>Security, backup & disaster recovery</li>
                    <li>Cloud migration & hybrid cloud</li>
                    <li>Enterprise software integration</li>
                  </ul>
                  <div className="service-cols">
                    <div className="service-col">
                      <h4>Vendors/Partners</h4>
                      <ul>
                        <li>HP</li>
                        <li>IBM</li>
                        <li>Cisco</li>
                        <li>Microsoft</li>
                        <li>Oracle</li>
                        <li>Symantec</li>
                      </ul>
                    </div>
                    <div className="service-col">
                      <h4>Technologies</h4>
                      <ul>
                        <li>VMware</li>
                        <li>Hyper-V</li>
                        <li>Windows Server</li>
                        <li>Linux</li>
                        <li>Active Directory</li>
                        <li>Exchange Server</li>
                      </ul>
                    </div>
                    <div className="service-col">
                      <h4>Solutions</h4>
                      <ul>
                        <li>Network & Security</li>
                        <li>Cloud (AWS, Azure, GCP)</li>
                        <li>Backup & Storage</li>
                        <li>Enterprise Integration</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
          {activeTab === 3 && (
            <div className="service-content active">
              <div className="service-layout">
                <div className="service-icon-wrap">
                  <div className="service-num-big">04</div>
                </div>
                <div className="service-details">
                  <h3>Labor Service (Labo)</h3>
                  <p>
                    We provide dedicated development teams (Labo) working on-site at our office, handling recruitment, payroll, and management so clients can focus on project delivery.
                  </p>
                  <h4>Main services</h4>
                  <ul>
                    <li>Dedicated developers, testers, or project teams</li>
                    <li>Flexible contract durations (short/long term)</li>
                    <li>Japanese-speaking coordinators available</li>
                    <li>Transparent cost & progress management</li>
                    <li>Full HR & payroll support</li>
                  </ul>
                  <div className="service-cols">
                    <div className="service-col">
                      <h4>Team Roles</h4>
                      <ul>
                        <li>Developers (Web, Mobile, Backend)</li>
                        <li>QA Engineers</li>
                        <li>Project Managers</li>
                        <li>BrSE (Bridge System Engineer)</li>
                        <li>UI/UX Designers</li>
                      </ul>
                    </div>
                    <div className="service-col">
                      <h4>Support</h4>
                      <ul>
                        <li>Japanese/English/Vietnamese communication</li>
                        <li>On-site/remote working options</li>
                        <li>Agile/Scrum process</li>
                        <li>Regular reporting</li>
                      </ul>
                    </div>
                    <div className="service-col">
                      <h4>Benefits</h4>
                      <ul>
                        <li>Cost transparency</li>
                        <li>Flexible scaling</li>
                        <li>Direct communication with team</li>
                        <li>HR & payroll handled by Paraline</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* QUOTES */}
      <div className="quotes-strip">
        <div className="quotes-track-wrapper">
          <div className="quotes-track">
            <div className="quote-card"><div className="quote-marks">"</div><p className="quote-text">Great things in business are never done by one person. They're done by a team of people.</p><span className="quote-author">— Steve Jobs</span></div>
            <div className="quote-card"><div className="quote-marks">"</div><p className="quote-text">If you can't make it good, at least make it look good.</p><span className="quote-author">— Bill Gates</span></div>
            <div className="quote-card"><div className="quote-marks">"</div><p className="quote-text">Great things in business are never done by one person. They're done by a team of people.</p><span className="quote-author">— Steve Jobs</span></div>
            <div className="quote-card"><div className="quote-marks">"</div><p className="quote-text">If you can't make it good, at least make it look good.</p><span className="quote-author">— Bill Gates</span></div>
          </div>
        </div>
      </div>

      {/* MEMBERS */}
      <div id="member-section">
        <div className="section-wrap">
          <div className="section-tag">Member</div>
          <h2 className="section-title">Meet the members of Paraline</h2>
          <div className="divider"></div>

          <div className="members-grid">
            {[
              { initials: "QP", name: "Quan Pham", role: "PHP Leader" },
              { initials: "TT", name: "Thu Thuy", role: "Japanese Communicator" },
              { initials: "QN", name: "Quy Nguyen", role: "PHP & Ruby Engineer" },
              { initials: "NM", name: "Nguyet Minh", role: "Tester Leader" },
              { initials: "TN", name: "Tuan Nguyen", role: "Android & iOS Engineer" },
              { initials: "GD", name: "Giang Duong", role: "System Engineer" },
            ].map((member) => (
              <div key={member.initials} className="member-card">
                <div className="member-avatar"><div className="member-avatar-initials">{member.initials}</div></div>
                <div className="member-name">{member.name}</div>
                <div className="member-role">{member.role}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* CUSTOMERS */}
      <div id="customer-section">
        <div className="section-wrap">
          <div className="section-tag">Customers</div>
          <h2 className="section-title">Our partners and customers</h2>
          <div className="divider"></div>

          <div className="partners-grid">
            {["ESSENCE", "NEXT IT", "e-novate", "PAX Creation", "Elentec", "PadITech", "Bach Khoa", "NPcore"].map((partner) => (
              <div key={partner} className="partner-item">
                <div className="partner-logo-placeholder">{partner}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ABOUT */}
      <div id="about-section">
        <div className="section-wrap">
          <div className="section-tag">About us</div>
          <h2 className="section-title">About Paraline</h2>
          <div className="divider"></div>

          <div className="about-grid">
            <div className="about-block">
              <h3>Company culture</h3>
              <div className="culture-list">
                <div className="culture-item">
                  <div className="culture-icon"></div>
                  <p>Each individual is company's asset. We are all building up the company together.</p>
                </div>
                <div className="culture-item">
                  <div className="culture-icon"></div>
                  <p>Work together, Happy together!</p>
                </div>
              </div>
            </div>

            <div className="about-block">
              <h3>Information</h3>
              <div className="info-table">
                <div className="info-row">
                  <div className="info-icon"></div>
                  <div className="info-content">
                    <div className="info-label">CEO</div>
                    <div className="info-value">Pham Van Quang</div>
                  </div>
                </div>
                <div className="info-row">
                  <div className="info-icon"></div>
                  <div className="info-content">
                    <div className="info-label">Company</div>
                    <div className="info-value">ParaLine VietNam Co., Ltd.</div>
                  </div>
                </div>
                <div className="info-row">
                  <div className="info-icon"></div>
                  <div className="info-content">
                    <div className="info-label">Tel</div>
                    <div className="info-value"><a href="tel:+842432004679">+84 24-3200-4679</a></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* CONTACT */}
      <div id="contact-section">
        <div className="section-wrap">
          <div className="section-tag">Contact</div>
          <h2 className="section-title">Please leave your comments about us</h2>
          <div className="divider"></div>

          <div className="contact-layout">
            <div className="contact-info-block">
              <div className="contact-info-item">
                <div className="contact-info-icon"></div>
                <div className="contact-info-text">
                  <p>Address</p>
                  <strong>15 Floor, Viwaseen Tower, 48 To Huu, Nam Tu Liem, Ha Noi, Vietnam</strong>
                </div>
              </div>
              <div className="contact-info-item">
                <div className="contact-info-icon"></div>
                <div className="contact-info-text">
                  <p>Phone</p>
                  <strong><a href="tel:+842432004679">+84 24-3200-4679</a></strong>
                </div>
              </div>
            </div>

            <div className="contact-form">
              <div className="form-row">
                <div className="form-group">
                  <label>Your Name *</label>
                  <input type="text" placeholder="Nguyen Van A" />
                </div>
                <div className="form-group">
                  <label>Email Address *</label>
                  <input type="email" placeholder="email@example.com" />
                </div>
              </div>
              <div className="form-group">
                <label>Message *</label>
                <textarea placeholder="Please describe your project or question..."></textarea>
              </div>
              <button className="btn-send">Send</button>
            </div>
          </div>
        </div>
      </div>

      {/* ACTIVITY */}
      <div id="activity-section" style={{ background: "var(--bg)" }}>
        <div className="section-wrap">
          <div className="section-tag">Activity</div>
          <h2 className="section-title">Life at Paraline</h2>
          <div className="divider"></div>

          <div className="activity-grid">
            {[
              { emoji: "", title: "Year End Party" },
              { emoji: "", title: "Report" },
              { emoji: "", title: "Daily meeting" },
              { emoji: "", title: "Soccer" },
              { emoji: "", title: "Party" },
              { emoji: "", title: "Team building" },
              { emoji: "", title: "Business trip" },
              { emoji: "", title: "Seminar" },
              { emoji: "", title: "Ha Long tour" },
            ].map((activity, i) => (
              <div key={i} className="activity-card" style={{ background: `linear-gradient(135deg, hsl(${i * 40},50%,20%), hsl(${i * 40},50%,35%))` }}>
                <div className="activity-thumb">{activity.emoji}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* FOOTER */}
      <footer>
        <div className="footer-main">
          <div>
            <div style={{ fontSize: "20px", fontWeight: 700, letterSpacing: "3px", textTransform: "uppercase", color: "white", marginBottom: "14px" }}>
              Para<span style={{ color: "#27ae60" }}>line</span>
            </div>
            <p className="footer-desc">Founded by members who had studied and worked in Japan, Australia. Providing products with 「International Quality」 in Vietnam.</p>
            <p style={{ fontSize: "13px", color: "rgba(255,255,255,0.3)" }}> 2017. Made with <span className="footer-heart"></span> in Hanoi</p>
          </div>
          <div className="footer-col">
            <h4>Navigation</h4>
            <ul>
              <li><a href="#home">Home</a></li>
              <li><a href="#service-section">Services</a></li>
              <li><a href="#about-section">About us</a></li>
              <li><a href="#contact-section">Contact</a></li>
            </ul>
          </div>
          <div className="footer-col">
            <h4>Services</h4>
            <ul>
              <li><a href="#service-section">Web Development</a></li>
              <li><a href="#service-section">Mobile Application</a></li>
            </ul>
          </div>
          <div className="footer-col">
            <h4>Contact</h4>
            <ul>
              <li><a href="tel:+842432004679">+84 24-3200-4679</a></li>
              <li><a href="https://www.facebook.com/ParalineVietnam" target="_blank" rel="noreferrer">Facebook</a></li>
            </ul>
          </div>
        </div>
        <div className="footer-bottom">
          <p> 2017. ParaLine VietNam Co., Ltd. All rights reserved.</p>
          <p>Made with <span className="footer-heart"></span> in Hanoi</p>
        </div>
      </footer>
    </>
  );
}

