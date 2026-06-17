// frontend/static/js/app.js

const token = localStorage.getItem('scorp_token');
const role = localStorage.getItem('scorp_role') || 'INSTRUCTOR';
let cachedName = localStorage.getItem('scorp_real_name');
if (!cachedName || cachedName === 'undefined' || cachedName === 'null') {
    cachedName = localStorage.getItem('scorp_name') || 'Authorized User';
}

if (!token && !window.location.pathname.includes('login')) {
    window.location.href = 'login.html'; 
}

// =====================================================================
// ZERO-LATENCY LAYOUT ENGINE (Fixes the popping/loading delay completely)
// =====================================================================
if (role === 'SUPER_ADMIN') {
    document.write(`
        <style>
            .admin-only { display: flex !important; }
            .admin-block { display: block !important; }
            /* Admin: 3 Columns Desktop, 2 Columns Tablet, 1 Column Mobile */
            .metrics-container { display: grid !important; grid-template-columns: repeat(1, minmax(0, 1fr)); gap: 1rem; }
            @media (min-width: 640px) { .metrics-container { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
            @media (min-width: 1024px) { .metrics-container { grid-template-columns: repeat(3, minmax(0, 1fr)); } }
        </style>
    `);
} else {
    document.write(`
        <style>
            .admin-only, .admin-block { display: none !important; }
            /* Instructor: Straight Vertical Line */
            .metrics-container { display: flex !important; flex-direction: column !important; gap: 1rem; }
        </style>
    `);
}

// =====================================================================
// GLOBAL SIDEBAR & MOBILE RESPONSIVENESS BUILDER
// =====================================================================
function renderGlobalSidebar() {
    const sidebarContainer = document.getElementById('global-sidebar-container');
    
    if (sidebarContainer && sidebarContainer.innerHTML.trim() === '') {
        const sidebarHTML = `
            <div id="mobile-overlay" class="fixed inset-0 bg-black/50 z-30 hidden md:hidden backdrop-blur-sm transition-opacity"></div>
            
            <aside id="main-sidebar" class="fixed inset-y-0 left-0 w-60 bg-[#0A0A0A] border-r border-white/10 flex flex-col shrink-0 z-40 h-full transition-transform duration-300 -translate-x-full md:translate-x-0 md:relative">
                <div class="py-5 px-5 flex items-center justify-between border-b border-white/5">
                    <div class="flex items-center gap-2">
                        <div class="w-5 h-5 bg-white rounded-sm flex items-center justify-center text-black"><i class="ph-fill ph-shield-check text-[11px]"></i></div>
                        <h1 class="font-semibold tracking-tight text-sm text-white">Scorpion Academy</h1>
                    </div>
                    <button id="closeMobileMenu" class="md:hidden text-gray-400 hover:text-white"><i class="ph ph-x text-lg"></i></button>
                </div>
                <nav class="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
                    <a href="dashboard.html" class="nav-link flex items-center gap-2.5 px-2.5 py-1.5 text-gray-400 hover:bg-white/5 hover:text-white rounded-md font-medium transition-colors"><i class="ph ph-squares-four text-base"></i> Dashboard</a>
                    <a href="leads.html" class="nav-link flex items-center gap-2.5 px-2.5 py-1.5 text-gray-400 hover:bg-white/5 hover:text-white rounded-md font-medium transition-colors"><i class="ph ph-funnel text-base"></i> Lead Management</a>
                    <a href="students.html" class="nav-link flex items-center gap-2.5 px-2.5 py-1.5 text-gray-400 hover:bg-white/5 hover:text-white rounded-md font-medium transition-colors"><i class="ph ph-student text-base"></i> Students</a>
                    <a href="attendance.html" class="nav-link flex items-center gap-2.5 px-2.5 py-1.5 text-gray-400 hover:bg-white/5 hover:text-white rounded-md font-medium transition-colors"><i class="ph ph-notebook text-base"></i> Attendance</a>
                    <a href="accounting.html" class="nav-link flex items-center gap-2.5 px-2.5 py-1.5 text-gray-400 hover:bg-white/5 hover:text-white rounded-md font-medium transition-colors"><i class="ph ph-wallet text-base"></i> Accounting</a>
                    <a href="exams.html" class="nav-link flex items-center gap-2.5 px-2.5 py-1.5 text-gray-400 hover:bg-white/5 hover:text-white rounded-md font-medium transition-colors"><i class="ph ph-certificate text-base"></i> Belt Exams</a>
                    <a href="instructors.html" class="nav-link admin-only flex items-center gap-2.5 px-2.5 py-1.5 text-gray-400 hover:bg-white/5 hover:text-white rounded-md font-medium transition-colors"><i class="ph ph-chalkboard-teacher text-base"></i> Instructors</a>
                </nav>
                <div class="p-4 border-t border-white/5 space-y-3">
                    <div class="px-2.5 py-2 bg-white/5 rounded-lg border border-white/5">
                        <div id="sidebar-user-name" class="text-white font-medium text-xs truncate">${cachedName}</div>
                        <div class="text-gray-400 font-mono text-[9px] uppercase tracking-wider mt-0.5">${role === 'SUPER_ADMIN' ? 'admin' : 'instructor'}</div>
                    </div>
                    <button id="globalLogoutBtn" class="flex items-center gap-2 w-full px-2.5 py-1.5 text-gray-400 hover:text-white text-left transition-colors"><i class="ph ph-sign-out text-base"></i> Log Out</button>
                </div>
            </aside>
        `;
        
        sidebarContainer.innerHTML = sidebarHTML;

        // Auto-Highlight Active Link
        const currentPath = window.location.pathname.split('/').pop() || 'dashboard.html';
        document.querySelectorAll('.nav-link').forEach(link => {
            const linkPath = link.getAttribute('href');
            if (currentPath === linkPath || currentPath.includes(linkPath.replace('.html', ''))) {
                link.classList.add('bg-white/10', 'text-white');
                link.classList.remove('text-gray-400');
                const icon = link.querySelector('i');
                if(icon) icon.className = icon.className.replace('ph ', 'ph-fill ');
            }
        });

        // Mobile Menu Toggle Logic
        const header = document.querySelector('header');
        if(header) {
            header.insertAdjacentHTML('afterbegin', `<button id="mobileMenuToggle" class="md:hidden mr-3 p-1 text-gray-500 hover:text-black transition-colors"><i class="ph ph-list text-2xl"></i></button>`);
            
            const sidebar = document.getElementById('main-sidebar');
            const overlay = document.getElementById('mobile-overlay');
            const openBtn = document.getElementById('mobileMenuToggle');
            const closeBtn = document.getElementById('closeMobileMenu');

            function toggleMenu() {
                sidebar.classList.toggle('-translate-x-full');
                overlay.classList.toggle('hidden');
            }

            openBtn.addEventListener('click', toggleMenu);
            closeBtn.addEventListener('click', toggleMenu);
            overlay.addEventListener('click', toggleMenu);
        }

        document.getElementById('globalLogoutBtn').addEventListener('click', () => {
            localStorage.clear();
            window.location.href = 'login.html';
        });
    }
}

if (document.readyState === 'loading') { document.addEventListener('DOMContentLoaded', renderGlobalSidebar); } 
else { renderGlobalSidebar(); }