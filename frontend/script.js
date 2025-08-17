function showSection(sectionId) {
    document.querySelectorAll('main section').forEach(section => {
        section.style.display = section.id === sectionId ? 'block' : 'none';
    });
}

async function planTrip() {
    const destination = document.getElementById('destination').value;
    const travelDate = document.getElementById('travelDate').value;
    if (!destination || !travelDate) {
        alert('Please enter a destination and travel date.');
        return;
    }

    try {
        const response = await fetch('http://35.224.187.121:5000/api/plan', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ destination, travel_date: travelDate })
        });
        const data = await response.json();
        if (response.ok) {
            const infoDiv = document.getElementById('destinationInfo');
            infoDiv.innerHTML = `
                <h3>${data.destination}</h3>
                <p>Country: ${data.country_info.name}</p>
                <p>Capital: ${data.country_info.capital}</p>
                <p>Currency: ${data.country_info.currency}</p>
                <p>Weather: ${data.weather.description} (${data.weather.temperature}°C)</p>
                <img src="${data.image_url}" alt="${data.destination} image">
            `;
            document.getElementById('destination').value = '';
            document.getElementById('travelDate').value = '';
            fetchTrips();
        } else {
            alert(data.error || 'Error planning trip.');
        }
    } catch (error) {
        alert('Error connecting to backend: ' + error.message);
    }
}

async function fetchTrips() {
    try {
        const response = await fetch('http://35.224.187.121:5000/api/trips');
        const trips = await response.json();
        const tripList = document.getElementById('tripList');
        tripList.innerHTML = '';
        trips.forEach(trip => {
            const li = document.createElement('li');
            li.textContent = `${trip.destination} - ${new Date(trip.travel_date).toLocaleDateString()}`;
            tripList.appendChild(li);
        });
    } catch (error) {
        console.error('Error fetching trips:', error);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    showSection('home');
    fetchTrips();
});
