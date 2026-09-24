// ==========================================================================
// Aswan SmartCurbs AI — Comprehensive Admin Dashboard DB Controller
// ==========================================================================

const API_BASE = 'http://127.0.0.1:8001/api/v1';

async function fetchAPI(endpoint, options = {}) {
    try {
        const res = await fetch(`${API_BASE}${endpoint}`, {
            headers: { 'Content-Type': 'application/json' },
            ...options
        });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || `HTTP ${res.status}`);
        }
        return await res.json();
    } catch (err) {
        console.warn(`[Admin DB Controller] ${endpoint} error:`, err.message);
        return null;
    }
}

// --------------------------------------------------------------------------
// 1. Universal Top Navigation, Modals & Live DB Status Banner
// --------------------------------------------------------------------------
function setupNavigationAndBanner() {
    // 1. Inject Live DB Connection Banner at the top of the main container
    const header = document.querySelector('header');
    if (header && !document.getElementById('db-status-banner')) {
        const banner = document.createElement('div');
        banner.id = 'db-status-banner';
        banner.className = 'flex items-center gap-2 px-3 py-1 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-semibold rounded-full shadow-sm cursor-pointer hover:bg-emerald-100 transition-colors';
        banner.title = 'Click to test FastAPI backend connection';
        banner.onclick = openSettingsModal;
        banner.innerHTML = `
            <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span>Live DB Connected (FastAPI :8001)</span>
        `;
        const rightContainer = header.querySelector('.flex.items-center.gap-4, .flex.items-center.gap-md, .flex.items-center.gap-lg') || header;
        rightContainer.prepend(banner);
    }

    // 2. Fix all sidebar links and buttons
    document.querySelectorAll('a, button').forEach(link => {
        const text = (link.textContent || '').trim();
        if (text.includes('Dashboard') && link.tagName === 'A') {
            link.href = '../main_dashboard/code.html';
        } else if ((text.includes('Parking Zones') || text.includes('Zones List') || text.includes('VIEW ALL ZONES')) && link.tagName === 'A') {
            link.href = '../parking_zones_list/code.html';
        } else if ((text.includes('Reservations') || text.includes('VIEW ALL RESERVATIONS') || text.includes('VIEW RESERVATIONS')) && link.tagName === 'A') {
            link.href = '../reservations_management/code.html';
        } else if (text.includes('Settings')) {
            link.onclick = (e) => { e.preventDefault(); openSettingsModal(); };
        } else if (text.includes('Logout')) {
            link.onclick = (e) => { e.preventDefault(); openLogoutModal(); };
        } else if (text.includes('Back to Zones List')) {
            link.href = '../parking_zones_list/code.html';
        }
    });

    // 3. Inject Modals into DOM if not present
    injectGlobalModals();
}

