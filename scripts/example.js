axios.post('/api/v1/login', {
    username: 'admin',
    password: '123'
});

fetch('/api/v2/save', {
    method: 'POST',
    body: JSON.stringify({
        session_id: 'xyz',
        data_payload: 'hello'
    })
});

axios.get('/search.php', {
    params: {
        query: 'test',
        page: 1
    }
});