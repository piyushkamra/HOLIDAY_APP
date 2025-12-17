function loadPackages(type) {
    fetch(`/api/packages?type=${type}`)
        .then(res => res.json())
        .then(data => console.log(data));
}

// --- City Dropdown Logic ---
const topCities = [
    "Bangalore", "Chennai", "Cochin", "Hyderabad", "Kolkata", "Mumbai", "New Delhi",
    "Ahmedabad", "Pune", "Jaipur", "Lucknow", "Goa", "Visakhapatnam", "Surat", "Nagpur",
    "Indore", "Bhopal", "Patna", "Vadodara", "Ludhiana", "Agra", "Nashik", "Faridabad",
    "Meerut", "Rajkot", "Varanasi", "Srinagar", "Amritsar", "Ranchi", "Guwahati", "Chandigarh"
];

document.addEventListener("DOMContentLoaded", function () {
    // --- City Dropdown ---
    const fromCityInput = document.getElementById("from_city");
    const cityDropdown = document.getElementById("city-dropdown");
    const citySearch = document.getElementById("city-search");
    const cityList = document.getElementById("city-list");
    const useLocation = document.getElementById("use-location");

    // --- To City Dropdown ---
    const toCityInput = document.getElementById("destination");
    // Create dropdown for To City
    const toCityDropdown = document.createElement("div");
    toCityDropdown.className = "city-dropdown";
    toCityDropdown.style.display = "none";
    toCityDropdown.innerHTML = `
        <div class="city-dropdown-search">
            <input type="text" id="to-city-search" class="form-control" placeholder="Search city...">
        </div>
        <div class="city-dropdown-divider"></div>
        <div class="city-dropdown-label">TOP SEARCHES</div>
        <div class="city-dropdown-list" id="to-city-list"></div>
    `;
    toCityInput.parentNode.appendChild(toCityDropdown);
    const toCitySearch = toCityDropdown.querySelector("#to-city-search");
    const toCityList = toCityDropdown.querySelector("#to-city-list");

    // --- Guests Dropdown ---
    const guestsInput = document.getElementById("guests");
    const guestsDropdown = document.getElementById("guests-dropdown");
    const roomsList = document.getElementById("rooms-list");
    const addRoomBtn = document.getElementById("add-room-btn");
    const applyGuestsBtn = document.getElementById("apply-guests-btn");
    const guestsWarning = document.getElementById("guests-warning");

    let rooms = [
        { adults: 2, children: 0, childrenAges: [] }
    ];

    // Show guests dropdown
    guestsInput.addEventListener("click", function () {
        guestsDropdown.style.display = "block";
        renderRooms();
    });

    // Hide guests dropdown on outside click
    document.addEventListener("mousedown", function (e) {
        // Only close if click is truly outside the guests dropdown and input
        if (
            !guestsDropdown.contains(e.target) &&
            e.target !== guestsInput
        ) {
            guestsDropdown.style.display = "none";
        }
    });

    // Add room
    addRoomBtn.addEventListener("click", function () {
        if (rooms.length < 4) {
            rooms.push({ adults: 1, children: 0, childrenAges: [] });
            renderRooms();
        }
    });

    // Apply guests selection
    applyGuestsBtn.addEventListener("click", function () {
        let summary = rooms.map((room, i) => {
            let adults = `${room.adults} Adult${room.adults > 1 ? "s" : ""}`;
            let children = room.children > 0 ? `, ${room.children} Child${room.children > 1 ? "ren" : ""}` : "";
            return `${adults}${children}`;
        }).join(" | ");
        guestsInput.value = `${rooms.length} Room${rooms.length > 1 ? "s" : ""}: ${summary}`;
        guestsDropdown.style.display = "none";
    });

    function renderRooms() {
        roomsList.innerHTML = "";
        rooms.forEach((room, idx) => {
            let roomDiv = document.createElement("div");
            roomDiv.className = "guests-room";
            roomDiv.innerHTML = `
                <div class="guests-room-header">
                    <span>ROOM ${idx + 1}</span>
                    ${rooms.length > 1 ? `<button type="button" class="remove-room-btn" data-idx="${idx}">&times;</button>` : ""}
                </div>
                <div class="guests-room-row">
                    <div class="guests-room-col">
                        <div class="guests-label">Adults <span class="guests-sub">(Above 12 Years)</span></div>
                        <div class="guests-counter">
                            <button type="button" class="guests-minus" data-type="adults" data-idx="${idx}">-</button>
                            <span class="guests-count">${room.adults.toString().padStart(2, "0")}</span>
                            <button type="button" class="guests-plus" data-type="adults" data-idx="${idx}">+</button>
                        </div>
                    </div>
                    <div class="guests-room-col">
                        <div class="guests-label">Children <span class="guests-sub">(Below 12 Years)</span></div>
                        <div class="guests-counter">
                            <button type="button" class="guests-minus" data-type="children" data-idx="${idx}">-</button>
                            <span class="guests-count">${room.children.toString().padStart(2, "0")}</span>
                            <button type="button" class="guests-plus" data-type="children" data-idx="${idx}">+</button>
                        </div>
                    </div>
                </div>
                ${room.children > 0 ? `
                <div class="guests-child-age">
                    <div class="guests-label">Child - Age Needed</div>
                    <div class="guests-sub">Please select child's age as on the last day of travel...</div>
                    ${Array.from({ length: room.children }).map((_, cidx) => `
                        <div class="guests-age-row">
                            <span>Age of Child ${cidx + 1}</span>
                            <div class="guests-age-selector">
                                ${Array.from({ length: 12 }).map((_, age) => `
                                    <button type="button" class="guests-age-btn${room.childrenAges[cidx] === age ? " selected" : ""}" data-idx="${idx}" data-cidx="${cidx}" data-age="${age}">${age}</button>
                                `).join("")}
                            </div>
                        </div>
                    `).join("")}
                </div>
                ` : ""}
            `;
            roomsList.appendChild(roomDiv);
        });

        // Add event listeners for counters and age selectors
        roomsList.querySelectorAll(".guests-minus").forEach(btn => {
            btn.addEventListener("click", function () {
                let idx = parseInt(btn.getAttribute("data-idx"));
                let type = btn.getAttribute("data-type");
                if (type === "adults" && rooms[idx].adults > 1) rooms[idx].adults--;
                if (type === "children" && rooms[idx].children > 0) {
                    rooms[idx].children--;
                    rooms[idx].childrenAges.pop();
                }
                renderRooms();
            });
        });
        roomsList.querySelectorAll(".guests-plus").forEach(btn => {
            btn.addEventListener("click", function () {
                let idx = parseInt(btn.getAttribute("data-idx"));
                let type = btn.getAttribute("data-type");
                let totalGuests = rooms[idx].adults + rooms[idx].children;
                if (type === "adults" && rooms[idx].adults < 3 && totalGuests < 4) rooms[idx].adults++;
                if (type === "children" && rooms[idx].children < 3 && totalGuests < 4) {
                    rooms[idx].children++;
                    rooms[idx].childrenAges.push(0);
                }
                renderRooms();
            });
        });
        roomsList.querySelectorAll(".remove-room-btn").forEach(btn => {
            btn.addEventListener("click", function () {
                let idx = parseInt(btn.getAttribute("data-idx"));
                rooms.splice(idx, 1);
                renderRooms();
            });
        });
        roomsList.querySelectorAll(".guests-age-btn").forEach(btn => {
            btn.addEventListener("click", function () {
                let idx = parseInt(btn.getAttribute("data-idx"));
                let cidx = parseInt(btn.getAttribute("data-cidx"));
                let age = parseInt(btn.getAttribute("data-age"));
                rooms[idx].childrenAges[cidx] = age;
                renderRooms();
            });
        });

        // Show warning if guest limits exceeded
        let warning = "";
        rooms.forEach(room => {
            if (room.adults > 3) warning = "Max 3 adults allowed in a room";
            if (room.adults + room.children > 4) warning = "Max 4 guests allowed in a room";
        });
        guestsWarning.textContent = warning;
        guestsWarning.style.display = warning ? "block" : "none";
    }

    // Show dropdown on input focus/click
    fromCityInput.addEventListener("focus", showDropdown);
    fromCityInput.addEventListener("click", showDropdown);

    toCityInput.addEventListener("focus", showToCityDropdown);
    toCityInput.addEventListener("click", showToCityDropdown);

    // Hide dropdowns on outside click
    document.addEventListener("mousedown", function (e) {
        // From City
        if (
            !cityDropdown.contains(e.target) &&
            e.target !== fromCityInput
        ) {
            setTimeout(() => {
                cityDropdown.style.display = "none";
            }, 120);
        }
        // To City
        if (
            !toCityDropdown.contains(e.target) &&
            e.target !== toCityInput
        ) {
            setTimeout(() => {
                toCityDropdown.style.display = "none";
            }, 120);
        }
    });

    // Filter cities as user types in search
    citySearch.addEventListener("input", function () {
        renderCityList(citySearch.value, cityList);
    });
    toCitySearch.addEventListener("input", function () {
        renderCityList(toCitySearch.value, toCityList);
    });

    // Select city from dropdowns
    cityList.addEventListener("click", function (e) {
        if (e.target.classList.contains("city-option")) {
            fromCityInput.value = e.target.textContent;
            cityDropdown.style.display = "none";
        }
    });
    toCityList.addEventListener("click", function (e) {
        if (e.target.classList.contains("city-option")) {
            toCityInput.value = e.target.textContent;
            toCityDropdown.style.display = "none";
        }
    });

    // Use current location (real geolocation) for From City only
    useLocation.addEventListener("click", function () {
        if (navigator.geolocation) {
            useLocation.textContent = "Locating...";
            navigator.geolocation.getCurrentPosition(function (pos) {
                const lat = pos.coords.latitude;
                const lon = pos.coords.longitude;
                fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}`)
                    .then(res => res.json())
                    .then(data => {
                        let city = data.address.city || data.address.town || data.address.village || data.address.state || "Current Location";
                        fromCityInput.value = city;
                        useLocation.textContent = "Use Current Location";
                        cityDropdown.style.display = "none";
                    })
                    .catch(() => {
                        fromCityInput.value = "Current Location";
                        useLocation.textContent = "Use Current Location";
                        cityDropdown.style.display = "none";
                    });
            }, function () {
                fromCityInput.value = "Current Location";
                useLocation.textContent = "Use Current Location";
                cityDropdown.style.display = "none";
            });
        } else {
            fromCityInput.value = "Current Location";
            cityDropdown.style.display = "none";
        }
    });

    function showDropdown() {
        cityDropdown.style.display = "block";
        citySearch.value = "";
        renderCityList("", cityList);
        citySearch.focus();
    }

    function showToCityDropdown() {
        toCityDropdown.style.display = "block";
        toCitySearch.value = "";
        renderCityList("", toCityList);
        toCitySearch.focus();
    }

    function renderCityList(filter, listElem) {
        let filtered = topCities.filter(city =>
            city.toLowerCase().includes(filter.toLowerCase())
        );
        listElem.innerHTML = filtered.map(city =>
            `<div class="city-option" style="padding:10px 18px;cursor:pointer;">${city}</div>`
        ).join("");
    }
});