function injectGlobalModals() {
    if (!document.getElementById('modal-system-settings')) {
        const modal = document.createElement('div');
        modal.id = 'modal-system-settings';
        modal.className = 'fixed inset-0 z-50 hidden bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4';
        modal.innerHTML = `
            <div class="bg-white rounded-2xl shadow-2xl max-w-lg w-full overflow-hidden border border-gray-200">
                <div class="px-6 py-4 bg-slate-900 text-white flex justify-between items-center">
                    <h3 class="font-bold text-lg flex items-center gap-2">
                        <span class="material-symbols-outlined text-teal-400">tune</span>
                        System & Architecture Settings
                    </h3>
                    <button onclick="closeSettingsModal()" class="text-gray-400 hover:text-white text-xl">✕</button>
                </div>
                <div class="p-6 space-y-4 text-sm text-gray-700">
                    <div class="bg-slate-50 p-4 rounded-xl border border-gray-200 space-y-2">
                        <div class="flex justify-between">
                            <span class="font-semibold text-gray-900">Backend API URL:</span>
                            <span class="font-mono text-xs text-teal-700 font-bold">${API_BASE}</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="font-semibold text-gray-900">Database Engine:</span>
                            <span class="font-mono text-xs text-gray-600">PostgreSQL / SQLAlchemy</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="font-semibold text-gray-900">AI Video Model:</span>
                            <span class="font-mono text-xs text-gray-600">YOLOv11 + ByteTrack</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="font-semibold text-gray-900">Ground Calibration:</span>
                            <span class="font-mono text-xs text-emerald-700 font-bold">Perspective Homography (cm)</span>
                        </div>
                    </div>
                    <div class="flex items-center justify-between p-3 bg-teal-50 rounded-xl border border-teal-200">
                        <div>
                            <p class="font-bold text-teal-900">Driver Portal Link</p>
                            <p class="text-xs text-teal-700">Driver space reservation & availability portal</p>
                        </div>
                        <a href="http://localhost:5173" target="_blank" class="px-3 py-1.5 bg-teal-600 text-white rounded-lg text-xs font-bold hover:bg-teal-700 transition-colors">Open Portal</a>
                    </div>
                </div>
                <div class="px-6 py-3 bg-gray-50 border-t border-gray-100 flex justify-end gap-2">
                    <button onclick="testConnection()" class="px-4 py-2 bg-slate-900 text-white rounded-lg text-xs font-bold hover:bg-slate-800">Test API Health</button>
                    <button onclick="closeSettingsModal()" class="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg text-xs font-bold hover:bg-gray-300">Close</button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }

    if (!document.getElementById('modal-logout-confirm')) {
        const modal = document.createElement('div');
        modal.id = 'modal-logout-confirm';
        modal.className = 'fixed inset-0 z-50 hidden bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4';
        modal.innerHTML = `
            <div class="bg-white rounded-2xl shadow-2xl max-w-md w-full overflow-hidden border border-gray-200 p-6 text-center">
                <div class="w-12 h-12 rounded-full bg-rose-100 text-rose-600 flex items-center justify-center mx-auto mb-4">
                    <span class="material-symbols-outlined text-2xl">logout</span>
                </div>
                <h3 class="font-bold text-lg text-gray-900 mb-2">Sign out of Admin Dashboard?</h3>
                <p class="text-sm text-gray-600 mb-6">Choose where you would like to navigate:</p>
                <div class="grid grid-cols-2 gap-3">
                    <a href="../index.html" class="px-4 py-2.5 bg-slate-900 text-white rounded-xl text-xs font-bold hover:bg-slate-800 transition-colors flex items-center justify-center gap-1">
                        <span class="material-symbols-outlined text-sm">home</span> Portal Home
                    </a>
                    <a href="http://localhost:5173" class="px-4 py-2.5 bg-teal-600 text-white rounded-xl text-xs font-bold hover:bg-teal-700 transition-colors flex items-center justify-center gap-1">
                        <span class="material-symbols-outlined text-sm">directions_car</span> Driver Portal
                    </a>
                </div>
                <button onclick="closeLogoutModal()" class="mt-4 text-xs text-gray-500 hover:text-gray-800 underline font-semibold">Cancel</button>
            </div>
        `;
        document.body.appendChild(modal);
    }
}

window.openSettingsModal = function() {
    const modal = document.getElementById('modal-system-settings');
    if (modal) modal.classList.remove('hidden');
};

window.closeSettingsModal = function() {
    const modal = document.getElementById('modal-system-settings');
    if (modal) modal.classList.add('hidden');
};

window.openLogoutModal = function() {
    const modal = document.getElementById('modal-logout-confirm');
    if (modal) modal.classList.remove('hidden');
};

window.closeLogoutModal = function() {
    const modal = document.getElementById('modal-logout-confirm');
    if (modal) modal.classList.add('hidden');
};

window.testConnection = async function() {
    const res = await fetchAPI('/availability');
    if (res) {
        alert(`✅ FastAPI Backend is Online! Retrieved ${res.length} live parking zones from the database.`);
    } else {
        alert('❌ Could not connect to FastAPI backend at ' + API_BASE);
    }
};

// --------------------------------------------------------------------------
// 2. Main Dashboard Page Controller
// --------------------------------------------------------------------------
async function renderMainDashboard() {
    const summaries = await fetchAPI('/availability');
    const logs = await fetchAPI('/occupancy/logs?limit=10');

    if (summaries) {
        let totalZones = summaries.length;
        let totalSpaces = 0;
        let availableSpaces = 0;
        let occupiedSpaces = 0;
        let reservedSpaces = 0;

        summaries.forEach(z => {
            totalSpaces += z.total_spaces || 0;
            availableSpaces += z.available_count || 0;
            occupiedSpaces += z.occupied_count || 0;
            reservedSpaces += z.reserved_count || 0;
        });

        const effectiveOccupied = occupiedSpaces + reservedSpaces;
        const occRate = totalSpaces > 0 ? ((effectiveOccupied / totalSpaces) * 100).toFixed(1) : '0.0';

        // 1. Update 4 Top Summary Metric Cards & Make them Clickable
        const statZones = document.getElementById('stat-total-zones');
        const statSpaces = document.getElementById('stat-total-spaces');
        const statOccupied = document.getElementById('stat-occupied-spaces');
        const statAvailable = document.getElementById('stat-available-spaces');

        if (statZones) statZones.textContent = totalZones;
        if (statSpaces) statSpaces.textContent = totalSpaces;
        if (statOccupied) statOccupied.textContent = effectiveOccupied;
        if (statAvailable) statAvailable.textContent = availableSpaces;

        const cardContainers = document.querySelectorAll('main div.grid-cols-1.md\\:grid-cols-2.lg\\:grid-cols-4 > div');
        if (cardContainers.length >= 4) {
            cardContainers[0].style.cursor = 'pointer';
            cardContainers[0].onclick = () => window.location.href = '../parking_zones_list/code.html';
            cardContainers[1].style.cursor = 'pointer';
            cardContainers[1].onclick = () => window.location.href = '../parking_zones_list/code.html';
            cardContainers[2].style.cursor = 'pointer';
            cardContainers[2].onclick = () => window.location.href = '../parking_zone_details/code.html?zone_id=1';
            cardContainers[3].style.cursor = 'pointer';
            cardContainers[3].onclick = () => window.location.href = '../parking_zone_details/code.html?zone_id=1';
        }

        // 2. Update Donut Chart
        const donutPct = document.getElementById('donut-pct');
        if (donutPct) donutPct.textContent = `${occRate}%`;
        const donutBg = document.getElementById('donut-bg');
        if (donutBg) donutBg.style.background = `conic-gradient(#ba1a1a 0% ${occRate}%, #006a61 ${occRate}% 100%)`;

        const donutOccupied = document.getElementById('donut-occupied-count');
        const donutAvailable = document.getElementById('donut-available-count');
        if (donutOccupied) donutOccupied.textContent = effectiveOccupied;
        if (donutAvailable) donutAvailable.textContent = availableSpaces;

        // 3. Update Section 3: Parking Zones List
        const zonesContainer = document.getElementById('dashboard-zones-list');
        if (zonesContainer && summaries.length > 0) {
            zonesContainer.innerHTML = '';
            summaries.forEach(z => {
                const total = z.total_spaces || 0;
                const occ = (z.occupied_count || 0) + (z.reserved_count || 0);
                const pct = total > 0 ? Math.round((occ / total) * 100) : 0;
                let badgeColor = 'bg-teal-50 text-teal-700 border border-teal-200';
                let badgeText = 'ACTIVE';
                if (pct >= 80) {
                    badgeColor = 'bg-rose-50 text-rose-700 border border-rose-200';
                    badgeText = 'HIGH OCCUPANCY';
                }

                const item = document.createElement('div');
                item.className = 'border border-outline-variant rounded-xl p-4 bg-white hover:border-teal-500 shadow-sm transition-all cursor-pointer';
                item.onclick = () => window.location.href = `../parking_zone_details/code.html?zone_id=${z.zone_id}`;
                item.innerHTML = `
                    <div class="flex justify-between items-start mb-3">
                        <div>
                            <h4 class="font-bold text-primary text-base hover:text-teal-600 transition-colors">${z.zone_name}</h4>
                            <p class="text-xs text-gray-500">${z.location} • ${total} total spaces</p>
                        </div>
                        <span class="text-xs font-semibold px-2.5 py-1 rounded-full ${badgeColor}">${badgeText}</span>
                    </div>
                    <div class="flex items-center gap-4">
                        <div class="flex-1 h-2.5 bg-gray-100 rounded-full overflow-hidden">
                            <div class="h-full ${pct >= 80 ? 'bg-rose-500' : 'bg-teal-600'} rounded-full transition-all" style="width: ${pct}%"></div>
                        </div>
                        <div class="w-28 text-right font-mono text-xs">
                            <span class="font-bold text-primary">${occ} / ${total}</span>
                            <span class="text-gray-500 ml-1">(${pct}%)</span>
                        </div>
                    </div>
                `;
                zonesContainer.appendChild(item);
            });
        }
    }

    // 4. Update Section 4: Live Detection / Reservation Logs Feed
    if (logs && logs.length > 0) {
        const tbody = document.querySelector('table tbody');
        if (tbody) {
            tbody.innerHTML = '';
            logs.forEach(l => {
                const tr = document.createElement('tr');
                tr.className = 'border-b border-gray-100 hover:bg-gray-50/50 transition-colors text-xs font-mono';
                
                const isOccupied = l.status === 'occupied';
                const badge = isOccupied 
                    ? `<span class="px-2 py-0.5 rounded-full bg-rose-50 text-rose-700 font-bold border border-rose-200">OCCUPIED</span>`
                    : `<span class="px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 font-bold border border-emerald-200">AVAILABLE</span>`;

                tr.innerHTML = `
                    <td class="py-3 px-4 font-bold text-primary">#LOG-${l.id}</td>
                    <td class="py-3 px-4 text-gray-700 font-sans font-medium">Space #${l.space_id}</td>
                    <td class="py-3 px-4 text-gray-600">Zone ${l.zone_id}</td>
                    <td class="py-3 px-4 text-gray-500">${l.created_at ? l.created_at.replace('T', ' ').substring(0, 19) : 'Live Event'}</td>
                    <td class="py-3 px-4 text-teal-700 font-bold">${Math.round((l.confidence || 0.95) * 100)}% Conf</td>
                    <td class="py-3 px-4 text-right">${badge}</td>
                `;
                tbody.appendChild(tr);
            });
        }
    }
}

// --------------------------------------------------------------------------
// 3. Parking Zones Directory Page Controller
// --------------------------------------------------------------------------
let allZonesCache = [];

async function renderParkingZonesList() {
    const summaries = await fetchAPI('/availability');
    const tbody = document.querySelector('table tbody');
    if (!tbody || !summaries) return;
    allZonesCache = summaries;

    // 1. Update Top 4 Bento Stats
    const totalZones = summaries.length;
    let totalSpaces = 0;
    let availableSpaces = 0;
    let highOccupancyCount = 0;
    let activeZonesCount = 0;

    summaries.forEach(z => {
        totalSpaces += z.total_spaces || 0;
        availableSpaces += z.available_count || 0;
        const occ = (z.occupied_count || 0) + (z.reserved_count || 0);
        if (z.total_spaces > 0) activeZonesCount++;
        if (z.total_spaces > 0 && (occ / z.total_spaces) >= 0.75) highOccupancyCount++;
    });

    const statNumbers = document.querySelectorAll('main .grid-cols-2.md\\:grid-cols-4 .font-display-lg');
    if (statNumbers.length >= 4) {
        statNumbers[0].textContent = totalZones;
        statNumbers[1].textContent = activeZonesCount;
        statNumbers[2].textContent = highOccupancyCount;
        statNumbers[3].textContent = availableSpaces;
    }

    // 2. Attach Search & Filter Listeners
    const searchInput = document.querySelector('input[placeholder="Search zones..."]');
    if (searchInput && !searchInput.dataset.bound) {
        searchInput.dataset.bound = 'true';
        searchInput.addEventListener('input', filterAndRenderZonesTable);
    }

    // 3. Attach Add Zone & Export Buttons
    document.querySelectorAll('button').forEach(btn => {
        const text = btn.textContent || '';
        if (text.includes('Add Zone') && !btn.dataset.bound) {
            btn.dataset.bound = 'true';
            btn.onclick = promptCreateZone;
        } else if (text.includes('Export') && !btn.dataset.bound) {
            btn.dataset.bound = 'true';
            btn.onclick = exportZonesData;
        }
    });

    filterAndRenderZonesTable();
}

function filterAndRenderZonesTable() {
    const tbody = document.querySelector('table tbody');
    if (!tbody) return;

    const searchInput = document.querySelector('input[placeholder="Search zones..."]');
    const query = searchInput ? searchInput.value.toLowerCase().trim() : '';

    let filtered = allZonesCache.filter(z => {
        return !query || 
            z.zone_name.toLowerCase().includes(query) || 
            z.location.toLowerCase().includes(query) ||
            `ZONE-${z.zone_id}`.toLowerCase().includes(query);
    });

    if (filtered.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" class="p-8 text-center text-gray-400 font-sans">No parking zones found matching your search.</td></tr>`;
        return;
    }

    tbody.innerHTML = '';
    filtered.forEach(z => {
        const total = z.total_spaces || 0;
        const available = z.available_count || 0;
        const occupied = (z.occupied_count || 0) + (z.reserved_count || 0);
        const rate = total > 0 ? Math.round((occupied / total) * 100) : 0;

        let statusBadge = `<span class="px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">Available</span>`;
        if (available === 0) {
            statusBadge = `<span class="px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200">Full</span>`;
        } else if (rate > 70) {
            statusBadge = `<span class="px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200">High Demand</span>`;
        }

        const tr = document.createElement('tr');
        tr.className = 'border-b border-gray-100 hover:bg-gray-50/50 transition-colors text-sm cursor-pointer';
        tr.onclick = () => window.location.href = `../parking_zone_details/code.html?zone_id=${z.zone_id}`;
        tr.innerHTML = `
            <td class="p-4 font-mono font-bold text-primary">#ZONE-${z.zone_id}</td>
            <td class="p-4">
                <a href="../parking_zone_details/code.html?zone_id=${z.zone_id}" class="font-bold text-primary hover:text-teal-600 transition-colors">${z.zone_name}</a>
                <div class="text-xs text-gray-500 font-normal">${z.location}</div>
            </td>
            <td class="p-4 text-center font-bold text-primary">${total}</td>
            <td class="p-4 text-center font-bold text-emerald-600 font-mono">${available}</td>
            <td class="p-4 text-center font-bold text-rose-600 font-mono">${occupied}</td>
            <td class="p-4">
                <div class="w-full bg-gray-100 rounded-full h-2.5 overflow-hidden">
                    <div class="bg-teal-600 h-2.5 rounded-full" style="width: ${rate}%"></div>
                </div>
                <div class="text-xs text-gray-500 mt-1 text-right font-mono">${rate}%</div>
            </td>
            <td class="p-4 text-center">${statusBadge}</td>
            <td class="p-4 text-center">
                <a href="../parking_zone_details/code.html?zone_id=${z.zone_id}" class="px-3 py-1.5 bg-teal-50 text-teal-700 hover:bg-teal-100 rounded-lg inline-flex items-center gap-1 text-xs font-bold transition-colors">
                    <span>Manage Bays</span>
                    <span class="material-symbols-outlined text-sm">arrow_forward</span>
                </a>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

window.promptCreateZone = async function() {
    const name = prompt("Enter Parking Zone Name (e.g. Aswan Downtown Zone B):");
    if (!name) return;
    const location = prompt("Enter Location Description (e.g. Downtown, Aswan):", "Aswan");
    if (!location) return;
    const spaces = parseInt(prompt("Enter Total Parking Spaces count:", "5") || "5", 10);

    const res = await fetchAPI('/zones', {
        method: 'POST',
        body: JSON.stringify({
            name,
            location,
            latitude: 24.0889,
            longitude: 32.8998,
            total_spaces: spaces
        })
    });

    if (res && res.id) {
        for (let i = 1; i <= spaces; i++) {
            await fetchAPI(`/zones/${res.id}/spaces`, {
                method: 'POST',
                body: JSON.stringify({
                    zone_id: res.id,
                    space_number: `B-${i}`,
                    status: 'available'
                })
            });
        }
        alert(`✅ Zone "${name}" and ${spaces} spaces created in DB!`);
        location.reload();
    }
};

window.exportZonesData = function() {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(allZonesCache, null, 2));
    const dlAnchorElem = document.createElement('a');
    dlAnchorElem.setAttribute("href", dataStr);
    dlAnchorElem.setAttribute("download", `aswan_parking_zones_${new Date().toISOString().slice(0,10)}.json`);
    dlAnchorElem.click();
};

// --------------------------------------------------------------------------
// 4. Parking Zone Details Page Controller (Bay-by-Bay Management)
// --------------------------------------------------------------------------
async function renderParkingZoneDetails() {
    const urlParams = new URLSearchParams(window.location.search);
    const zoneId = urlParams.get('zone_id') || '1';

    const [detail, reservations, logs] = await Promise.all([
        fetchAPI(`/availability/${zoneId}`),
        fetchAPI('/reservations?limit=100'),
        fetchAPI('/occupancy/logs?limit=10')
    ]);

    if (!detail) return;

    // 1. Update Title & Metadata
    const title = document.querySelector('h1.font-display-lg, h1');
    if (title) title.textContent = detail.zone_name || `Zone ${zoneId}`;

    const locationText = document.querySelector('p.font-body-md');
    if (locationText) {
        locationText.innerHTML = `
            <span class="material-symbols-outlined text-[18px]">pin_drop</span> Location: ${detail.location} | 
            <span class="inline-flex items-center gap-1 text-emerald-600 font-medium">
                <span class="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></span> Status: Live DB Active
            </span>
        `;
    }

    // 2. Update Capacity Stats
    const statCards = document.querySelectorAll('.bg-surface-container-low span.font-display-lg-mobile, .bg-surface-container-low span.text-display-lg-mobile');
    if (statCards.length >= 3) {
        statCards[0].textContent = detail.total_spaces;
        statCards[1].textContent = (detail.occupied_count || 0) + (detail.reserved_count || 0);
        statCards[2].textContent = detail.available_count;
    }

    const occRate = detail.total_spaces > 0 
        ? Math.round((((detail.occupied_count || 0) + (detail.reserved_count || 0)) / detail.total_spaces) * 100) 
        : 0;

    const occPctText = document.querySelector('.flex.justify-between.items-end span.font-bold');
    if (occPctText) occPctText.textContent = `${occRate}%`;
    const progressBar = document.querySelector('.h-full.bg-\\[\\#0D9488\\]');
    if (progressBar) progressBar.style.width = `${occRate}%`;

    // 3. Update Secondary Bento Stats (Today's Reservations, Average Occupancy)
    const secondaryNumbers = document.querySelectorAll('.lg\\:col-span-8 .font-display-lg');
    if (secondaryNumbers.length >= 2) {
        const zoneReservations = (reservations || []).filter(r => detail.spaces && detail.spaces.some(s => s.id === r.space_id));
        secondaryNumbers[0].textContent = zoneReservations.length;
        secondaryNumbers[1].textContent = `${occRate}%`;
    }

    // 4. Update Recent Activity Feed
    const activityFeed = document.querySelector('.divide-y.divide-outline-variant\\/40, .divide-y');
    if (activityFeed && logs && logs.length > 0) {
        activityFeed.innerHTML = '';
        const zoneLogs = logs.filter(l => l.zone_id === parseInt(zoneId, 10)).slice(0, 3);
        const displayLogs = zoneLogs.length > 0 ? zoneLogs : logs.slice(0, 3);
        displayLogs.forEach(l => {
            const isOcc = l.status === 'occupied';
            const icon = isOcc ? 'directions_car' : 'exit_to_app';
            const iconColor = isOcc ? 'bg-error/10 text-error' : 'bg-secondary/10 text-secondary';
            const text = isOcc ? `Vehicle arrived at Space #${l.space_id}` : `Vehicle departed Space #${l.space_id}`;
            const timeStr = l.created_at ? l.created_at.replace('T', ' ').substring(11, 19) : 'Just now';

            const item = document.createElement('div');
            item.className = 'py-sm px-sm flex justify-between items-center';
            item.innerHTML = `
                <div class="flex items-center gap-sm">
                    <span class="w-8 h-8 rounded-full ${iconColor} flex items-center justify-center">
                        <span class="material-symbols-outlined text-[16px]">${icon}</span>
                    </span>
                    <div>
                        <p class="font-body-sm font-medium text-primary">${text}</p>
                        <p class="text-[11px] text-on-surface-variant">Sensor / AI Detection Event</p>
                    </div>
                </div>
                <span class="font-mono-data text-mono-data text-on-surface-variant">${timeStr}</span>
            `;
            activityFeed.appendChild(item);
        });
    }

    // 5. Header Action Buttons
    const actionHeader = document.querySelector('.flex.gap-sm');
    if (actionHeader && !document.getElementById('btn-add-space')) {
        actionHeader.innerHTML = `
            <button onclick="exportSingleZoneData(${zoneId})" class="px-md py-sm border-2 border-secondary text-secondary rounded-lg font-title-sm hover:bg-secondary-container transition-colors">
                Export Data
            </button>
            <button id="btn-add-space" onclick="promptAddSpace(${zoneId})" class="px-md py-sm bg-teal-600 text-white rounded-lg font-title-sm hover:bg-teal-700 transition-colors shadow-soft flex items-center gap-1">
                <span class="material-symbols-outlined text-sm">add</span> Add Space
            </button>
            <button onclick="simulateAIOccupancy(${zoneId})" class="px-md py-sm bg-primary text-on-primary rounded-lg font-title-sm hover:bg-primary-container transition-colors shadow-soft flex items-center gap-1">
                <span class="material-symbols-outlined text-sm">sensors</span> Trigger Detection
            </button>
        `;
    }

    // 6. Dynamic Bays Grid Rendering
    const grid = document.getElementById('dynamic-bays-grid');
    if (grid && detail.spaces) {
        grid.innerHTML = '';
        const subtitle = document.getElementById('zone-grid-subtitle');
        if (subtitle) subtitle.textContent = `Live sensor & AI camera mapping for ${detail.zone_name} (${detail.spaces.length} Total Bays)`;

        detail.spaces.forEach(s => {
            let borderClass = 'border-emerald-500 bg-emerald-50/60 text-emerald-950';
            let badgeBg = 'bg-emerald-100 text-emerald-800';
            let icon = 'check_circle';
            let label = 'AVAILABLE';

            if (s.status === 'occupied') {
                borderClass = 'border-rose-500 bg-rose-50/60 text-rose-950';
                badgeBg = 'bg-rose-100 text-rose-800';
                icon = 'directions_car';
                label = 'OCCUPIED (AI)';
            } else if (s.status === 'reserved') {
                borderClass = 'border-amber-500 bg-amber-50/60 text-amber-950';
                badgeBg = 'bg-amber-100 text-amber-800';
                icon = 'lock';
                label = 'RESERVED';
            }

            const bay = document.createElement('div');
            bay.className = `p-4 rounded-xl border-2 ${borderClass} flex flex-col justify-between shadow-sm transition-all hover:scale-[1.02]`;
            bay.innerHTML = `
                <div class="flex items-center justify-between mb-3">
                    <span class="font-mono font-extrabold text-xl text-primary">${s.space_number}</span>
                    <span class="material-symbols-outlined text-xl">${icon}</span>
                </div>
                <div class="flex justify-between items-center mt-2">
                    <span class="text-[10px] font-bold px-2 py-0.5 rounded-full ${badgeBg}">${label}</span>
                    <button onclick="toggleBayStatus(${zoneId}, ${s.id}, '${s.status}')" class="text-[10px] font-semibold text-gray-600 hover:text-primary underline">Toggle</button>
                </div>
            `;
            grid.appendChild(bay);
        });

        const syncTime = document.getElementById('last-sync-time');
        if (syncTime) syncTime.textContent = new Date().toLocaleTimeString();
    }
}

