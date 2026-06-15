(function() {
    // 1. Global authentication logic
    const token = localStorage.getItem('scorp_token');
    const role = localStorage.getItem('scorp_role');
    const email = localStorage.getItem('scorp_email') || 'User';

    // If no token and not on login page, redirect to login
    if (!token && !window.location.pathname.includes('login.html')) {
        window.location.href = 'login.html';
    }

    // 2. Anti-Flicker (FOUC) script
    if (role !== 'SUPER_ADMIN') {
        const style = document.createElement('style');
        style.innerHTML = `
            #nav-staff, 
            #adminBranchInputGroup, 
            #drawerAdminBranch { 
                display: none !important; 
            }
        `;
        document.head.appendChild(style);
    }

    // 3. Initialization function
    document.addEventListener('DOMContentLoaded', () => {
        // Populate profile data
        const userProfileEmail = document.getElementById('userProfileEmail');
        const userProfileRole = document.getElementById('userProfileRole');
        
        if (userProfileEmail) {
            userProfileEmail.innerText = email;
            userProfileEmail.classList.remove('animate-pulse');
        }
        
        if (userProfileRole) {
            userProfileRole.innerText = role === 'SUPER_ADMIN' ? 'admin' : 'instructor';
        }

        // Attach logout event listener
        const logoutBtn = document.getElementById('logoutBtn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => {
                localStorage.clear();
                window.location.href = 'login.html';
            });
        }

        // Secondary fallback to hide nav-staff
        const navStaff = document.getElementById('nav-staff');
        if (navStaff && role !== 'SUPER_ADMIN') {
            navStaff.style.display = 'none';
        }
    });
})();
