document.addEventListener('DOMContentLoaded', () => {
    // Global Chart Instances Cache
    const charts = {};

    // Initialize View Navigation & App
    initViewRouter();
    initAuth();
    initDashboardNav();
    initUploadHandlers();
    initProfileHandlers();
    initEventListeners();

    // Toast Notification System
    function showToast(message, type = 'success') {
        const container = document.getElementById('toastContainer');
        const toast = document.createElement('div');
        toast.className = 'toast';
        toast.style.borderColor = type === 'success' ? '#10A37F' : (type === 'info' ? '#383838' : '#EF4444');
        toast.innerHTML = message;
        container.appendChild(toast);
        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 300);
        }, 4000);
    }
    window.showToast = showToast;

    // Contact Form Handler
    window.submitContactForm = function() {
        const name = document.getElementById('contactName').value.trim();
        showToast(`Thank you ${name}. Your message has been received.`);
        document.getElementById('contactForm').reset();
    };

    // ========================================================
    // 🧭 1. VIEW ROUTING (Home Page <-> Dashboard)
    // ========================================================
    function initViewRouter() {
        const homeSection = document.getElementById('homePageSection');
        const dashSection = document.getElementById('dashboardSection');
        const loginModal = document.getElementById('loginModal');

        // Check if user already authenticated
        const token = localStorage.getItem('retail_ai_token');
        const userJson = localStorage.getItem('retail_ai_user');

        if (token && userJson) {
            // Default to Dashboard if logged in
            showDashboard();
        } else {
            // Default to Home page
            showHomePage();
        }

        // Navigation Button Listeners
        const btnHomeSignIn = document.getElementById('btnHomeSignIn');
        if (btnHomeSignIn) {
            btnHomeSignIn.addEventListener('click', () => {
                loginModal.style.display = 'flex';
                renderGoogleButtons();
            });
        }

        const btnCloseAuth = document.getElementById('btnCloseAuthModal');
        if (btnCloseAuth) {
            btnCloseAuth.addEventListener('click', () => {
                loginModal.style.display = 'none';
            });
        }

        const btnHeroGetStarted = document.getElementById('btnHeroGetStarted');
        if (btnHeroGetStarted) {
            btnHeroGetStarted.addEventListener('click', () => {
                const currentToken = localStorage.getItem('retail_ai_token');
                if (currentToken) {
                    showDashboard();
                } else {
                    loginModal.style.display = 'flex';
                    renderGoogleButtons();
                }
            });
        }

        const btnHeroViewDocs = document.getElementById('btnHeroViewDocs');
        if (btnHeroViewDocs) {
            btnHeroViewDocs.addEventListener('click', () => {
                const templ = document.getElementById('templatesSection');
                if (templ) templ.scrollIntoView({ behavior: 'smooth' });
            });
        }

        const btnNavBackHome = document.getElementById('btnNavBackHome');
        if (btnNavBackHome) {
            btnNavBackHome.addEventListener('click', () => {
                showHomePage();
            });
        }
    }

    function showHomePage() {
        document.getElementById('homePageSection').style.display = 'block';
        document.getElementById('dashboardSection').style.display = 'none';
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    function isImageAvatar(avatar) {
        return Boolean(
            avatar && (
                avatar.startsWith('http://') ||
                avatar.startsWith('https://') ||
                avatar.startsWith('data:image/')
            )
        );
    }

    function applyUserUI(user) {
        if (!user) return;
        const hasImg = isImageAvatar(user.avatar);

        const badge = document.getElementById('userBadgeName');
        if (badge) {
            const avatarHtml = hasImg
                ? `<img src="${user.avatar}" alt="Avatar" style="width:18px; height:18px; border-radius:50%; vertical-align:middle; margin-right:6px; object-fit:cover;">`
                : '';
            badge.innerHTML = `${avatarHtml}${user.full_name || user.username}`;
        }

        const renderAvatarInto = (elId) => {
            const el = document.getElementById(elId);
            if (!el) return;
            if (hasImg) {
                el.innerHTML = `<img src="${user.avatar}" alt="Avatar" style="width:68px; height:68px; border-radius:50%; object-fit:cover; display:block;">`;
            } else {
                el.innerHTML = `<i data-lucide="user" style="width:28px; height:28px; color:var(--text-primary);"></i>`;
            }
        };
        renderAvatarInto('profAvatar');
        renderAvatarInto('editProfAvatar');

        const fullNameParts = (user.full_name || '').trim().split(' ');
        const firstName = user.first_name || fullNameParts[0] || '';
        const lastName = user.last_name || fullNameParts.slice(1).join(' ');
        const displayFullName = `${firstName} ${lastName}`.trim() || user.full_name || user.username || 'Retail User';

        // 1. Update Read-Only Profile View
        const setViewText = (id, val, fallback = 'Not set') => {
            const el = document.getElementById(id);
            if (!el) return;
            const clean = (val || '').trim();
            if (clean) {
                el.textContent = clean;
                el.classList.remove('profile-detail-empty');
            } else {
                el.textContent = fallback;
                el.classList.add('profile-detail-empty');
            }
        };

        setViewText('viewProfFullName', displayFullName, 'Retail User');
        setViewText('viewProfEmail', user.email, 'user@company.com');
        setViewText('viewProfFirstName', firstName);
        setViewText('viewProfLastName', lastName);
        setViewText('viewProfEmailVal', user.email);
        setViewText('viewProfPhone', user.phone);
        setViewText('viewProfLanguage', user.default_language || 'English', 'English');
        setViewText('viewProfDirection', user.direction || 'System Default', 'System Default');
        setViewText('viewProfFacebook', user.facebook);
        setViewText('viewProfLinkedin', user.linkedin);
        setViewText('viewProfSkype', user.skype);
        setViewText('viewProfSignature', user.email_signature);

        // 2. Sync Edit Profile Modal Form Inputs
        const setVal = (id, val) => {
            const el = document.getElementById(id);
            if (el) el.value = val || '';
        };
        setVal('profFirstName', firstName);
        setVal('profLastName', lastName);
        setVal('profEmailInput', user.email || '');
        setVal('profPhone', user.phone || '');
        setVal('profLanguage', user.default_language || 'English');
        setVal('profDirection', user.direction || 'System Default');
        setVal('profFacebook', user.facebook || '');
        setVal('profLinkedin', user.linkedin || '');
        setVal('profSkype', user.skype || '');
        setVal('profSignature', user.email_signature || '');

        if (window.lucide) lucide.createIcons();
    }

    async function loadUserProfile() {
        const token = localStorage.getItem('retail_ai_token');
        if (!token) return;
        try {
            const res = await fetch(`/api/profile?token=${encodeURIComponent(token)}`);
            if (!res.ok) return;
            const data = await res.json();
            if (data.success && data.user) {
                localStorage.setItem('retail_ai_user', JSON.stringify(data.user));
                applyUserUI(data.user);
            }
        } catch (e) {
            console.warn('Profile fetch notice:', e);
        }
    }

    function showDashboard() {
        document.getElementById('homePageSection').style.display = 'none';
        document.getElementById('dashboardSection').style.display = 'block';

        const userJson = localStorage.getItem('retail_ai_user');
        if (userJson) {
            applyUserUI(JSON.parse(userJson));
        }

        // Initialize Lucide icons
        if (window.lucide) lucide.createIcons();

        // Load Dashboard & Profile Data
        loadDashboard();
        loadCatalogProducts();
        loadDatasetHistory();
        loadDbStatistics();
        loadUserProfile();
    }

    // ========================================================
    // 🔐 2. AUTHENTICATION & GOOGLE OAUTH
    // ========================================================
    const GOOGLE_CLIENT_ID = '815551152014-sfm7lgsvisfua5o1f2fh26o4r4d3kd0p.apps.googleusercontent.com';

    function initAuth() {
        // Tab Switching in Auth Modal
        const tabBtnSignIn = document.getElementById('tabBtnSignIn');
        const tabBtnRegister = document.getElementById('tabBtnRegister');
        const signInPanel = document.getElementById('signInPanel');
        const registerPanel = document.getElementById('registerPanel');
        const errDiv = document.getElementById('loginError');
        const succDiv = document.getElementById('loginSuccess');

        if (tabBtnSignIn && tabBtnRegister) {
            tabBtnSignIn.addEventListener('click', () => {
                tabBtnSignIn.classList.add('active');
                tabBtnRegister.classList.remove('active');
                signInPanel.style.display = 'block';
                registerPanel.style.display = 'none';
                errDiv.style.display = 'none';
                succDiv.style.display = 'none';
                renderGoogleButtons();
            });

            tabBtnRegister.addEventListener('click', () => {
                tabBtnRegister.classList.add('active');
                tabBtnSignIn.classList.remove('active');
                signInPanel.style.display = 'none';
                registerPanel.style.display = 'block';
                errDiv.style.display = 'none';
                succDiv.style.display = 'none';
                renderGoogleButtons();
            });
        }

        // Custom Google Auth Button Listeners
        const btnCustomGoogleSignIn = document.getElementById('btnCustomGoogleSignIn');
        if (btnCustomGoogleSignIn) {
            btnCustomGoogleSignIn.addEventListener('click', triggerGoogleAuthFlow);
        }

        const btnCustomGoogleSignUp = document.getElementById('btnCustomGoogleSignUp');
        if (btnCustomGoogleSignUp) {
            btnCustomGoogleSignUp.addEventListener('click', triggerGoogleAuthFlow);
        }

        // Initialize Google Identity Services
        initGoogleAuth();

        // Login Action
        document.getElementById('btnLogin').addEventListener('click', performLogin);

        // Register Action
        const btnRegister = document.getElementById('btnRegister');
        if (btnRegister) {
            btnRegister.addEventListener('click', performRegister);
        }

        // Logout Action
        document.getElementById('btnLogout').addEventListener('click', async () => {
            const currentToken = localStorage.getItem('retail_ai_token');
            if (currentToken) {
                try {
                    await fetch('/api/auth/logout', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({token: currentToken})
                    });
                } catch (e) {}
            }
            localStorage.removeItem('retail_ai_token');
            localStorage.removeItem('retail_ai_user');
            showToast('Signed out successfully.', 'info');
            showHomePage();
        });
    }

    // Google Identity Services & OAuth 2.0 Setup
    let googleTokenClient = null;

    function initGoogleAuth() {
        if (window.google && window.google.accounts) {
            // 1. Initialize Credential ID client
            if (window.google.accounts.id) {
                try {
                    google.accounts.id.initialize({
                        client_id: GOOGLE_CLIENT_ID,
                        callback: handleGoogleCredentialResponse,
                        auto_select: false,
                        cancel_on_tap_outside: true
                    });
                } catch (e) {
                    console.warn('Google id initialization note:', e);
                }
            }

            // 2. Initialize OAuth 2.0 Token Client (Popup flow for custom button)
            if (window.google.accounts.oauth2) {
                try {
                    googleTokenClient = google.accounts.oauth2.initTokenClient({
                        client_id: GOOGLE_CLIENT_ID,
                        scope: 'email profile openid',
                        callback: async (tokenResponse) => {
                            if (tokenResponse && tokenResponse.access_token) {
                                await handleGoogleAccessToken(tokenResponse.access_token);
                            } else if (tokenResponse && tokenResponse.error) {
                                handleGoogleAuthError(tokenResponse.error_description || tokenResponse.error);
                            }
                        },
                        error_callback: (err) => {
                            handleGoogleAuthError(err && err.message ? err.message : 'Google Cloud origin verification check');
                        }
                    });
                } catch (e) {
                    console.warn('Google oauth2 initialization note:', e);
                }
            }
        } else {
            setTimeout(initGoogleAuth, 300);
        }
    }

    function triggerGoogleAuthFlow() {
        const errDiv = document.getElementById('loginError');
        const succDiv = document.getElementById('loginSuccess');
        if (errDiv) errDiv.style.display = 'none';

        // 1. Try Google OAuth 2.0 Token Client (Official popup)
        if (googleTokenClient) {
            try {
                googleTokenClient.requestAccessToken({ prompt: 'select_account' });
                return;
            } catch (e) {
                console.warn('requestAccessToken error:', e);
            }
        }

        // 2. Try Google One-Tap / ID prompt
        if (window.google && window.google.accounts && window.google.accounts.id) {
            try {
                google.accounts.id.prompt((notification) => {
                    if (notification.isNotDisplayed() || notification.isSkippedMoment()) {
                        fallbackGoogleOAuthPopup();
                    }
                });
                return;
            } catch (e) {
                console.warn('google.accounts.id.prompt error:', e);
            }
        }

        // 3. Fallback Popup
        fallbackGoogleOAuthPopup();
    }

    function fallbackGoogleOAuthPopup() {
        const redirectUri = window.location.origin;
        const authUrl = `https://accounts.google.com/o/oauth2/v2/auth?client_id=${GOOGLE_CLIENT_ID}&redirect_uri=${encodeURIComponent(redirectUri)}&response_type=token&scope=openid%20email%20profile&prompt=select_account`;
        const popup = window.open(authUrl, 'GoogleSignIn', 'width=520,height=630,status=no,toolbar=no,menubar=no');

        if (!popup || popup.closed || typeof popup.closed === 'undefined') {
            const errDiv = document.getElementById('loginError');
            if (errDiv) {
                errDiv.textContent = 'Pop-up was blocked by browser. Please allow popups for this site.';
                errDiv.style.display = 'block';
            }
            return;
        }

        const timer = setInterval(() => {
            try {
                if (popup.closed) {
                    clearInterval(timer);
                    return;
                }
                if (popup.location.href.includes(redirectUri)) {
                    const hash = popup.location.hash;
                    popup.close();
                    clearInterval(timer);
                    if (hash) {
                        const params = new URLSearchParams(hash.substring(1));
                        const accessToken = params.get('access_token');
                        if (accessToken) {
                            handleGoogleAccessToken(accessToken);
                        }
                    }
                }
            } catch (e) {}
        }, 500);
    }

    function handleGoogleAuthError(errMsg) {
        const errDiv = document.getElementById('loginError');
        if (errDiv) {
            errDiv.innerHTML = `Google OAuth Notice: ${errMsg}<br><small style="color:var(--text-secondary);">Ensure <code>${window.location.origin}</code> is in <strong>Authorized JavaScript origins</strong> in Google Cloud Console.</small>`;
            errDiv.style.display = 'block';
        }
    }

    async function handleGoogleAccessToken(accessToken) {
        const errDiv = document.getElementById('loginError');
        const succDiv = document.getElementById('loginSuccess');

        try {
            if (errDiv) errDiv.style.display = 'none';
            if (succDiv) {
                succDiv.textContent = 'Verifying Google account...';
                succDiv.style.display = 'block';
            }

            const res = await fetch('/api/auth/google', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({access_token: accessToken})
            });

            if (!res.ok) {
                const errData = await res.json();
                if (succDiv) succDiv.style.display = 'none';
                if (errDiv) {
                    errDiv.textContent = errData.detail || 'Google sign-in failed.';
                    errDiv.style.display = 'block';
                }
                return;
            }

            const data = await res.json();
            localStorage.setItem('retail_ai_token', data.token);
            localStorage.setItem('retail_ai_user', JSON.stringify(data.user));

            if (succDiv) {
                succDiv.textContent = 'Signed in successfully. Opening dashboard...';
                succDiv.style.display = 'block';
            }

            setTimeout(() => {
                document.getElementById('loginModal').style.display = 'none';
                if (succDiv) succDiv.style.display = 'none';
                showToast(`Signed in as ${data.user.full_name || data.user.email}.`);
                showDashboard();
            }, 600);

        } catch (ex) {
            if (succDiv) succDiv.style.display = 'none';
            if (errDiv) {
                errDiv.textContent = `Server connection error: ${ex.message}`;
                errDiv.style.display = 'block';
            }
        }
    }

    async function handleGoogleCredentialResponse(response) {
        const errDiv = document.getElementById('loginError');
        const succDiv = document.getElementById('loginSuccess');

        if (!response || !response.credential) {
            if (errDiv) {
                errDiv.textContent = 'Google authentication was not completed.';
                errDiv.style.display = 'block';
            }
            return;
        }

        try {
            if (errDiv) errDiv.style.display = 'none';
            if (succDiv) {
                succDiv.textContent = 'Authenticating with Google...';
                succDiv.style.display = 'block';
            }

            const res = await fetch('/api/auth/google', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({credential: response.credential})
            });

            if (!res.ok) {
                const errData = await res.json();
                if (succDiv) succDiv.style.display = 'none';
                if (errDiv) {
                    errDiv.textContent = errData.detail || 'Google sign-in failed.';
                    errDiv.style.display = 'block';
                }
                return;
            }

            const data = await res.json();
            localStorage.setItem('retail_ai_token', data.token);
            localStorage.setItem('retail_ai_user', JSON.stringify(data.user));

            if (succDiv) {
                succDiv.textContent = 'Signed in successfully. Opening dashboard...';
                succDiv.style.display = 'block';
            }

            setTimeout(() => {
                document.getElementById('loginModal').style.display = 'none';
                if (succDiv) succDiv.style.display = 'none';
                showToast(`Signed in as ${data.user.full_name || data.user.email}.`);
                showDashboard();
            }, 600);

        } catch (ex) {
            if (succDiv) succDiv.style.display = 'none';
            if (errDiv) {
                errDiv.textContent = `Server connection error during Google sign-in: ${ex.message}`;
                errDiv.style.display = 'block';
            }
        }
    }

    async function performLogin() {
        const username = document.getElementById('loginUser').value.trim();
        const password = document.getElementById('loginPass').value.trim();
        const errDiv = document.getElementById('loginError');

        if (!username || !password) {
            errDiv.textContent = 'Please enter both username or email and password.';
            errDiv.style.display = 'block';
            return;
        }

        try {
            const res = await fetch('/api/auth/login', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({username, password})
            });

            if (!res.ok) {
                const errData = await res.json();
                errDiv.textContent = errData.detail || 'Login failed.';
                errDiv.style.display = 'block';
                return;
            }

            const data = await res.json();
            localStorage.setItem('retail_ai_token', data.token);
            localStorage.setItem('retail_ai_user', JSON.stringify(data.user));

            errDiv.style.display = 'none';
            document.getElementById('loginModal').style.display = 'none';
            
            showToast(`Welcome back, ${data.user.full_name || data.user.username}! Signed in successfully.`);
            showDashboard();
        } catch (e) {
            errDiv.textContent = 'Connection error with server.';
            errDiv.style.display = 'block';
        }
    }

    async function performRegister() {
        const fullName = document.getElementById('regFullName').value.trim();
        const username = document.getElementById('regUser').value.trim();
        const email = document.getElementById('regEmail').value.trim();
        const role = 'Retail Analyst';
        const password = document.getElementById('regPass').value.trim();
        const errDiv = document.getElementById('loginError');
        const succDiv = document.getElementById('loginSuccess');

        if (!username || !email || !password || !fullName) {
            errDiv.textContent = 'Please fill out all registration fields.';
            errDiv.style.display = 'block';
            return;
        }

        try {
            const res = await fetch('/api/auth/register', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    username,
                    email,
                    password,
                    full_name: fullName,
                    role,
                    company: 'Enterprise Suite'
                })
            });

            if (!res.ok) {
                const errData = await res.json();
                errDiv.textContent = errData.detail || 'Registration failed.';
                errDiv.style.display = 'block';
                succDiv.style.display = 'none';
                return;
            }

            const data = await res.json();
            localStorage.setItem('retail_ai_token', data.token);
            localStorage.setItem('retail_ai_user', JSON.stringify(data.user));

            errDiv.style.display = 'none';
            succDiv.textContent = 'Account created. Opening dashboard...';
            succDiv.style.display = 'block';

            setTimeout(() => {
                document.getElementById('loginModal').style.display = 'none';
                showToast(`Welcome, ${data.user.full_name}. Account created.`);
                showDashboard();
            }, 600);

        } catch (e) {
            errDiv.textContent = 'Server error during account registration.';
            errDiv.style.display = 'block';
        }
    }

    // ========================================================
    // 🗄️ 3. SYSTEM HEALTH & METRICS
    // ========================================================
    async function loadDbStatistics() {
        try {
            const res = await fetch('/api/db/stats');
            if (!res.ok) return;
            const data = await res.json();

            // Header Pill
            const dbBadge = document.getElementById('dbStatusLabel');
            if (dbBadge) {
                dbBadge.textContent = 'Engine Active';
            }

            // Profile Tab Stats
            if (document.getElementById('profTotalUsers')) {
                document.getElementById('profTotalUsers').textContent = data.total_registered_users || 3;
                document.getElementById('profTotalChats').textContent = data.total_logged_chat_queries || 0;
            }
        } catch (e) {
            console.warn('Error loading system stats:', e);
        }
    }

    // ========================================================
    // 🧭 4. DASHBOARD SIDEBAR NAVIGATION (Matches Hand Sketch)
    // ========================================================
    function initDashboardNav() {
        const navItems = document.querySelectorAll('.sidebar .nav-item');
        navItems.forEach(item => {
            item.addEventListener('click', () => {
                const targetTab = item.getAttribute('data-tab');
                if (!targetTab) return;

                navItems.forEach(n => n.classList.remove('active'));
                item.classList.add('active');

                // Switch Tab Content
                document.querySelectorAll('.tab-content').forEach(tc => tc.classList.remove('active'));
                const activeTab = document.getElementById(`tab-${targetTab}`);
                if (activeTab) activeTab.classList.add('active');

                // Trigger tab-specific loaders
                if (targetTab === 'dashboard') loadDashboard();
                if (targetTab === 'analytics') loadAnalytics();
                if (targetTab === 'prediction') loadPrediction();
                if (targetTab === 'history') loadDatasetHistory();
                if (targetTab === 'profile') loadUserProfile();
            });
        });

        // Notification Bell Dropdown Toggle
        const btnBell = document.getElementById('btnNotificationBell');
        const notifDropdown = document.getElementById('notificationDropdown');
        if (btnBell && notifDropdown) {
            btnBell.addEventListener('click', (e) => {
                e.stopPropagation();
                notifDropdown.style.display = notifDropdown.style.display === 'none' ? 'block' : 'none';
            });

            document.addEventListener('click', () => {
                notifDropdown.style.display = 'none';
            });
        }
    }

    // ========================================================
    // 📜 5. DATASET HISTORY & SELECTION
    // ========================================================
    async function loadDatasetHistory() {
        const res = await fetch('/api/datasets');
        const data = await res.json();
        const tbody = document.querySelector('#historyTable tbody');
        if (!tbody) return;
        tbody.innerHTML = '';

        data.datasets.forEach(d => {
            if (d.is_active) {
                const activeLabel = document.getElementById('activeDatasetLabel');
                if (activeLabel) activeLabel.textContent = `Active: ${d.filename}`;
                if (document.getElementById('floatChatDatasetPill')) {
                    document.getElementById('floatChatDatasetPill').textContent = `QA: ${d.filename}`;
                }
            }

            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${d.is_active ? '<span class="pill pill-emerald">Active</span>' : '<span class="pill pill-indigo">Archived</span>'}</td>
                <td><strong>${d.filename}</strong></td>
                <td>${d.upload_time}</td>
                <td>${d.cleaned_rows.toLocaleString()}</td>
                <td><strong>£${d.total_revenue.toLocaleString()}</strong></td>
                <td>${d.total_customers.toLocaleString()}</td>
                <td>${d.total_products.toLocaleString()}</td>
                <td>
                    ${d.is_active ? 
                        '<span style="color:#10B981; font-weight:600; font-size:0.8125rem;">Active</span>' : 
                        `<div style="display:flex; gap:6px;">
                            <button class="btn-secondary btn-select-ds" data-id="${d.dataset_id}" style="padding:4px 10px; font-size:0.75rem;">Select</button>
                            ${!d.is_default ? `<button class="btn-secondary btn-delete-ds" data-id="${d.dataset_id}" style="padding:4px 8px; font-size:0.75rem; color:#F87171;">Delete</button>` : ''}
                        </div>`}
                </td>
            `;
            tbody.appendChild(tr);
        });

        // Add Listeners to Select Buttons
        document.querySelectorAll('.btn-select-ds').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const dsId = e.currentTarget.getAttribute('data-id');
                await switchActiveDataset(dsId);
            });
        });

        // Add Listeners to Delete Buttons
        document.querySelectorAll('.btn-delete-ds').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const dsId = e.currentTarget.getAttribute('data-id');
                if (confirm('Permanently delete this dataset?')) {
                    await deleteDataset(dsId);
                }
            });
        });
    }

    async function switchActiveDataset(dsId) {
        const res = await fetch(`/api/datasets/select/${dsId}`, {method: 'POST'});
        const data = await res.json();
        if (data.success) {
            showToast(`Active dataset switched to: ${data.metadata.filename}`);
            loadDatasetHistory();
            loadDashboard();
            loadAnalytics();
            loadCatalogProducts();
            loadPrediction();
            loadDbStatistics();
        }
    }

    async function deleteDataset(dsId) {
        const res = await fetch(`/api/datasets/${dsId}`, {method: 'DELETE'});
        const data = await res.json();
        if (data.success) {
            showToast('Dataset deleted.', 'info');
            loadDatasetHistory();
            loadDbStatistics();
        }
    }

    // ========================================================
    // 6. REAL-TIME DATASET UPLOAD (Dedicated Page)
    // ========================================================
    function initUploadHandlers() {
        const dropzone = document.getElementById('uploadDropzone');
        const btnBrowse = document.getElementById('btnBrowseUploadFile');
        const fileInput = document.getElementById('fileInput');
        const statusDiv = document.getElementById('uploadStatus');

        if (btnBrowse && fileInput) {
            btnBrowse.addEventListener('click', (e) => {
                e.stopPropagation();
                fileInput.click();
            });
        }

        if (dropzone && fileInput) {
            dropzone.addEventListener('click', () => fileInput.click());
            dropzone.addEventListener('dragover', (e) => {
                e.preventDefault();
                dropzone.style.background = '#1C1C1C';
                dropzone.style.borderColor = '#555555';
            });
            dropzone.addEventListener('dragleave', () => {
                dropzone.style.background = '#141414';
                dropzone.style.borderColor = '#2A2A2A';
            });
            dropzone.addEventListener('drop', (e) => {
                e.preventDefault();
                dropzone.style.background = '#141414';
                dropzone.style.borderColor = '#2A2A2A';
                if (e.dataTransfer.files.length > 0) uploadDatasetFile(e.dataTransfer.files[0]);
            });
        }

        if (fileInput) {
            fileInput.addEventListener('change', () => {
                if (fileInput.files.length > 0) uploadDatasetFile(fileInput.files[0]);
            });
        }

        async function uploadDatasetFile(file) {
            statusDiv.style.display = 'block';
            statusDiv.innerHTML = `<span style="color:var(--text-secondary);">Processing <strong>${file.name}</strong> and running analytical models...</span>`;

            const formData = new FormData();
            formData.append('file', file);

            try {
                const res = await fetch('/api/upload', {
                    method: 'POST',
                    body: formData
                });

                if (!res.ok) {
                    const err = await res.json();
                    statusDiv.innerHTML = `<span style="color:#EF4444;">Upload error: ${err.detail || 'Upload failed.'}</span>`;
                    if (fileInput) fileInput.value = '';
                    return;
                }

                const data = await res.json();
                if (fileInput) fileInput.value = '';

                statusDiv.innerHTML = `
                    <div style="color:#10A37F; font-weight:600; margin-bottom:6px;">Dataset analyzed and archived successfully.</div>
                    <div style="color:var(--text-secondary); margin-bottom:14px;">
                        <strong>${file.name}</strong> — ${data.metadata.cleaned_rows.toLocaleString()} clean rows | £${data.metadata.total_revenue.toLocaleString()} revenue | ${data.metadata.total_customers.toLocaleString()} customers
                    </div>
                    <button type="button" id="btnGoDashboardAfterUpload" class="btn-primary" style="padding:8px 20px;">
                        View Dashboard Analysis
                    </button>
                `;

                const btnGoDash = document.getElementById('btnGoDashboardAfterUpload');
                if (btnGoDash) {
                    btnGoDash.addEventListener('click', () => {
                        const dashNav = document.querySelector('.sidebar .nav-item[data-tab="dashboard"]');
                        if (dashNav) dashNav.click();
                    });
                }

                showToast(`Dataset ${file.name} uploaded and analyzed.`);
                loadDatasetHistory();
                loadDashboard();
                loadAnalytics();
                loadCatalogProducts();
                loadPrediction();
                loadDbStatistics();

            } catch (ex) {
                if (fileInput) fileInput.value = '';
                statusDiv.innerHTML = `<span style="color:#EF4444;">Upload error: ${ex.message}</span>`;
            }
        }
    }

    // ========================================================
    // 6B. PROFILE MODALS HANDLERS (Edit Profile & Change Password)
    // ========================================================
    function initProfileHandlers() {
        let pendingAvatarDataUrl = null;

        const editModal = document.getElementById('editProfileModal');
        const btnOpenEdit = document.getElementById('btnOpenEditProfile');
        const btnCloseEdit = document.getElementById('btnCloseEditProfile');
        const btnCancelEdit = document.getElementById('btnCancelEditProfile');
        const editErr = document.getElementById('editProfileError');

        const pwModal = document.getElementById('changePasswordModal');
        const btnOpenPw = document.getElementById('btnOpenChangePassword');
        const btnClosePw = document.getElementById('btnCloseChangePassword');
        const btnCancelPw = document.getElementById('btnCancelChangePassword');
        const pwErr = document.getElementById('changePasswordError');

        const btnUploadPhoto = document.getElementById('btnUploadProfPhoto');
        const photoInput = document.getElementById('profPhotoInput');
        const editAvatarEl = document.getElementById('editProfAvatar');
        const btnSaveProfile = document.getElementById('btnSaveProfile');
        const btnSavePassword = document.getElementById('btnSavePassword');

        const closeEditModal = () => {
            if (editModal) editModal.style.display = 'none';
            pendingAvatarDataUrl = null;
            if (photoInput) photoInput.value = '';
            if (editErr) editErr.style.display = 'none';
        };

        const closePwModal = () => {
            if (pwModal) pwModal.style.display = 'none';
            if (pwErr) pwErr.style.display = 'none';
            ['profOldPassword', 'profNewPassword', 'profRepeatPassword'].forEach(id => {
                const el = document.getElementById(id);
                if (el) {
                    el.value = '';
                    el.type = 'password';
                }
            });
            document.querySelectorAll('#changePasswordModal .btn-toggle-pw').forEach(b => {
                b.innerHTML = `<i data-lucide="eye-off" style="width:16px; height:16px;"></i>`;
            });
            if (window.lucide) lucide.createIcons();
        };

        if (btnOpenEdit && editModal) {
            btnOpenEdit.addEventListener('click', () => {
                const userJson = localStorage.getItem('retail_ai_user');
                if (userJson) applyUserUI(JSON.parse(userJson));
                pendingAvatarDataUrl = null;
                if (photoInput) photoInput.value = '';
                if (editErr) editErr.style.display = 'none';
                editModal.style.display = 'flex';
            });
        }
        if (btnCloseEdit) btnCloseEdit.addEventListener('click', closeEditModal);
        if (btnCancelEdit) btnCancelEdit.addEventListener('click', closeEditModal);

        if (btnOpenPw && pwModal) {
            btnOpenPw.addEventListener('click', () => {
                closePwModal();
                pwModal.style.display = 'flex';
            });
        }
        if (btnClosePw) btnClosePw.addEventListener('click', closePwModal);
        if (btnCancelPw) btnCancelPw.addEventListener('click', closePwModal);

        if (btnUploadPhoto && photoInput) {
            btnUploadPhoto.addEventListener('click', () => photoInput.click());

            photoInput.addEventListener('change', () => {
                const file = photoInput.files && photoInput.files[0];
                if (!file) return;

                if (file.size > 2 * 1024 * 1024) {
                    showToast('Photo exceeds 2MB limit. Please choose a smaller image.', 'error');
                    photoInput.value = '';
                    return;
                }

                const reader = new FileReader();
                reader.onload = (ev) => {
                    pendingAvatarDataUrl = ev.target.result;
                    if (editAvatarEl) {
                        editAvatarEl.innerHTML = `<img src="${pendingAvatarDataUrl}" alt="Profile Photo" style="width:68px; height:68px; border-radius:50%; object-fit:cover; display:block;">`;
                    }
                };
                reader.readAsDataURL(file);
            });
        }

        // Password show/hide eye toggles
        document.querySelectorAll('.btn-toggle-pw').forEach(btn => {
            btn.addEventListener('click', () => {
                const targetId = btn.getAttribute('data-target');
                const input = document.getElementById(targetId);
                if (!input) return;

                const isPassword = input.type === 'password';
                input.type = isPassword ? 'text' : 'password';
                btn.innerHTML = `<i data-lucide="${isPassword ? 'eye' : 'eye-off'}" style="width:16px; height:16px;"></i>`;
                if (window.lucide) lucide.createIcons();
            });
        });

        // Save Edit Profile Popup
        if (btnSaveProfile) {
            btnSaveProfile.addEventListener('click', async () => {
                const token = localStorage.getItem('retail_ai_token');
                if (!token) {
                    showToast('Please sign in to save profile changes.', 'error');
                    return;
                }

                const getVal = (id) => {
                    const el = document.getElementById(id);
                    return el ? el.value.trim() : '';
                };

                const payload = {
                    token,
                    first_name: getVal('profFirstName'),
                    last_name: getVal('profLastName'),
                    email: getVal('profEmailInput'),
                    phone: getVal('profPhone'),
                    default_language: getVal('profLanguage') || 'English',
                    direction: getVal('profDirection') || 'System Default',
                    facebook: getVal('profFacebook'),
                    linkedin: getVal('profLinkedin'),
                    skype: getVal('profSkype'),
                    email_signature: document.getElementById('profSignature') ? document.getElementById('profSignature').value : ''
                };
                if (pendingAvatarDataUrl) {
                    payload.avatar = pendingAvatarDataUrl;
                }

                btnSaveProfile.disabled = true;
                btnSaveProfile.textContent = 'Saving...';
                if (editErr) editErr.style.display = 'none';

                try {
                    const res = await fetch('/api/profile', {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload)
                    });
                    const data = await res.json();

                    if (!res.ok) {
                        const errMsg = data.detail || 'Could not save profile changes.';
                        if (editErr) {
                            editErr.textContent = errMsg;
                            editErr.style.display = 'block';
                        }
                        return;
                    }

                    if (data.user) {
                        localStorage.setItem('retail_ai_user', JSON.stringify(data.user));
                        applyUserUI(data.user);
                    }
                    closeEditModal();
                    showToast('Profile details updated and saved.', 'success');
                } catch (err) {
                    if (editErr) {
                        editErr.textContent = `Error saving profile: ${err.message}`;
                        editErr.style.display = 'block';
                    }
                } finally {
                    btnSaveProfile.disabled = false;
                    btnSaveProfile.textContent = 'Save Changes';
                }
            });
        }

        // Save Change Password Popup
        if (btnSavePassword) {
            btnSavePassword.addEventListener('click', async () => {
                const token = localStorage.getItem('retail_ai_token');
                if (!token) {
                    showToast('Please sign in to change your password.', 'error');
                    return;
                }

                const old_password = document.getElementById('profOldPassword') ? document.getElementById('profOldPassword').value : '';
                const new_password = document.getElementById('profNewPassword') ? document.getElementById('profNewPassword').value : '';
                const repeat_password = document.getElementById('profRepeatPassword') ? document.getElementById('profRepeatPassword').value : '';

                if (pwErr) pwErr.style.display = 'none';

                if (!old_password || !new_password || !repeat_password) {
                    if (pwErr) {
                        pwErr.textContent = 'Please fill in Old password, New password, and Repeat New Password.';
                        pwErr.style.display = 'block';
                    }
                    return;
                }
                if (new_password !== repeat_password) {
                    if (pwErr) {
                        pwErr.textContent = 'New password and Repeat New Password do not match.';
                        pwErr.style.display = 'block';
                    }
                    return;
                }

                btnSavePassword.disabled = true;
                btnSavePassword.textContent = 'Updating...';

                try {
                    const res = await fetch('/api/profile/password', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ token, old_password, new_password, repeat_password })
                    });
                    const data = await res.json();

                    if (!res.ok) {
                        if (pwErr) {
                            pwErr.textContent = data.detail || 'Could not update password.';
                            pwErr.style.display = 'block';
                        }
                        return;
                    }

                    closePwModal();
                    showToast('Password updated successfully.', 'success');
                } catch (err) {
                    if (pwErr) {
                        pwErr.textContent = `Error updating password: ${err.message}`;
                        pwErr.style.display = 'block';
                    }
                } finally {
                    btnSavePassword.disabled = false;
                    btnSavePassword.textContent = 'Update Password';
                }
            });
        }
    }

    // ========================================================
    // 7. DASHBOARD DATA LOADERS (KPIs, Charts, Analytics)
    // ========================================================
    async function loadDashboard() {
        // 1. KPIs
        const kpiRes = await fetch('/api/kpis');
        const kpiData = await kpiRes.json();
        
        document.getElementById('kpiRevenue').textContent = `£${kpiData.kpis.total_revenue.toLocaleString()}`;
        document.getElementById('kpiOrders').textContent = kpiData.kpis.total_orders.toLocaleString();
        document.getElementById('kpiCustomers').textContent = kpiData.kpis.total_customers.toLocaleString();
        document.getElementById('kpiProducts').textContent = kpiData.kpis.total_products.toLocaleString();
        document.getElementById('kpiAvgOrder').textContent = `£${kpiData.kpis.avg_order_value.toFixed(2)}`;

        // 2. Monthly Revenue Trend Line Chart
        const mRes = await fetch('/api/charts/monthly-revenue');
        const mData = await mRes.json();
        renderLineChart('chartMonthlyRevenue', mData.map(d => d.YearMonth), mData.map(d => d.Revenue), 'Monthly Revenue (£)', '#FFFFFF');

        // 3. Daily Sales Distribution Line Chart
        const dRes = await fetch('/api/charts/daily-sales');
        const dData = await dRes.json();
        renderLineChart('chartDailySales', dData.map(d => d.Date), dData.map(d => d.Revenue), 'Daily Revenue (£)', '#10A37F');

        // 4. Top 10 Products Bar Chart
        const tpRes = await fetch('/api/charts/top-products');
        const tpData = await tpRes.json();
        renderBarChart('chartTopProducts', tpData.map(d => d.Product.substring(0, 18) + '...'), tpData.map(d => d.Revenue), 'Revenue (£)', '#B4B4B4');

        // 5. Top 10 Customers Bar Chart
        const tcRes = await fetch('/api/charts/top-customers');
        const tcData = await tcRes.json();
        renderBarChart('chartTopCustomers', tcData.map(d => d.Customer), tcData.map(d => d.Revenue), 'Total Spend (£)', '#71717A');
    }

    async function loadAnalytics() {
        // Weekday & Hourly Charts
        const whRes = await fetch('/api/charts/weekday-hour');
        const whData = await whRes.json();
        renderBarChart('chartWeekdayRevenue', whData.weekday.map(d => d.Weekday), whData.weekday.map(d => d.Revenue), 'Revenue (£)', '#FFFFFF');
        renderLineChart('chartHourlyRevenue', whData.hourly.map(d => d.Hour), whData.hourly.map(d => d.Revenue), 'Revenue (£)', '#10A37F');

        // RFM Segment Breakdown
        const segRes = await fetch('/api/segmentation');
        const segData = await segRes.json();
        segData.summary.forEach(s => {
            if (s.Segment === 'VIP Customer') {
                document.getElementById('cntVIP').textContent = s.count.toLocaleString();
                document.getElementById('spendVIP').innerHTML = `Spend: £${s.total_spend.toLocaleString()}<br>Perks & Dedicated Manager`;
            } else if (s.Segment === 'Loyal Customer') {
                document.getElementById('cntLoyal').textContent = s.count.toLocaleString();
                document.getElementById('spendLoyal').innerHTML = `Spend: £${s.total_spend.toLocaleString()}<br>Cross-sell & Points`;
            } else if (s.Segment === 'Regular Customer') {
                document.getElementById('cntRegular').textContent = s.count.toLocaleString();
                document.getElementById('spendRegular').innerHTML = `Spend: £${s.total_spend.toLocaleString()}<br>Re-engagement Offers`;
            } else if (s.Segment === 'At Risk') {
                document.getElementById('cntRisk').textContent = s.count.toLocaleString();
                document.getElementById('spendRisk').innerHTML = `Spend: £${s.total_spend.toLocaleString()}<br>Win-Back Campaigns`;
            }
        });

        // Summary Audit Table
        const sumRes = await fetch('/api/summary');
        const sumData = await sumRes.json();
        const tbody = document.querySelector('#summaryAuditTable tbody');
        if (tbody) {
            tbody.innerHTML = `
                <tr><td>Active Dataset Filename</td><td><strong>${sumData.active_dataset.filename}</strong></td></tr>
                <tr><td>Cleaned Line Items</td><td>${sumData.summary.num_rows.toLocaleString()}</td></tr>
                <tr><td>Catalog SKUs Count</td><td>${sumData.summary.unique_counts.Description ? sumData.summary.unique_counts.Description.toLocaleString() : 'N/A'}</td></tr>
                <tr><td>Unique Customer Accounts</td><td>${sumData.summary.unique_counts.CustomerID ? sumData.summary.unique_counts.CustomerID.toLocaleString() : 'N/A'}</td></tr>
                <tr><td>Data Engine</td><td><span class="pill pill-emerald">Enterprise Analytics Core</span></td></tr>
            `;
        }
    }

    async function loadPrediction() {
        const horizon = document.getElementById('forecastHorizon').value;
        const res = await fetch(`/api/forecast?days=${horizon}`);
        const data = await res.json();

        document.getElementById('rfMAE').textContent = `£${data.metrics.mae.toLocaleString()}`;
        document.getElementById('rfRMSE').textContent = `£${data.metrics.rmse.toLocaleString()}`;
        document.getElementById('rfR2').textContent = data.metrics.r2.toFixed(4);

        const histLabels = data.historical.map(d => d.Date);
        const histData = data.historical.map(d => d.Revenue);
        const futLabels = data.future.map(d => d.Date);
        const futData = data.future.map(d => d.Predicted_Sales);

        renderForecastChart('chartForecast', histLabels, histData, futLabels, futData);
    }

    async function loadCatalogProducts() {
        const res = await fetch('/api/products');
        const data = await res.json();
        const select = document.getElementById('recProductSelect');
        if (select) {
            select.innerHTML = '<option value="">Select a product to view market basket recommendations...</option>';
            data.products.slice(0, 100).forEach(p => {
                const opt = document.createElement('option');
                opt.value = p;
                opt.textContent = p;
                select.appendChild(opt);
            });
        }
    }

    // ========================================================
    // 🤖 8. FLOATING CHATBOT WIDGET (Drawn in Sketch Bottom-Right)
    // ========================================================
    function initEventListeners() {
        // Forecast Horizon Slider
        const horizonSlider = document.getElementById('forecastHorizon');
        if (horizonSlider) {
            horizonSlider.addEventListener('input', () => {
                document.getElementById('daysVal').textContent = horizonSlider.value;
                loadPrediction();
            });
        }

        // SKU Quick Search
        const skuInput = document.getElementById('skuSearchInput');
        if (skuInput) {
            skuInput.addEventListener('input', debounce(async (e) => {
                const q = e.target.value.trim();
                const box = document.getElementById('searchResultsBox');
                if (!q || q.length < 2) {
                    box.style.display = 'none';
                    return;
                }

                const res = await fetch(`/api/search?q=${encodeURIComponent(q)}`);
                const data = await res.json();

                if (data.found) {
                    box.style.display = 'block';
                    document.getElementById('searchProdTitle').textContent = `Search Result: ${data.product}`;
                    document.getElementById('searchRev').textContent = `£${data.total_revenue.toLocaleString()}`;
                    document.getElementById('searchUnits').textContent = data.units_sold.toLocaleString();
                    document.getElementById('searchCust').textContent = data.distinct_customers.toLocaleString();
                    document.getElementById('searchPrice').textContent = `£${data.avg_unit_price.toFixed(2)}`;
                } else {
                    box.style.display = 'none';
                }
            }, 300));
        }

        // Floating Chatbot Widget Toggle
        const floatTrigger = document.getElementById('btnToggleFloatChat');
        const floatWidget = document.getElementById('floatingChatWidget');
        const floatClose = document.getElementById('btnCloseFloatChat');

        if (floatTrigger && floatWidget) {
            floatTrigger.addEventListener('click', () => {
                floatWidget.style.display = floatWidget.style.display === 'none' ? 'flex' : 'none';
            });
            floatClose.addEventListener('click', () => {
                floatWidget.style.display = 'none';
            });

            document.getElementById('btnSendFloatChat').addEventListener('click', () => executeChatQuery('floatChatInput', 'floatChatHistory'));
            document.getElementById('floatChatInput').addEventListener('keypress', (e) => {
                if (e.key === 'Enter') executeChatQuery('floatChatInput', 'floatChatHistory');
            });

            document.querySelectorAll('.float-chip').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    const prompt = e.currentTarget.getAttribute('data-prompt');
                    document.getElementById('floatChatInput').value = prompt;
                    executeChatQuery('floatChatInput', 'floatChatHistory');
                });
            });
        }
    }

    async function executeChatQuery(inputId, historyId) {
        const input = document.getElementById(inputId);
        const q = input.value.trim();
        if (!q) return;

        const history = document.getElementById(historyId);

        // User message
        const userDiv = document.createElement('div');
        userDiv.className = 'chat-msg chat-user';
        userDiv.textContent = q;
        history.appendChild(userDiv);
        input.value = '';
        history.scrollTop = history.scrollHeight;

        // Assistant loading indicator
        const botDiv = document.createElement('div');
        botDiv.className = 'chat-msg chat-assistant';
        botDiv.innerHTML = '<span style="color:var(--text-muted);">Querying dataset index and computing metrics...</span>';
        history.appendChild(botDiv);
        history.scrollTop = history.scrollHeight;

        const userJson = localStorage.getItem('retail_ai_user');
        const currentUser = userJson ? JSON.parse(userJson).username : 'retail_user';

        try {
            const res = await fetch('/api/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({query: q, username: currentUser})
            });
            const data = await res.json();
            
            // Format Markdown text to HTML safely
            let formattedText = formatChatResponse(data.response);
            
            // If cross-sell recommendations returned, embed interactive list
            if (data.recommendations && data.recommendations.length > 0) {
                formattedText += `<br><br><strong style="color:var(--text-primary);">Recommended Cross-Sell Items:</strong><ul style="margin-top:6px; padding-left:18px;">`;
                data.recommendations.forEach(r => {
                    formattedText += `<li style="color:#60A5FA; margin-bottom:4px;"><strong>${r}</strong></li>`;
                });
                formattedText += `</ul>`;
            }

            botDiv.innerHTML = formattedText;
            history.scrollTop = history.scrollHeight;
        } catch (ex) {
            botDiv.innerHTML = `<span style="color:#EF4444;">Error querying assistant: ${ex.message}</span>`;
            history.scrollTop = history.scrollHeight;
        }
    }

    function formatChatResponse(text) {
        if (!text) return '';
        const escaped = text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
        return escaped
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/^- (.*?)(?=\n|$)/gm, '<div style="margin:3px 0 3px 8px;">• $1</div>')
            .replace(/^• (.*?)(?=\n|$)/gm, '<div style="margin:3px 0 3px 8px;">• $1</div>')
            .replace(/\n\n/g, '<br><br>')
            .replace(/\n/g, '<br>');
    }

    // ========================================================
    // 🎨 9. CHART RENDERING HELPERS (Chart.js)
    // ========================================================
    function renderLineChart(canvasId, labels, data, label, color) {
        if (charts[canvasId]) charts[canvasId].destroy();
        const ctx = document.getElementById(canvasId).getContext('2d');
        charts[canvasId] = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: label,
                    data: data,
                    borderColor: color,
                    backgroundColor: color + '22',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.3,
                    pointRadius: 2
                }]
            },
            options: getDarkChartOptions()
        });
    }

    function renderBarChart(canvasId, labels, data, label, color) {
        if (charts[canvasId]) charts[canvasId].destroy();
        const ctx = document.getElementById(canvasId).getContext('2d');
        charts[canvasId] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: label,
                    data: data,
                    backgroundColor: color,
                    borderRadius: 6
                }]
            },
            options: getDarkChartOptions()
        });
    }

    function renderDoughnutChart(canvasId, labels, data) {
        if (charts[canvasId]) charts[canvasId].destroy();
        const ctx = document.getElementById(canvasId).getContext('2d');
        charts[canvasId] = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: ['#10A37F', '#FFFFFF', '#B4B4B4', '#71717A', '#52525B', '#3F3F46', '#27272A', '#D97706', '#EF4444', '#10A37F']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'right', labels: { color: '#B4B4B4' } }
                }
            }
        });
    }

    function renderForecastChart(canvasId, histLabels, histData, futLabels, futData) {
        if (charts[canvasId]) charts[canvasId].destroy();
        const ctx = document.getElementById(canvasId).getContext('2d');

        const combinedLabels = [...histLabels, ...futLabels];
        const histSeries = [...histData, ...Array(futLabels.length).fill(null)];
        const futSeries = [...Array(histLabels.length - 1).fill(null), histData[histData.length - 1], ...futData];

        charts[canvasId] = new Chart(ctx, {
            type: 'line',
            data: {
                labels: combinedLabels,
                datasets: [
                    { label: 'Historical Daily Revenue (£)', data: histSeries, borderColor: '#FFFFFF', borderWidth: 2, fill: false, tension: 0.2 },
                    { label: 'Random Forest Forecast (£)', data: futSeries, borderColor: '#10A37F', borderDash: [5, 5], borderWidth: 3, fill: false, tension: 0.2 }
                ]
            },
            options: getDarkChartOptions()
        });
    }

    function getDarkChartOptions() {
        return {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { labels: { color: '#B4B4B4' } } },
            scales: {
                x: { ticks: { color: '#8E8EA0' }, grid: { color: '#2F2F2F' } },
                y: { ticks: { color: '#8E8EA0' }, grid: { color: '#2F2F2F' } }
            }
        };
    }

    function debounce(func, wait) {
        let timeout;
        return function(...args) {
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(this, args), wait);
        };
    }
});