window.promptAddSpace = async function(zoneId) {
    const num = prompt("Enter Space Number (e.g. A-6):");
    if (!num) return;
    const res = await fetchAPI(`/zones/${zoneId}/spaces`, {
        method: 'POST',
        body: JSON.stringify({
            zone_id: parseInt(zoneId, 10),
            space_number: num,
            status: 'available'
        })
    });
    if (res && res.id) {
        alert(`✅ Space "${num}" added to Zone ${zoneId}!`);
        renderParkingZoneDetails();
    }
};

window.toggleBayStatus = async function(zoneId, spaceId, currentStatus) {
    const nextStatus = currentStatus === 'available' ? 'occupied' : 'available';
    await fetchAPI('/occupancy', {
        method: 'POST',
        body: JSON.stringify({
            zone_id: parseInt(zoneId, 10),
            space_id: parseInt(spaceId, 10),
            status: nextStatus,
            confidence: 0.98
        })
    });
    renderParkingZoneDetails();
};

window.simulateAIOccupancy = async function(zoneId) {
    const detail = await fetchAPI(`/availability/${zoneId}`);
    if (detail && detail.spaces && detail.spaces.length > 0) {
        const randomSpace = detail.spaces[Math.floor(Math.random() * detail.spaces.length)];
        const newStatus = randomSpace.status === 'occupied' ? 'available' : 'occupied';
        await fetchAPI('/occupancy', {
            method: 'POST',
            body: JSON.stringify({
                zone_id: parseInt(zoneId, 10),
                space_id: randomSpace.id,
                status: newStatus,
                confidence: 0.95
            })
        });
        alert(`📡 AI Detection Simulated: Space ${randomSpace.space_number} is now ${newStatus.toUpperCase()}`);
        renderParkingZoneDetails();
    }
};

