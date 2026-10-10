document.addEventListener('DOMContentLoaded', () => {
    // Global Chart Instances Cache
    const charts = {};

    // Initialize View Navigation & App
    initViewRouter();
    initAuth();
    initDashboardNav();
    initUploadHandlers();
    initEventListeners();

    // Toast Notification System
    function showToast(message, type = 'success') {
        const container = document.getElementById('toastContainer');
        const toast = document.createElement('div');
        toast.className = 'toast';
        toast.style.borderColor = type === 'success' ? '#34D399' : (type === 'info' ? '#818CF8' : '#EF4444');
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
        showToast(`✅ Thank you ${name}! Your inquiry has been submitted to support.`);
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

    function showDashboard() {
        document.getElementById('homePageSection').style.display = 'none';
        document.getElementById('dashboardSection').style.display = 'block';

        const userJson = localStorage.getItem('retail_ai_user');
        if (userJson) {
            const user = JSON.parse(userJson);
            const badge = document.getElementById('userBadgeName');
            if (badge) badge.textContent = `${user.avatar || '🛍️'} ${user.username} (${user.company || 'Enterprise Suite'})`;

            // Update Profile Tab Details
            if (document.getElementById('profFullName')) {
                document.getElementById('profFullName').textContent = user.full_name || user.username;
                document.getElementById('profRole').textContent = user.role || 'Retail Store Manager';
                document.getElementById('profCompany').textContent = user.company || 'Enterprise Suite';
                document.getElementById('profEmail').textContent = user.email || 'user@retail-ai.com';
                document.getElementById('profAvatar').textContent = user.avatar || '🛍️';
            }
        }

        // Initialize Lucide icons
        if (window.lucide) lucide.createIcons();

        // Load Dashboard Data
        loadDashboard();
        loadCatalogProducts();
        loadDatasetHistory();
        loadDbStatistics();
    }

    // ========================================================
    // 🔐 2. AUTHENTICATION & REGISTRATION
    // ========================================================
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
            });

            tabBtnRegister.addEventListener('click', () => {
                tabBtnRegister.classList.add('active');
                tabBtnSignIn.classList.remove('active');
                signInPanel.style.display = 'none';
                registerPanel.style.display = 'block';
                errDiv.style.display = 'none';
                succDiv.style.display = 'none';
            });
        }

        // Login Action
        document.getElementById('btnLogin').addEventListener('click', performLogin);

        // Register Action
        const btnRegister = document.getElementById('btnRegister');
        if (btnRegister) {
            btnRegister.addEventListener('click', performRegister);
        }

        // Demo Quick Accounts
        document.querySelectorAll('.btn-demo-quick').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const u = e.currentTarget.getAttribute('data-user');
                const p = e.currentTarget.getAttribute('data-pass');
                document.getElementById('loginUser').value = u;
                document.getElementById('loginPass').value = p;
                performLogin();
            });
        });

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
            showToast('👋 Successfully logged out of Retail AI Suite.', 'info');
            showHomePage();
        });
    }

    async function performLogin() {
        const username = document.getElementById('loginUser').value.trim();
        const password = document.getElementById('loginPass').value.trim();
        const errDiv = document.getElementById('loginError');

        if (!username || !password) {
            errDiv.textContent = 'Please enter both username and password.';
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
        const role = document.getElementById('regRole').value;
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
                    company: 'Enterprise Retail'
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
            succDiv.textContent = '✅ Account created! Launching Dashboard...';
            succDiv.style.display = 'block';

            setTimeout(() => {
                document.getElementById('loginModal').style.display = 'none';
                showToast(`🎉 Welcome ${data.user.full_name}! Account created successfully.`);
                showDashboard();
            }, 800);

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
                dbBadge.textContent = '🟢 AI Engine Active';
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
                
                // If clicked "Upload data" item, open upload modal
                if (item.id === 'navItemUploadData') {
                    document.getElementById('uploadModal').style.display = 'flex';
                    return;
                }

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
                if (targetTab === 'profile') loadDbStatistics();
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
                document.getElementById('activeDatasetLabel').textContent = `Active: ${d.filename}`;
                if (document.getElementById('floatChatDatasetPill')) {
                    document.getElementById('floatChatDatasetPill').textContent = `QA: ${d.filename}`;
                }
            }

            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${d.is_active ? '<span class="pill pill-emerald">🟢 Active</span>' : '<span class="pill pill-indigo">Archived</span>'}</td>
                <td><strong>${d.filename}</strong></td>
                <td>${d.upload_time}</td>
                <td>${d.cleaned_rows.toLocaleString()}</td>
                <td><strong>£${d.total_revenue.toLocaleString()}</strong></td>
                <td>${d.total_customers.toLocaleString()}</td>
                <td>${d.total_products.toLocaleString()}</td>
                <td>
                    ${d.is_active ? 
                        '<span style="color:#34D399; font-weight:700;">Currently Analyzing</span>' : 
                        `<div style="display:flex; gap:6px;">
                            <button class="btn-secondary btn-select-ds" data-id="${d.dataset_id}" style="padding:6px 10px;">⚡ Select</button>
                            ${!d.is_default ? `<button class="btn-secondary btn-delete-ds" data-id="${d.dataset_id}" style="padding:6px 10px; border-color:#EF4444; color:#F87171;">🗑️</button>` : ''}
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
            showToast(`🔄 Active dataset switched to: <strong>${data.metadata.filename}</strong>`);
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
            showToast('🗑️ Dataset removed permanently.', 'info');
            loadDatasetHistory();
            loadDbStatistics();
        }
    }

    // ========================================================
    // 📤 6. REAL-TIME DATASET UPLOAD
    // ========================================================
    function initUploadHandlers() {
        const modal = document.getElementById('uploadModal');
        const btnClose = document.getElementById('btnCloseUploadModal');
        const dropzone = document.getElementById('uploadDropzone');
        const fileInput = document.getElementById('fileInput');
        const statusDiv = document.getElementById('uploadStatus');

        if (btnClose) btnClose.addEventListener('click', () => modal.style.display = 'none');
        if (dropzone) {
            dropzone.addEventListener('click', () => fileInput.click());
            dropzone.addEventListener('dragover', (e) => {
                e.preventDefault();
                dropzone.style.background = 'rgba(99, 102, 241, 0.2)';
            });
            dropzone.addEventListener('dragleave', () => {
                dropzone.style.background = 'rgba(99, 102, 241, 0.05)';
            });
            dropzone.addEventListener('drop', (e) => {
                e.preventDefault();
                dropzone.style.background = 'rgba(99, 102, 241, 0.05)';
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
            statusDiv.innerHTML = '<span style="color:#818CF8;">⏳ Processing dataset & analyzing retail metrics...</span>';

            const formData = new FormData();
            formData.append('file', file);

            try {
                const res = await fetch('/api/upload', {
                    method: 'POST',
                    body: formData
                });

                if (!res.ok) {
                    const err = await res.json();
                    statusDiv.innerHTML = `<span style="color:#EF4444;">❌ Error: ${err.detail || 'Upload failed.'}</span>`;
                    return;
                }

                const data = await res.json();
                statusDiv.innerHTML = `
                    <span style="color:#34D399;">✅ Dataset Analyzed & Saved to Archive!</span><br>
                    <strong>${data.metadata.cleaned_rows.toLocaleString()} Clean Rows</strong> | Revenue: <strong>£${data.metadata.total_revenue.toLocaleString()}</strong>
                `;

                setTimeout(() => {
                    modal.style.display = 'none';
                    statusDiv.style.display = 'none';
                    showToast(`🎉 Analysis Ready for <strong>${file.name}</strong>!<br>Cleaned Rows: ${data.metadata.cleaned_rows.toLocaleString()}`);

                    loadDatasetHistory();
                    loadDashboard();
                    loadAnalytics();
                    loadCatalogProducts();
                    loadPrediction();
                    loadDbStatistics();
                }, 1200);

            } catch (ex) {
                statusDiv.innerHTML = `<span style="color:#EF4444;">❌ Server upload error: ${ex.message}</span>`;
            }
        }
    }

    // ========================================================
    // 📊 7. DASHBOARD DATA LOADERS (KPIs, Charts, Analytics)
    // ========================================================
    async function loadDashboard() {
        const country = document.getElementById('countryFilter').value;
        const urlParam = country !== 'All' ? `?country=${encodeURIComponent(country)}` : '';

        // 1. KPIs
        const kpiRes = await fetch(`/api/kpis${urlParam}`);
        const kpiData = await kpiRes.json();
        
        document.getElementById('kpiRevenue').textContent = `£${kpiData.kpis.total_revenue.toLocaleString()}`;
        document.getElementById('kpiOrders').textContent = kpiData.kpis.total_orders.toLocaleString();
        document.getElementById('kpiCustomers').textContent = kpiData.kpis.total_customers.toLocaleString();
        document.getElementById('kpiProducts').textContent = kpiData.kpis.total_products.toLocaleString();
        document.getElementById('kpiAvgOrder').textContent = `£${kpiData.kpis.avg_order_value.toFixed(2)}`;

        // Populate Country Filter Options if only 1 option
        const select = document.getElementById('countryFilter');
        if (select.children.length <= 1 && kpiData.countries) {
            select.innerHTML = '';
            kpiData.countries.forEach(c => {
                const opt = document.createElement('option');
                opt.value = c;
                opt.textContent = c === 'All' ? '🌍 All Countries' : c;
                select.appendChild(opt);
            });
            select.value = country;
        }

        // 2. Monthly Revenue Trend Line Chart
        const mRes = await fetch(`/api/charts/monthly-revenue${urlParam}`);
        const mData = await mRes.json();
        renderLineChart('chartMonthlyRevenue', mData.map(d => d.YearMonth), mData.map(d => d.Revenue), 'Monthly Revenue (£)', '#818CF8');

        // 3. Daily Sales Distribution Line Chart
        const dRes = await fetch(`/api/charts/daily-sales${urlParam}`);
        const dData = await dRes.json();
        renderLineChart('chartDailySales', dData.map(d => d.Date), dData.map(d => d.Revenue), 'Daily Revenue (£)', '#34D399');

        // 4. Top 10 Products Bar Chart
        const tpRes = await fetch(`/api/charts/top-products${urlParam}`);
        const tpData = await tpRes.json();
        renderBarChart('chartTopProducts', tpData.map(d => d.Product.substring(0, 18) + '...'), tpData.map(d => d.Revenue), 'Revenue (£)', '#F472B6');

        // 5. Top 10 Customers Bar Chart
        const tcRes = await fetch(`/api/charts/top-customers${urlParam}`);
        const tcData = await tcRes.json();
        renderBarChart('chartTopCustomers', tcData.map(d => d.Customer), tcData.map(d => d.Revenue), 'Total Spend (£)', '#FBBF24');
    }

    async function loadAnalytics() {
        // Country Revenue Doughnut Chart
        const cRes = await fetch('/api/charts/country-revenue');
        const cData = await cRes.json();
        renderDoughnutChart('chartCountryRevenue', cData.map(d => d.Country), cData.map(d => d.Revenue));

        // Weekday & Hourly Charts
        const whRes = await fetch('/api/charts/weekday-hour');
        const whData = await whRes.json();
        renderBarChart('chartWeekdayRevenue', whData.weekday.map(d => d.Weekday), whData.weekday.map(d => d.Revenue), 'Revenue (£)', '#C084FC');
        renderLineChart('chartHourlyRevenue', whData.hourly.map(d => d.Hour), whData.hourly.map(d => d.Revenue), 'Revenue (£)', '#38BDF8');

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
        // Country Filter Listener
        const countryFilter = document.getElementById('countryFilter');
        if (countryFilter) {
            countryFilter.addEventListener('change', () => loadDashboard());
        }

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
                    document.getElementById('searchProdTitle').textContent = `🔍 Instant Search Result: ${data.product}`;
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
        botDiv.innerHTML = '<span style="color:#818CF8;">⏳ Querying AI dataset index & analyzing metrics...</span>';
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
                formattedText += `<br><br><strong style="color:#818CF8;">💡 Top Co-Purchased Cross-Sell Recommendations:</strong><ul style="margin-top:6px; padding-left:18px;">`;
                data.recommendations.forEach(r => {
                    formattedText += `<li style="color:#34D399; margin-bottom:4px;"><strong>${r}</strong></li>`;
                });
                formattedText += `</ul>`;
            }

            botDiv.innerHTML = formattedText;
            history.scrollTop = history.scrollHeight;
        } catch (ex) {
            botDiv.innerHTML = `<span style="color:#EF4444;">❌ Error querying AI Assistant: ${ex.message}</span>`;
            history.scrollTop = history.scrollHeight;
        }
    }

    function formatChatResponse(text) {
        if (!text) return '';
        return text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/• (.*?)(?=\n|$)/g, '<li style="margin-left:14px;">$1</li>')
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
                    backgroundColor: ['#818CF8', '#34D399', '#F472B6', '#FBBF24', '#C084FC', '#3B82F6', '#EF4444', '#10B981', '#6366F1', '#A78BFA']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'right', labels: { color: '#94A3B8' } }
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
                    { label: 'Historical Daily Revenue (£)', data: histSeries, borderColor: '#818CF8', borderWidth: 2, fill: false, tension: 0.2 },
                    { label: 'Random Forest Forecast (£)', data: futSeries, borderColor: '#34D399', borderDash: [5, 5], borderWidth: 3, fill: false, tension: 0.2 }
                ]
            },
            options: getDarkChartOptions()
        });
    }

    function getDarkChartOptions() {
        return {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { labels: { color: '#94A3B8' } } },
            scales: {
                x: { ticks: { color: '#94A3B8' }, grid: { color: 'rgba(255,255,255,0.05)' } },
                y: { ticks: { color: '#94A3B8' }, grid: { color: 'rgba(255,255,255,0.05)' } }
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
