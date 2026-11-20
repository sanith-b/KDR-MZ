export interface TMDbDrama {
  id: number;
  name: string;
  original_name?: string;
  overview?: string;
  first_air_date?: string;
  year?: string;
  vote_average?: number;
  vote_count?: number;
  poster_url?: string;
  backdrop_url?: string;
  genres?: string;
  seasons?: Season[];
  number_of_seasons?: number;
  number_of_episodes?: number;
  status?: string;
  cast?: string;
}

export interface Season {
  season_number: number;
  name: string;
  episode_count: number;
  air_date?: string;
  poster_url?: string;
}

export interface MediaFile {
  _id: string;
  file_name: string;
  file_size: number;
  file_type?: string;
  mime_type?: string;
  caption?: string;
}

export interface User {
  id: number;
  name: string;
  username?: string;
  role: 'user' | 'premium' | 'moderator' | 'admin';
}

export interface KDramaRequest {
  request_id: string;
  user_id: number;
  user_name: string;
  drama_name: string;
  details?: string;
  status: 'pending' | 'approved' | 'rejected';
  created_at: string;
  admin_notes?: string;
}