window.exportSingleZoneData = async function(zoneId) {
    const detail = await fetchAPI(`/availability/${zoneId}`);
    if (!detail) return;
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(detail, null, 2));
    const dlAnchorElem = document.createElement('a');
    dlAnchorElem.setAttribute("href", dataStr);
    dlAnchorElem.setAttribute("download", `zone_${zoneId}_data_${new Date().toISOString().slice(0,10)}.json`);
    dlAnchorElem.click();
};

// --------------------------------------------------------------------------
// 5. Reservations Management Page Controller
// --------------------------------------------------------------------------
let allReservationsCache = [];

async function renderReservationsManagement() {
    const tbody = document.querySelector('table tbody');
    if (!tbody) return;

    const reservations = await fetchAPI('/reservations?limit=100');
    if (!reservations) return;
    allReservationsCache = reservations;

    // 1. Update Summary Stats Cards
    const total = reservations.length;
    const active = reservations.filter(r => r.status === 'active').length;
    const completed = reservations.filter(r => r.status === 'completed').length;
    const cancelled = reservations.filter(r => r.status === 'cancelled').length;

    const bentoNumbers = document.querySelectorAll('main .grid-cols-12 .font-display-lg');
    if (bentoNumbers.length >= 5) {
        bentoNumbers[0].textContent = total;
        bentoNumbers[1].textContent = active;
        bentoNumbers[2].textContent = '0'; // Pending (FastAPI auto-activates bookings)
        bentoNumbers[3].textContent = completed;
        bentoNumbers[4].textContent = cancelled;
    }

    // 2. Attach Search & Filter Listeners
    const searchInput = document.querySelector('input[placeholder="Search Reservations..."]');
    const statusSelect = document.querySelector('select');
    if (searchInput && !searchInput.dataset.bound) {
        searchInput.dataset.bound = 'true';
        searchInput.addEventListener('input', filterAndRenderReservationRows);
    }
    if (statusSelect && !statusSelect.dataset.bound) {
        statusSelect.dataset.bound = 'true';
        statusSelect.addEventListener('change', filterAndRenderReservationRows);
    }

    // 3. Attach New Reservation & Export Buttons
    document.querySelectorAll('button').forEach(btn => {
        const text = btn.textContent || '';
        if (text.includes('New Reservation') && !btn.dataset.bound) {
            btn.dataset.bound = 'true';
            btn.onclick = promptCreateReservation;
        } else if (text.includes('Export') && !btn.dataset.bound) {
            btn.dataset.bound = 'true';
            btn.onclick = exportReservationsData;
        }
    });

    filterAndRenderReservationRows();
}

