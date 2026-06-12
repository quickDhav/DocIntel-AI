'use client';

/* ============================================================
   DocIntel AI — Navbar Component
   ============================================================ */

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

export default function Navbar() {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);

  const links = [
    { href: '/chat', label: 'Chat', id: 'nav-chat' },
    { href: '/upload', label: 'Upload', id: 'nav-upload' },
  ];

  return (
    <nav className="navbar" id="navbar">
      <div className="navbar-inner">
        {/* Logo */}
        <Link href="/chat" className="navbar-logo" id="navbar-logo">
          <div className="navbar-logo-icon">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
              <line x1="16" y1="13" x2="8" y2="13" />
              <line x1="16" y1="17" x2="8" y2="17" />
              <polyline points="10 9 9 9 8 9" />
            </svg>
          </div>
          <span className="text-gradient">DocIntel AI</span>
        </Link>

        {/* Desktop Nav */}
        <div className={`navbar-nav${mobileOpen ? ' open' : ''}`} id="navbar-nav">
          {links.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              id={link.id}
              className={`navbar-link${pathname === link.href || pathname?.startsWith(link.href + '/') ? ' active' : ''}`}
              onClick={() => setMobileOpen(false)}
            >
              {link.label}
            </Link>
          ))}
        </div>

        {/* Mobile Toggle */}
        <button
          className="navbar-mobile-toggle"
          id="navbar-mobile-toggle"
          onClick={() => setMobileOpen(!mobileOpen)}
          aria-label="Toggle navigation"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            {mobileOpen ? (
              <>
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </>
            ) : (
              <>
                <line x1="3" y1="6" x2="21" y2="6" />
                <line x1="3" y1="12" x2="21" y2="12" />
                <line x1="3" y1="18" x2="21" y2="18" />
              </>
            )}
          </svg>
        </button>
      </div>
    </nav>
  );
}
