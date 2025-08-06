export const getAccessToken = () => localStorage.getItem('sb_access_token');
export const getRefreshToken = () => localStorage.getItem('sb_refresh_token');

export const setSession = (access_token: string, refresh_token: string) => {
    localStorage.setItem('sb_access_token', access_token);
    localStorage.setItem('sb_refresh_token', refresh_token);
};

export const clearSession = () => {
    localStorage.removeItem('sb_access_token');
    localStorage.removeItem('sb_refresh_token');
};