function formatReservationDateTime(startIso, endIso) {
    if (!startIso) return { dateStr: "Today", dayStr: "", timeWindow: "Now", durationStr: "1.5 hrs" };

    const startMatch = String(startIso).match(/^(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2})/);
    let startDateObj = new Date(startIso);
    let year, month, day, startHours, startMins;

    if (startMatch) {
        year = parseInt(startMatch[1], 10);
        month = parseInt(startMatch[2], 10) - 1;
        day = parseInt(startMatch[3], 10);
        startHours = parseInt(startMatch[4], 10);
        startMins = parseInt(startMatch[5], 10);
        startDateObj = new Date(year, month, day, startHours, startMins);
    } else {
        year = startDateObj.getFullYear();
        month = startDateObj.getMonth();
        day = startDateObj.getDate();
        startHours = startDateObj.getHours();
        startMins = startDateObj.getMinutes();
    }

    const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    const days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];

    const dateStr = `${day} ${months[month]} ${year}`;
    const dayStr = days[startDateObj.getDay()];

    const formatTime12 = (h, m) => {
        const ampm = h >= 12 ? "PM" : "AM";
        const h12 = h % 12 === 0 ? 12 : h % 12;
        const mStr = String(m).padStart(2, "0");
        return `${h12}:${mStr} ${ampm}`;
    };

    const startTimeFormatted = formatTime12(startHours, startMins);
    let endTimeFormatted = "";
    let durationStr = "1.5 hrs";

    if (endIso) {
        const endMatch = String(endIso).match(/^(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2})/);
        let endHours, endMins, endDateObj;
        if (endMatch) {
            endHours = parseInt(endMatch[4], 10);
            endMins = parseInt(endMatch[5], 10);
            endDateObj = new Date(
                parseInt(endMatch[1], 10),
                parseInt(endMatch[2], 10) - 1,
                parseInt(endMatch[3], 10),
                endHours,
                endMins
            );
        } else {
            endDateObj = new Date(endIso);
            endHours = endDateObj.getHours();
            endMins = endDateObj.getMinutes();
        }
        endTimeFormatted = formatTime12(endHours, endMins);

        const diffMs = endDateObj.getTime() - startDateObj.getTime();
        const diffMins = Math.round(diffMs / 60000);
        if (diffMins > 0) {
            if (diffMins % 60 === 0) {
                durationStr = `${diffMins / 60} ${diffMins === 60 ? "hr" : "hrs"}`;
            } else {
                const hours = (diffMins / 60).toFixed(1).replace(/\.0$/, "");
                durationStr = `${hours} hrs`;
            }
        }
    }

    const timeWindow = endTimeFormatted ? `${startTimeFormatted} - ${endTimeFormatted}` : startTimeFormatted;

    return {
        dateStr,
        dayStr,
        startTimeFormatted,
        endTimeFormatted,
        timeWindow,
        durationStr,
    };
}

