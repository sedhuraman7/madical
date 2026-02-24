document.addEventListener("DOMContentLoaded", () => {

    // Theme Toggle Logic
    const themeToggleBtn = document.getElementById('themeToggle');
    const currentTheme = localStorage.getItem('theme') || 'light';

    if (currentTheme === 'dark') {
        document.body.setAttribute('data-theme', 'dark');
        if (themeToggleBtn) themeToggleBtn.innerHTML = '<i class="fas fa-sun"></i>';
    }

    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', () => {
            let theme = document.body.getAttribute('data-theme');
            if (theme === 'dark') {
                document.body.removeAttribute('data-theme');
                localStorage.setItem('theme', 'light');
                themeToggleBtn.innerHTML = '<i class="fas fa-moon"></i>';
            } else {
                document.body.setAttribute('data-theme', 'dark');
                localStorage.setItem('theme', 'dark');
                themeToggleBtn.innerHTML = '<i class="fas fa-sun"></i>';
            }
        });
    }


    // Auto-detect location
    const detectLocationBtn = document.getElementById("detectLocationBtn");
    if (detectLocationBtn) {
        detectLocationBtn.addEventListener("click", () => {
            if ("geolocation" in navigator) {
                detectLocationBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
                navigator.geolocation.getCurrentPosition(
                    async (position) => {
                        const lat = position.coords.latitude;
                        const lng = position.coords.longitude;

                        document.getElementById("lat").value = lat;
                        document.getElementById("lng").value = lng;

                        try {
                            const response = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}`);
                            const data = await response.json();

                            const address = data.address;
                            const city = address.city || address.town || address.village || address.county || '';
                            const state = address.state || '';

                            let locationString = "";
                            if (city) locationString += city;
                            if (city && state) locationString += ", ";
                            if (state) locationString += state;

                            if (locationString) {
                                document.getElementById("location").value = locationString;
                            } else {
                                document.getElementById("location").value = `Lat: ${lat.toFixed(4)}, Lng: ${lng.toFixed(4)}`;
                            }

                        } catch (e) {
                            console.error("Reverse geocoding error:", e);
                            document.getElementById("location").value = `Lat: ${lat.toFixed(4)}, Lng: ${lng.toFixed(4)}`;
                        }

                        detectLocationBtn.innerHTML = '<i class="fas fa-check" style="color:var(--risk-low)"></i>';
                    },
                    (error) => {
                        console.error("Error getting location:", error);
                        alert("Could not detect your location. Please enter it manually.");
                        detectLocationBtn.innerHTML = '<i class="fas fa-crosshairs"></i>';
                    }
                );
            } else {
                alert("Geolocation is not supported by your browser.");
            }
        });
    }

    // Basic Form validation
    const form = document.getElementById("assessmentForm");
    if (form) {
        form.addEventListener("submit", (e) => {
            const btn = document.getElementById("submitBtn");
            if (btn) {
                btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
                btn.style.pointerEvents = 'none'; // Prevent double click
                // Let the form submit normally
            }
        });
    }
});
