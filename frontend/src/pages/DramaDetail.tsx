import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Star, Calendar, Layers, Play, Download, ArrowLeft, Tv, ShieldCheck } from 'lucide-react';
import { api } from '../services/api';
import { TMDbDrama, MediaFile } from '../types';

export const DramaDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [drama, setDrama] = useState<TMDbDrama | null>(null);
  const [files, setFiles] = useState<MediaFile[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDrama = async () => {
      if (!id) return;
      setLoading(true);
      try {
        const res = await api.getDramaDetails(parseInt(id, 10));
        setDrama(res.metadata);
        setFiles(res.available_files || []);
      } catch (err) {
        console.error("Failed to load drama details", err);
      } finally {
        setLoading(false);
      }
    };
    fetchDrama();
  }, [id]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="w-10 h-10 border-4 border-rose-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!drama) {
    return (
      <div className="text-center py-20">
        <h2 className="text-xl font-bold text-white">Drama not found</h2>
        <Link to="/" className="text-rose-400 mt-2 inline-block">Return to home</Link>
      </div>
    );
  }

  return (
    <div className="space-y-10 pb-20">
      <Link to="/" className="inline-flex items-center gap-2 text-sm font-semibold text-slate-400 hover:text-white transition-colors">
        <ArrowLeft className="w-4 h-4" />
        <span>Back to catalog</span>
      </Link>

      {/* Backdrop & Header Banner */}
      <div className="relative rounded-3xl overflow-hidden border border-slate-800 bg-slate-900 shadow-2xl">
        {drama.backdrop_url && (
          <div className="absolute inset-0">
            <img
              src={drama.backdrop_url}
              alt={drama.name}
              className="w-full h-full object-cover opacity-25 filter blur-xs"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-slate-950/80 to-transparent" />
          </div>
        )}

        <div className="relative z-10 p-6 sm:p-10 flex flex-col md:flex-row gap-8 items-start">
          {/* Poster */}
          <div className="w-48 sm:w-60 aspect-[2/3] shrink-0 rounded-2xl overflow-hidden shadow-2xl border border-slate-700/80 bg-slate-800">
            <img
              src={drama.poster_url || ''}
              alt={drama.name}
              className="w-full h-full object-cover"
            />
          </div>

          {/* Metadata */}
          <div className="flex-1 space-y-4">
            <div>
              <div className="flex items-center gap-2.5 flex-wrap">
                {drama.vote_average && (
                  <span className="px-2.5 py-1 rounded-full text-xs font-black bg-amber-500/20 text-amber-300 border border-amber-500/40 flex items-center gap-1">
                    <Star className="w-3.5 h-3.5 fill-amber-400" />
                    {drama.vote_average.toFixed(1)} TMDb
                  </span>
                )}
                {drama.year && (
                  <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-800 text-slate-300 border border-slate-700 flex items-center gap-1">
                    <Calendar className="w-3.5 h-3.5" />
                    {drama.year}
                  </span>
                )}
                {drama.number_of_seasons && (
                  <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-800 text-slate-300 border border-slate-700 flex items-center gap-1">
                    <Tv className="w-3.5 h-3.5" />
                    {drama.number_of_seasons} Seasons
                  </span>
                )}
              </div>
              <h1 className="text-3xl sm:text-4xl font-extrabold text-white mt-3 tracking-tight">
                {drama.name}
              </h1>
              {drama.original_name && (
                <p className="text-slate-400 italic text-base mt-0.5">{drama.original_name}</p>
              )}
            </div>

            {drama.genres && (
              <div className="text-xs font-bold text-rose-400 uppercase tracking-wider">
                {drama.genres}
              </div>
            )}

            <p className="text-sm sm:text-base text-slate-300 leading-relaxed max-w-3xl">
              {drama.overview || 'No synopsis available for this drama.'}
            </p>

            {drama.cast && (
              <div className="text-xs text-slate-400 pt-2 border-t border-slate-800/80">
                <span className="font-bold text-slate-300">Starring: </span>
                {drama.cast}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Available Episodes & Files */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Layers className="w-5 h-5 text-rose-500" />
            <h2 className="text-xl font-bold text-white tracking-tight">Available Files & Episodes</h2>
          </div>
          <span className="text-xs font-semibold text-slate-400">{files.length} files detected</span>
        </div>

        {files.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {files.map((file) => (
              <div
                key={file._id}
                className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 flex items-center justify-between gap-4 hover:border-slate-700 transition-colors"
              >
                <div className="min-w-0 flex-1">
                  <h4 className="text-sm font-bold text-slate-200 truncate">{file.file_name}</h4>
                  <p className="text-xs text-slate-500 mt-0.5 font-mono">
                    {(file.file_size / (1024 * 1024)).toFixed(1)} MB • {file.file_type || 'video'}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <a
                    href={`https://t.me/SupMyKDramaBot?start=file_0_${file._id}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="p-2 rounded-xl bg-rose-600/20 text-rose-400 hover:bg-rose-600 hover:text-white transition-all"
                    title="Download via Telegram"
                  >
                    <Download className="w-4 h-4" />
                  </a>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-8 rounded-3xl bg-slate-900/40 border border-slate-800/60 text-center">
            <p className="text-sm text-slate-400">
              Files are being indexed or scheduled for upload. Use the bot or request modal to notify uploaders!
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