function filterAndRenderReservationRows() {
    const tbody = document.querySelector('table tbody');
    if (!tbody) return;

    const searchInput = document.querySelector('input[placeholder="Search Reservations..."]');
    const statusSelect = document.querySelector('select');

    const query = searchInput ? searchInput.value.toLowerCase().trim() : '';
    const statusFilter = statusSelect ? statusSelect.value.toLowerCase().trim() : '';

    let filtered = allReservationsCache.filter(r => {
        const matchesQuery = !query || 
            (r.driver_name && r.driver_name.toLowerCase().includes(query)) ||
            (r.driver_email && r.driver_email.toLowerCase().includes(query)) ||
            (r.vehicle_plate && r.vehicle_plate.toLowerCase().includes(query)) ||
            (`RES-${r.id}`.toLowerCase().includes(query));
        
        const matchesStatus = !statusFilter || r.status.toLowerCase() === statusFilter;
        return matchesQuery && matchesStatus;
    });

    const showingText = document.querySelector('main .border-t span.font-body-sm');
    if (showingText) {
        showingText.textContent = `Showing ${filtered.length} of ${allReservationsCache.length} reservations`;
    }

    if (filtered.length === 0) {
        tbody.innerHTML = `<tr><td colspan="8" class="p-8 text-center text-gray-400 font-sans">No reservations found matching your criteria.</td></tr>`;
        return;
    }

    tbody.innerHTML = '';
    filtered.forEach(r => {
        const tr = document.createElement('tr');
        tr.className = 'border-b border-gray-100 hover:bg-gray-50/50 transition-colors text-sm cursor-pointer';

        let badgeClass = 'bg-emerald-50 text-emerald-700 border border-emerald-200';
        let label = 'ACTIVE';
        if (r.status === 'cancelled') {
            badgeClass = 'bg-gray-100 text-gray-600 border border-gray-200';
            label = 'CANCELLED';
        } else if (r.status === 'completed') {
            badgeClass = 'bg-teal-50 text-teal-700 border border-teal-200';
            label = 'COMPLETED';
        }

        const dtInfo = formatReservationDateTime(r.start_time, r.end_time);

        tr.innerHTML = `
            <td class="p-4 font-mono font-bold text-primary">#RES-${r.id.toString().padStart(3, '0')}</td>
            <td class="p-4 font-bold text-primary">${r.driver_name}</td>
            <td class="p-4 font-mono text-gray-700">${r.vehicle_model ? `<span class="text-xs text-gray-500 mr-1">${r.vehicle_model}</span>` : ''}${r.vehicle_plate}</td>
            <td class="p-4 font-mono font-bold text-teal-700">Space #${r.space_id}</td>
            <td class="p-4 text-xs text-gray-600">${dtInfo.dateStr}</td>
            <td class="p-4 text-xs text-gray-600">${dtInfo.timeWindow}</td>
            <td class="p-4 text-center">
                <span class="px-3 py-1 rounded-full text-xs font-bold ${badgeClass}">${label}</span>
            </td>
            <td class="p-4 text-center">
                <div class="flex items-center justify-center gap-2">
                    <button onclick="event.stopPropagation(); viewReservationDetail(${r.id})" class="px-2.5 py-1 bg-gray-100 hover:bg-gray-200 text-primary rounded text-xs font-semibold">View</button>
                    ${r.status === 'active' ? `
                    <button onclick="event.stopPropagation(); cancelReservationById(${r.id})" class="px-2.5 py-1 bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 rounded text-xs font-bold transition-colors shadow-sm">
                        Cancel
                    </button>` : ''}
                </div>
            </td>
        `;
        tr.onclick = () => viewReservationDetail(r.id);
        tbody.appendChild(tr);
    });
}

