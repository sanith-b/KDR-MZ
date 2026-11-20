import React, { useState } from 'react';
import { Search, Film, Send, ShieldCheck, Heart, Menu, X } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';

interface NavbarProps {
  onOpenRequest: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ onOpenRequest }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const navigate = useNavigate();

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/?q=${encodeURIComponent(searchQuery.trim())}`);
    }
  };

  return (
    <header className="sticky top-0 z-40 bg-slate-950/80 backdrop-blur-md border-b border-slate-800/80">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
        {/* Brand Logo */}
        <Link to="/" className="flex items-center gap-2.5 group">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-rose-600 to-pink-500 flex items-center justify-center shadow-lg shadow-rose-500/20 group-hover:scale-105 transition-transform">
            <Film className="w-5 h-5 text-white" />
          </div>
          <div>
            <span className="font-extrabold text-lg tracking-tight bg-gradient-to-r from-white via-slate-100 to-rose-300 bg-clip-text text-transparent">
              My K-Drama <span className="text-rose-500 font-mono text-sm ml-0.5">2.0</span>
            </span>
          </div>
        </Link>

        {/* Search Bar */}
        <form onSubmit={handleSearch} className="flex-1 max-w-md relative hidden md:block">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search dramas, actors, genres... (AI assisted)"
            className="w-full bg-slate-900/90 border border-slate-800 rounded-full pl-10 pr-4 py-1.5 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-rose-500/70 focus:ring-1 focus:ring-rose-500/50 transition-all"
          />
        </form>

        {/* Action Buttons */}
        <div className="flex items-center gap-3">
          <button
            onClick={onOpenRequest}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-sm font-medium bg-rose-600/10 text-rose-400 hover:bg-rose-600/20 border border-rose-500/30 transition-all hover:scale-105"
          >
            <Send className="w-3.5 h-3.5" />
            <span>Request Drama</span>
          </button>

          <a
            href="https://t.me/SupMyKDramaBot"
            target="_blank"
            rel="noopener noreferrer"
            className="hidden sm:flex items-center gap-1.5 px-4 py-1.5 rounded-full text-sm font-semibold bg-gradient-to-r from-rose-600 to-pink-600 hover:from-rose-500 hover:to-pink-500 text-white shadow-md shadow-rose-600/20 transition-all hover:scale-105"
          >
            <span>Open in Telegram</span>
          </a>
        </div>
      </div>
    </header>
  );
};
