import React from 'react';
import { Star, Play, Calendar } from 'lucide-react';
import { Link } from 'react-router-dom';
import { TMDbDrama } from '../types';

interface DramaCardProps {
  drama: TMDbDrama;
}

export const DramaCard: React.FC<DramaCardProps> = ({ drama }) => {
  const fallbackPoster = 'https://images.unsplash.com/photo-1518676590629-3dcbd9c5a5c9?w=500&auto=format&fit=crop&q=80';

  return (
    <Link
      to={`/drama/${drama.id}`}
      className="group relative flex flex-col rounded-2xl overflow-hidden bg-slate-900/60 border border-slate-800/60 hover:border-rose-500/50 hover:shadow-xl hover:shadow-rose-500/10 transition-all duration-300 hover:-translate-y-1.5"
    >
      {/* Poster Image */}
      <div className="aspect-[2/3] w-full overflow-hidden relative bg-slate-800">
        <img
          src={drama.poster_url || fallbackPoster}
          alt={drama.name}
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
          loading="lazy"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-slate-950/20 to-transparent opacity-80 group-hover:opacity-60 transition-opacity" />

        {/* Rating Badge */}
        {drama.vote_average ? (
          <div className="absolute top-2.5 right-2.5 bg-slate-950/80 backdrop-blur-md px-2 py-0.5 rounded-full border border-amber-500/30 flex items-center gap-1 shadow-md">
            <Star className="w-3 h-3 text-amber-400 fill-amber-400" />
            <span className="text-xs font-bold text-amber-300">{drama.vote_average.toFixed(1)}</span>
          </div>
        ) : null}

        {/* Play Overlay Button */}
        <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
          <div className="w-12 h-12 rounded-full bg-rose-600/90 text-white flex items-center justify-center shadow-lg shadow-rose-600/40 backdrop-blur-sm group-hover:scale-110 transition-transform">
            <Play className="w-5 h-5 ml-0.5 fill-current" />
          </div>
        </div>
      </div>

      {/* Content Info */}
      <div className="p-3.5 flex flex-col flex-1">
        <h3 className="font-bold text-sm text-slate-100 line-clamp-1 group-hover:text-rose-400 transition-colors">
          {drama.name}
        </h3>
        <div className="mt-1 flex items-center gap-2 text-xs text-slate-400">
          {drama.year && (
            <span className="flex items-center gap-1">
              <Calendar className="w-3 h-3" />
              {drama.year}
            </span>
          )}
          {drama.original_name && drama.original_name !== drama.name && (
            <span className="line-clamp-1 italic text-slate-500">• {drama.original_name}</span>
          )}
        </div>
      </div>
    </Link>
  );
};