window.promptCreateReservation = async function() {
    const spaceId = prompt("Enter Target Space ID (e.g. 1):", "1");
    if (!spaceId) return;
    const driverName = prompt("Enter Driver Full Name:", "Mahmoud Hassan");
    if (!driverName) return;
    const vehiclePlate = prompt("Enter Vehicle License Plate:", "ASW 9876");
    if (!vehiclePlate) return;

    const res = await fetchAPI('/reservations', {
        method: 'POST',
        body: JSON.stringify({
            space_id: parseInt(spaceId, 10),
            driver_name: driverName,
            vehicle_plate: vehiclePlate
        })
    });

    if (res && res.id) {
        alert(`✅ Reservation #${res.id} created successfully for Space #${spaceId}!`);
        renderReservationsManagement();
    }
};

window.viewReservationDetail = function(id) {
    const r = allReservationsCache.find(x => x.id === id);
    if (!r) return;

    const modal = document.getElementById('modal-res-001');
    if (!modal) return;

    const dtInfo = formatReservationDateTime(r.start_time, r.end_time);

    // Modal Header
    const modalId = modal.querySelector('#modal-res-id') || modal.querySelector('.font-mono-data');
    if (modalId) modalId.textContent = `ID: RES-${r.id.toString().padStart(3, '0')}`;

    const statusBadge = modal.querySelector('#modal-res-status-badge');
    if (statusBadge) {
        statusBadge.textContent = r.status.toUpperCase();
        if (r.status === 'active') {
            statusBadge.className = 'inline-flex items-center px-2 py-1 rounded bg-secondary/10 text-secondary font-label-caps text-label-caps font-bold ml-sm tracking-normal';
        } else if (r.status === 'cancelled') {
            statusBadge.className = 'inline-flex items-center px-2 py-1 rounded bg-rose-100 text-rose-700 font-label-caps text-label-caps font-bold ml-sm tracking-normal';
        } else {
            statusBadge.className = 'inline-flex items-center px-2 py-1 rounded bg-teal-100 text-teal-700 font-label-caps text-label-caps font-bold ml-sm tracking-normal';
        }
    }

    // Driver Info
    const driverNameEl = modal.querySelector('#modal-res-driver-name');
    if (driverNameEl) driverNameEl.textContent = r.driver_name;

    const driverEmailEl = modal.querySelector('#modal-res-driver-email');
    if (driverEmailEl) driverEmailEl.textContent = r.driver_email || 'No email provided';

    const driverPhoneEl = modal.querySelector('#modal-res-driver-phone');
    if (driverPhoneEl) driverPhoneEl.textContent = r.driver_phone || 'No phone provided';

    // Vehicle Info
    const vehicleModelEl = modal.querySelector('#modal-res-vehicle-model');
    if (vehicleModelEl) vehicleModelEl.textContent = r.vehicle_model || 'Car — Sedan';

    const vehiclePlateEl = modal.querySelector('#modal-res-vehicle-plate');
    if (vehiclePlateEl) vehiclePlateEl.textContent = r.vehicle_plate;

    // Booking Details
    const zoneNameEl = modal.querySelector('#modal-res-zone-name');
    if (zoneNameEl) zoneNameEl.textContent = 'Smart Curb Zone';

    const zoneSectorEl = modal.querySelector('#modal-res-zone-sector');
    if (zoneSectorEl) zoneSectorEl.textContent = `Space #${r.space_id}`;

    const dateEl = modal.querySelector('#modal-res-date');
    if (dateEl) dateEl.textContent = dtInfo.dateStr;

    const dayEl = modal.querySelector('#modal-res-day');
    if (dayEl) dayEl.textContent = dtInfo.dayStr;

    const timeWindowEl = modal.querySelector('#modal-res-time-window');
    if (timeWindowEl) timeWindowEl.textContent = dtInfo.timeWindow;

    const durationEl = modal.querySelector('#modal-res-duration');
    if (durationEl) durationEl.textContent = `Duration: ${dtInfo.durationStr}`;

    // Actions
    const cancelBtn = modal.querySelector('#modal-res-cancel-btn') || modal.querySelector('button.border-error');
    if (cancelBtn) {
        if (r.status === 'active') {
            cancelBtn.style.display = 'inline-flex';
            cancelBtn.onclick = () => {
                modal.classList.add('hidden');
                cancelReservationById(r.id);
            };
        } else {
            cancelBtn.style.display = 'none';
        }
    }

    modal.classList.remove('hidden');
};

