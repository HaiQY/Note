const BASE_URL = '/api';

async function request(path, options = {}) {
    const res = await fetch(BASE_URL + path, options);
    if (!res.ok) {
        const text = await res.text();
        throw new Error(text || res.statusText);
    }
    const json = await res.json();
    // ensure there is always a data object to avoid undefined accesses
    if (json && !('data' in json)) {
        json.data = null;
    }
    return json;
}

export const api = {
    uploadNote: (formData) => request('/notes/upload', { method: 'POST', body: formData }),
    getNotes: (params) => {
        const qs = new URLSearchParams(params);
        return request('/notes?' + qs.toString()).then(res => res.data || {});
    },
    searchNotes: (params) => {
        const qs = new URLSearchParams(params);
        return request('/search?' + qs.toString()).then(res => res.data || {});
    },
    generateCards: (noteId, body) => request(`/cards/generate/${noteId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    }),
    reviewCard: (cardId, body) => request(`/cards/${cardId}/review`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    }),
    updateNote: (noteId, body) => request(`/notes/${noteId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    }),
    markImportant: (noteId) => request(`/notes/${noteId}/important`, {
        method: 'POST'
    }),
    getCategories: () => request('/categories'),
    classifyNote: (noteId) => request(`/notes/${noteId}/classify`, {
        method: 'POST'
    }),
    getNote: (noteId) => request(`/notes/${noteId}`).then(res => res.data),
    deleteNote: (noteId) => request(`/notes/${noteId}`, { method: 'DELETE' }),
    reprocessNote: (noteId) => request(`/notes/${noteId}/reprocess`, { method: 'POST' }),

    ocrProcess: (formData) => request('/ocr/process', { method: 'POST', body: formData }),
    ocrBatch: (formData) => request('/ocr/batch', { method: 'POST', body: formData }),
    ocrStatus: (taskId) => request(`/ocr/status/${taskId}`),

    createCategory: (body) => request('/categories', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    }),
    updateCategory: (catId, body) => request(`/categories/${catId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    }),
    deleteCategory: (catId) => request(`/categories/${catId}`, { method: 'DELETE' }),

    extractKeywords: (noteId) => request(`/notes/${noteId}/keywords`, {
        method: 'POST'
    }),

    searchSuggestions: (params) => {
        const qs = new URLSearchParams(params);
        return request('/search/suggestions?' + qs.toString()).then(res => res.data || []);
    },

    getCards: (params) => {
        const qs = new URLSearchParams(params);
        return request('/cards?' + qs.toString()).then(res => res.data || {});
    },
    getCard: (cardId) => request(`/cards/${cardId}`).then(res => res.data),
    getReviewCards: (limit = 20) => request(`/cards/review?limit=${limit}`).then(res => res.data),
    reviewCard: (cardId, body) => request(`/cards/${cardId}/review`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    }),
    updateCard: (cardId, body) => request(`/cards/${cardId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    }),
    deleteCard: (cardId) => request(`/cards/${cardId}`, { method: 'DELETE' }),

    getSettings: () => request('/settings').then(res => res.data || []),
    getSetting: (key) => request(`/settings/${key}`).then(res => res.data),
    updateSetting: (key, value) => request(`/settings/${key}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ key, value })
    }),
    toggleSetting: (key, value) => request(`/settings/boolean/${key}?value=${value}`, {
        method: 'POST'
    }),
};
