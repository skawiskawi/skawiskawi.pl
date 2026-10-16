const TOKEN_ENDPOINT = 'https://accounts.spotify.com/api/token';
const NOW_PLAYING_ENDPOINT = 'https://api.spotify.com/v1/me/player/currently-playing';
const RECENTLY_PLAYED_ENDPOINT = 'https://api.spotify.com/v1/me/player/recently-played?limit=1';

const CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Content-Type': 'application/json',
    'Cache-Control': 'no-cache, no-store, must-revalidate'
};

async function getAccessToken(env) {
    const clientId = env.SPOTIFY_CLIENT_ID;
    const clientSecret = env.SPOTIFY_CLIENT_SECRET;
    const refreshToken = env.SPOTIFY_REFRESH_TOKEN;
    
    // Wskazanie dokładnie, której zmiennej brakuje
    const missing = [];
    if (!clientId) missing.push('SPOTIFY_CLIENT_ID');
    if (!clientSecret) missing.push('SPOTIFY_CLIENT_SECRET');
    if (!refreshToken) missing.push('SPOTIFY_REFRESH_TOKEN');
    
    if (missing.length > 0) {
        throw new Error(`Brak zmiennych w Cloudflare: ${missing.join(', ')}`);
    }
    
    const basic = btoa(`${clientId.trim()}:${clientSecret.trim()}`);
    
    const response = await fetch(TOKEN_ENDPOINT, {
        method: 'POST',
        headers: {
            'Authorization': `Basic ${basic}`,
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: new URLSearchParams({
            grant_type: 'refresh_token',
            refresh_token: refreshToken.trim()
        }).toString()
    });
    
    if (!response.ok) {
        const errorDetails = await response.text();
        throw new Error(`Spotify token error (${response.status}): ${errorDetails}`);
    }
    
    const data = await response.json();
    return data.access_token;
}

export async function onRequest(context) {
    if (context.request.method === 'OPTIONS') {
        return new Response(null, { headers: CORS_HEADERS });
    }
    
    try {
        const accessToken = await getAccessToken(context.env);
        
        // 1. Sprawdzenie aktualnie odtwarzanego utworu
        const nowPlayingRes = await fetch(NOW_PLAYING_ENDPOINT, {
            headers: { Authorization: `Bearer ${accessToken}` }
        });
        
        if (nowPlayingRes.status === 200) {
            const data = await nowPlayingRes.json();
            if (data && data.item && data.currently_playing_type === 'track') {
                return new Response(JSON.stringify({
                    id: data.item.id,
                    isPlaying: data.is_playing,
                    isRecentlyPlayed: false,
                    title: data.item.name,
                    artist: data.item.artists.map(a => a.name).join(', '),
                    albumImageUrl: data.item.album.images[0]?.url || '',
                    songUrl: data.item.external_urls?.spotify || 'https://open.spotify.com',
                    progressMs: data.progress_ms || 0,
                    durationMs: data.item.duration_ms || 0
                }), { headers: CORS_HEADERS });
            }
        }
        
        // 2. Fallback: sprawdzenie ostatnio odtwarzanego utworu
        const recentlyPlayedRes = await fetch(RECENTLY_PLAYED_ENDPOINT, {
            headers: { Authorization: `Bearer ${accessToken}` }
        });
        
        if (recentlyPlayedRes.status === 200) {
            const recentData = await recentlyPlayedRes.json();
            const lastTrack = recentData.items?.[0]?.track;
            if (lastTrack) {
                return new Response(JSON.stringify({
                    id: lastTrack.id,
                    isPlaying: false,
                    isRecentlyPlayed: true,
                    title: lastTrack.name,
                    artist: lastTrack.artists.map(a => a.name).join(', '),
                    albumImageUrl: lastTrack.album.images[0]?.url || '',
                    songUrl: lastTrack.external_urls?.spotify || 'https://open.spotify.com',
                    progressMs: 0,
                    durationMs: lastTrack.duration_ms || 0
                }), { headers: CORS_HEADERS });
            }
        }
        
        return new Response(JSON.stringify({
            isPlaying: false,
            isRecentlyPlayed: false
        }), { headers: CORS_HEADERS });
        
    } catch (error) {
        return new Response(JSON.stringify({
            isPlaying: false,
            isRecentlyPlayed: false,
            error: error.message
        }), { status: 500, headers: CORS_HEADERS });
    }
}