window.cancelReservationById = async function(id) {
    if (!confirm(`Cancel Reservation #${id}? This will immediately free the space in the DB.`)) return;
    const res = await fetchAPI(`/reservations/${id}/cancel`, { method: 'PATCH' });
    if (res) {
        alert(`✅ Reservation #${res.id || id} cancelled! Space is now available.`);
        renderReservationsManagement();
    }
};

window.exportReservationsData = function() {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(allReservationsCache, null, 2));
    const dlAnchorElem = document.createElement('a');
    dlAnchorElem.setAttribute("href", dataStr);
    dlAnchorElem.setAttribute("download", `aswan_reservations_${new Date().toISOString().slice(0,10)}.json`);
    dlAnchorElem.click();
};

// --------------------------------------------------------------------------
// 6. Router & Live Polling (every 2.5s)
// --------------------------------------------------------------------------
document.addEventListener('DOMContentLoaded', () => {
    setupNavigationAndBanner();

    const path = window.location.pathname;
    if (path.includes('main_dashboard')) {
        renderMainDashboard();
        setInterval(renderMainDashboard, 2500);
    } else if (path.includes('parking_zones_list')) {
        renderParkingZonesList();
        setInterval(renderParkingZonesList, 2500);
    } else if (path.includes('parking_zone_details')) {
        renderParkingZoneDetails();
        setInterval(renderParkingZoneDetails, 2500);
    } else if (path.includes('reservations_management')) {
        renderReservationsManagement();
        setInterval(renderReservationsManagement, 2500);
    }
});

