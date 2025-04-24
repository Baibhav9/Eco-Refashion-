document.addEventListener("DOMContentLoaded", function () {

});

function getCSRFToken() {
    const name = 'csrftoken=';
    const decodedCookie = decodeURIComponent(document.cookie);
    const cookies = decodedCookie.split(';');
    for (let c of cookies) {
        c = c.trim();
        if (c.startsWith(name)) {
            return c.substring(name.length);
        }
    }
    return '';
}
