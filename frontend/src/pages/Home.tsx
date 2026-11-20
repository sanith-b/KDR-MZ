import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Sparkles, Flame, Play, Clock, Film } from 'lucide-react';
import { api } from '../services/api';
import { TMDbDrama } from '../types';
import { DramaCard } from '../components/DramaCard';

export const Home: React.FC = () => {
  const [searchParams] = useSearchParams();
  const query = searchParams.get('q') || '';
  const [dramas, setDramas] = useState<TMDbDrama[]>([]);
  const [correctedQuery, setCorrectedQuery] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        if (query) {
          const res = await api.searchDramas(query);
          setDramas(res.tmdb_matches || []);
          setCorrectedQuery(res.corrected_query || null);
        } else {
          // Default popular Korean dramas
          const res = await api.searchDramas("Queen of Tears");
          setDramas(res.tmdb_matches || []);
          setCorrectedQuery(null);
        }
      } catch (err) {
        console.error("Failed to load catalog", err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [query]);

  return (
    <div className="space-y-10 pb-16">
      {/* Hero Banner (Shown when not searching) */}
      {!query && (
        <div className="relative rounded-3xl overflow-hidden border border-slate-800 bg-slate-900 shadow-2xl">
          <div className="absolute inset-0 bg-gradient-to-r from-slate-950 via-slate-950/80 to-transparent z-10" />
          <img
            src="https://images.unsplash.com/photo-1578328819058-b69f3a3b0f6b?w=1600&auto=format&fit=crop&q=80"
            alt="Hero Banner"
            className="w-full h-80 sm:h-96 object-cover object-center"
          />
          <div className="absolute inset-0 z-20 flex flex-col justify-center px-6 sm:px-12 max-w-2xl">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-rose-500/20 text-rose-300 border border-rose-500/30 w-fit mb-3">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Next-Gen K-Drama Experience</span>
            </div>
            <h1 className="text-3xl sm:text-5xl font-black text-white tracking-tight leading-tight">
              Stream, Search & Request <span className="bg-gradient-to-r from-rose-400 to-pink-500 bg-clip-text text-transparent">Korean Dramas</span>
            </h1>
            <p className="mt-3 text-sm sm:text-base text-slate-300 line-clamp-2">
              Integrated with our high-speed Telegram Bot network. Watch high-definition series directly in browser or download via bot.
            </p>
            <div className="mt-6 flex items-center gap-3">
              <a
                href="#catalog"
                className="px-6 py-2.5 rounded-full font-bold text-sm bg-rose-600 hover:bg-rose-500 text-white shadow-lg shadow-rose-600/30 flex items-center gap-2 transition-all hover:scale-105"
              >
                <Play className="w-4 h-4 fill-current" />
                <span>Explore Catalog</span>
              </a>
            </div>
          </div>
        </div>
      )}

      {/* Search Header / Corrected Banner */}
      {query && (
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5">
          <h2 className="text-xl font-extrabold text-white">
            Search results for: <span className="text-rose-400 font-mono">"{query}"</span>
          </h2>
          {correctedQuery && (
            <div className="mt-2 text-sm text-slate-300 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-amber-400 shrink-0" />
              <span>
                Gemini AI normalized title to: <strong className="text-white">"{correctedQuery}"</strong>
              </span>
            </div>
          )}
        </div>
      )}

      {/* Catalog Grid */}
      <div id="catalog" className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Flame className="w-5 h-5 text-rose-500" />
            <h2 className="text-xl font-bold text-white tracking-tight">
              {query ? 'Matched Korean Dramas' : 'Trending Now'}
            </h2>
          </div>
        </div>

        {loading ? (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
            {[...Array(10)].map((_, i) => (
              <div key={i} className="aspect-[2/3] rounded-2xl bg-slate-900 animate-pulse border border-slate-800" />
            ))}
          </div>
        ) : dramas.length > 0 ? (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4 sm:gap-6">
            {dramas.map((drama) => (
              <DramaCard key={drama.id} drama={drama} />
            ))}
          </div>
        ) : (
          <div className="text-center py-16 bg-slate-900/40 rounded-3xl border border-slate-800/60 p-8">
            <Film className="w-12 h-12 text-slate-600 mx-auto mb-3" />
            <h3 className="text-lg font-bold text-slate-200">No dramas found</h3>
            <p className="text-sm text-slate-400 mt-1 max-w-sm mx-auto">
              We couldn't locate any title matching your query. Use the request button above to request it from our team!
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
