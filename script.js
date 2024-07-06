// Function to generate embed HTML from video URL
function generateEmbedHtml(videoUrl) {
    const videoId = videoUrl.split('/').pop();
    return `
        <blockquote class="tiktok-embed" cite="${videoUrl}" data-video-id="${videoId}" style="max-width: 605px; min-width: 325px;">
            <section>
                <a target="_blank" title="Watch on TikTok" href="${videoUrl}">Watch on TikTok</a>
            </section>
        </blockquote>
    `;
}

// Function to toggle video visibility and load embed dynamically
function toggleVideo(event) {
    const row = event.currentTarget;
    const hiddenRow = row.nextElementSibling;
    hiddenRow.classList.toggle('expanded');
    if (hiddenRow.classList.contains('expanded') && !hiddenRow.dataset.loaded) {
        const videoUrl = row.dataset.videoUrl;
        hiddenRow.querySelector('.blockquote-container').innerHTML = generateEmbedHtml(videoUrl);
        hiddenRow.dataset.loaded = true;
        // Manually trigger TikTok embed script
        if (window.ttEmbed) {
            window.ttEmbed.loadEmbeds();
        } else {
            const script = document.createElement('script');
            script.src = "https://www.tiktok.com/embed.js";
            script.async = true;
            script.onload = () => window.ttEmbed.loadEmbeds();
            document.body.appendChild(script);
        }
    }
}

// Function to populate the table
function populateTable(reviews) {
    const tbody = document.querySelector('#leaderboard tbody');
    tbody.innerHTML = '';

    reviews
        .sort((a, b) => b.score - a.score)
        .forEach((review, index) => {
            const row = document.createElement('tr');
            row.classList.add('clickable-row');
            row.dataset.videoUrl = review.videoUrl;

            row.innerHTML = `
                <td>${index + 1}</td>
                <td>${review.score}</td>
                <td>${review.description}</td>
                <td>View</td>
            `;

            const hiddenRow = document.createElement('tr');
            hiddenRow.classList.add('hidden-row');
            hiddenRow.innerHTML = `
                <td colspan="4" class="blockquote-container"></td>
            `;

            tbody.appendChild(row);
            tbody.appendChild(hiddenRow);
        });

    // Add event listeners to rows
    document.querySelectorAll('.clickable-row').forEach(row => {
        row.addEventListener('click', toggleVideo);
    });
}

// Initialize table on page load
document.addEventListener('DOMContentLoaded', () => {
    // Fetch JSON data
    fetch('reviews.json')
        .then(response => response.json())
        .then(reviews => {
            populateTable(reviews);
        })
        .catch(error => console.error('Error fetching reviews:', error));
});
