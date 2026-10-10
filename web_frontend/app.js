document.addEventListener('DOMContentLoaded', () => {
    // Global Chart Instances Cache
    const charts = {};

    // Initialize Auth & App
    initAuth();
    initNav();
    initUploadHandlers();
    initEventListeners();

    // Toast Notification System
    function showToast(message, type = 'success') {
        const container = document.getElementById('toastContainer');
        const toast = document.createElement('div');
        toast.className = 'toast';
        toast.style.borderColor = type === 'success' ? '#34D399' : '#EF4444';
        toast.innerHTML = message;
        container.appendChild(toast);
        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 300);
        }, 4000);
    }

    // ==========================================
    // 🔐 AUTHENTICATION & LOGIN/REGISTRATION HANDLER
    // ==========================================
    function initAuth() {
        const token = localStorage.getItem('retail_ai_token');
        const userJson = localStorage.getItem('retail_ai_user');

        const loginModal = document.getElementById('loginModal');
        if (!token || !userJson) {
            loginModal.style.display = 'flex';
        } else {
            loginModal.style.display = 'none';
            const user = JSON.parse(userJson);
            document.getElementById('userBadgeName').textContent = `${user.avatar || '🛍️'} ${user.username} (${user.company || 'DMVCORETECH'})`;
            loadDashboard();
            loadCatalogProducts();
            loadDatasetHistory();
            loadDbStatistics();
        }

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

        // Demo Accounts Quick Buttons
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
            document.getElementById('loginModal').style.display = 'flex';
            showToast('👋 Successfully logged out of DMVCORETECH AI Retail Suite.', 'info');
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
            document.getElementById('userBadgeName').textContent = `${data.user.avatar || '🛍️'} ${data.user.username} (${data.user.company || 'DMVCORETECH'})`;
            
            showToast(`Welcome back, ${data.user.full_name || data.user.username}! Signed in to ${data.user.company} Retail Suite.`);
            loadDashboard();
            loadCatalogProducts();
            loadDatasetHistory();
            loadDbStatistics();
        } catch (e) {
            errDiv.textContent = 'Server connection error during login.';
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
                    company: 'DMVCORETECH'
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
            succDiv.textContent = '✅ Account created and persisted in SQLite! Redirecting...';
            succDiv.style.display = 'block';

            setTimeout(() => {
                document.getElementById('loginModal').style.display = 'none';
                document.getElementById('userBadgeName').textContent = `${data.user.avatar || '🛍️'} ${data.user.username} (${data.user.company})`;
                showToast(`🎉 Welcome ${data.user.full_name}! Account created & persisted in SQLite database.`);
                loadDashboard();
                loadCatalogProducts();
                loadDatasetHistory();
                loadDbStatistics();
            }, 800);

        } catch (e) {
            errDiv.textContent = 'Server error during account registration.';
            errDiv.style.display = 'block';
        }
    }

    // ==========================================
    // 🗄️ DATABASE & SYSTEM HEALTH LOADER
    // ==========================================
    async function loadDbStatistics() {
        try {
            const res = await fetch('/api/db/stats');
            if (!res.ok) return;
            const data = await res.json();

            // Header Pill
            const dbBadge = document.getElementById('dbStatusLabel');
            if (dbBadge) {
                dbBadge.textContent = `🟢 SQLite: ${data.database_file} (${data.database_size_kb} KB)`;
            }

            // Tab 8 Cards
            if (document.getElementById('dbSizeKb')) {
                document.getElementById('dbSizeKb').textContent = `${data.database_size_kb} KB`;
                document.getElementById('dbUsersCount').textContent = data.total_registered_users;
                document.getElementById('dbDatasetsCount').textContent = data.total_archived_datasets;
                document.getElementById('dbChatsCount').textContent = data.total_logged_chat_queries;
            }
        } catch (e) {
            console.warn('Error loading DB stats:', e);
        }
    }

    // ==========================================
    // 📜 MULTI-DATASET HISTORY ARCHIVE & SELECTION
    // ==========================================
    async function loadDatasetHistory() {
        const res = await fetch('/api/datasets');
        const data = await res.json();
        const tbody = document.querySelector('#historyTable tbody');
        tbody.innerHTML = '';

        data.datasets.forEach(d => {
            if (d.is_active) {
                document.getElementById('activeDatasetLabel').textContent = `Active: ${d.filename}`;
                if (document.getElementById('chatActiveDatasetPill')) {
                    document.getElementById('chatActiveDatasetPill').textContent = `Dataset: ${d.filename}`;
                }
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
                if (confirm('Are you sure you want to permanently delete this dataset from the SQLite database archive?')) {
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
            loadRFM();
            loadMarketBasket();
            loadCatalogProducts();
            loadPrediction();
            loadDbStatistics();
        }
    }

    async function deleteDataset(dsId) {
        const res = await fetch(`/api/datasets/${dsId}`, {method: 'DELETE'});
        const data = await res.json();
        if (data.success) {
            showToast('🗑️ Dataset removed permanently from SQLite database.', 'info');
            loadDatasetHistory();
            loadDbStatistics();
        }
    }

    // ==========================================
    // 📤 REAL-TIME DATASET UPLOAD HANDLER
    // ==========================================
    function initUploadHandlers() {
        const modal = document.getElementById('uploadModal');
        const btnOpen = document.getElementById('btnOpenUploadModal');
        const btnClose = document.getElementById('btnCloseUploadModal');
        const dropzone = document.getElementById('uploadDropzone');
        const fileInput = document.getElementById('fileInput');
        const statusDiv = document.getElementById('uploadStatus');

        btnOpen.addEventListener('click', () => modal.style.display = 'flex');
        btnClose.addEventListener('click', () => modal.style.display = 'none');

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
            if (e.dataTransfer.files.length > 0) {
                uploadDatasetFile(e.dataTransfer.files[0]);
            }
        });

        fileInput.addEventListener('change', () => {
            if (fileInput.files.length > 0) {
                uploadDatasetFile(fileInput.files[0]);
            }
        });

        async function uploadDatasetFile(file) {
            statusDiv.style.display = 'block';
            statusDiv.innerHTML = '<span style="color:#818CF8;">⏳ Uploading and running real-time customer segmentation & market basket pipeline...</span>';

            const formData = new FormData();
            formData.append('file', file);

            try {
                const res = await fetch('/api/upload', {
                    method: 'POST',
                    body: formData
                });

                if (!res.ok) {
                    const err = await res.json();
                    statusDiv.innerHTML = `<span style="color:#EF4444;">❌ Error: ${err.detail || 'Failed processing dataset.'}</span>`;
                    return;
                }

                const data = await res.json();
                statusDiv.innerHTML = `
                    <span style="color:#34D399;">✅ Dataset Analyzed & Archived Successfully!</span><br>
                    <strong>${data.metadata.cleaned_rows.toLocaleString()} Clean Rows</strong> | Revenue: <strong>£${data.metadata.total_revenue.toLocaleString()}</strong> | Customers: <strong>${data.metadata.total_customers.toLocaleString()}</strong>
                `;

                setTimeout(() => {
                    modal.style.display = 'none';
                    statusDiv.style.display = 'none';
                    
                    showToast(`🎉 Real-Time Analysis Complete for <strong>${file.name}</strong>!<br>Cleaned Rows: ${data.metadata.cleaned_rows.toLocaleString()} | Revenue: £${data.metadata.total_revenue.toLocaleString()}`);

                    // Reload All Visualizations and History Archive
                    loadDatasetHistory();
                    loadDashboard();
                    loadAnalytics();
                    loadRFM();
                    loadMarketBasket();
                    loadCatalogProducts();
                    loadPrediction();
                }, 1200);

            } catch (ex) {
                statusDiv.innerHTML = `<span style="color:#EF4444;">❌ Server upload error: ${ex.message}</span>`;
            }
        }
    }

    // ==========================================
    // 🧭 NAVIGATION TAB SWITCHER
    // ==========================================
    function initNav() {
        const navItems = document.querySelectorAll('.nav-item');
        navItems.forEach(item => {
            item.addEventListener('click', () => {
                const targetTab = item.getAttribute('data-tab');
                
                navItems.forEach(i => i.classList.remove('active'));
                item.classList.add('active');

                document.querySelectorAll('.tab-content').forEach(tab => {
                    tab.classList.remove('active');
                });
                
                const activeTabEl = document.getElementById(`tab-${targetTab}`);
                if (activeTabEl) activeTabEl.classList.add('active');

                // Trigger specific tab loaders
                if (targetTab === 'dashboard') loadDashboard();
                else if (targetTab === 'history') loadDatasetHistory();
                else if (targetTab === 'analytics') loadAnalytics();
                else if (targetTab === 'rfm') loadRFM();
                else if (targetTab === 'basket') loadMarketBasket();
                else if (targetTab === 'prediction') loadPrediction();
                else if (targetTab === 'exports') loadSummaryAudit();
            });
        });

        // Country Filter Listener
        const countrySelect = document.getElementById('countryFilter');
        countrySelect.addEventListener('change', () => {
            loadDashboard();
            if (document.getElementById('tab-analytics').classList.contains('active')) loadAnalytics();
        });
    }

    // ==========================================
    // 🏠 1. DASHBOARD MODULE
    // ==========================================
    async function loadDashboard() {
        const country = document.getElementById('countryFilter').value;
        const qCountry = country !== 'All' ? `?country=${encodeURIComponent(country)}` : '';

        // Fetch KPIs
        const kpiRes = await fetch(`/api/kpis${qCountry}`);
        const kpiData = await kpiRes.json();

        document.getElementById('kpiRevenue').textContent = `£${kpiData.kpis.total_revenue.toLocaleString('en-GB', {maximumFractionDigits: 0})}`;
        document.getElementById('kpiOrders').textContent = kpiData.kpis.total_orders.toLocaleString();
        document.getElementById('kpiCustomers').textContent = kpiData.kpis.total_customers.toLocaleString();
        document.getElementById('kpiProducts').textContent = kpiData.kpis.total_products.toLocaleString();
        document.getElementById('kpiAvgOrder').textContent = `£${kpiData.kpis.avg_order_value.toFixed(2)}`;
        
        document.getElementById('heroCustomers').textContent = `👥 ${kpiData.kpis.total_customers.toLocaleString()} Customers`;
        document.getElementById('activeDatasetLabel').textContent = `Active: ${kpiData.active_dataset.filename}`;

        // Populate Country Filter Options if needed
        const countrySelect = document.getElementById('countryFilter');
        if (countrySelect.options.length <= 1) {
            kpiData.countries.forEach(c => {
                const opt = document.createElement('option');
                opt.value = c;
                opt.textContent = c;
                countrySelect.appendChild(opt);
            });
        }

        // Fetch Monthly Revenue
        const mRes = await fetch(`/api/charts/monthly-revenue${qCountry}`);
        const mData = await mRes.json();
        renderLineChart('chartMonthlyRevenue', mData.map(d => d.YearMonth), mData.map(d => d.Revenue), 'Monthly Revenue (£)', '#818CF8');

        // Fetch Daily Sales
        const dRes = await fetch(`/api/charts/daily-sales${qCountry}`);
        const dData = await dRes.json();
        renderLineChart('chartDailySales', dData.map(d => d.Date), dData.map(d => d.Revenue), 'Daily Sales (£)', '#34D399');

        // Fetch Top Products
        const pRes = await fetch(`/api/charts/top-products${qCountry}`);
        const pData = await pRes.json();
        renderBarChart('chartTopProducts', pData.map(d => d.Product.substring(0, 20) + '...'), pData.map(d => d.Revenue), 'Revenue (£)', '#C084FC');

        // Fetch Top Customers
        const cRes = await fetch(`/api/charts/top-customers${qCountry}`);
        const cData = await cRes.json();
        renderBarChart('chartTopCustomers', cData.map(d => d.Customer), cData.map(d => d.Revenue), 'Revenue (£)', '#F472B6');
    }

    // ==========================================
    // 📈 2. SALES & ANALYTICS MODULE
    // ==========================================
    async function loadAnalytics() {
        const country = document.getElementById('countryFilter').value;
        const qCountry = country !== 'All' ? `?country=${encodeURIComponent(country)}` : '';

        // Country Revenue Pie/Doughnut
        const crRes = await fetch(`/api/charts/country-revenue`);
        const crData = await crRes.json();
        renderDoughnutChart('chartCountryRevenue', crData.map(d => d.Country), crData.map(d => d.Revenue));

        // Weekday & Hourly Sales
        const whRes = await fetch(`/api/charts/weekday-hour`);
        const whData = await whRes.json();
        renderBarChart('chartWeekdayRevenue', whData.weekday.map(d => d.Weekday), whData.weekday.map(d => d.Revenue), 'Revenue (£)', '#FBBF24');
        renderLineChart('chartHourlyRevenue', whData.hourly.map(d => d.Hour), whData.hourly.map(d => d.Revenue), 'Revenue (£)', '#818CF8');

        loadSummaryAudit();
    }

    async function loadSummaryAudit() {
        const res = await fetch('/api/summary');
        const data = await res.json();
        const tbody = document.querySelector('#summaryAuditTable tbody');
        tbody.innerHTML = `
            <tr><td>Active Dataset Filename</td><td><strong>${data.active_dataset.filename}</strong></td></tr>
            <tr><td>Total Clean Line Items</td><td><strong>${data.summary.num_rows.toLocaleString()}</strong></td></tr>
            <tr><td>Total Columns</td><td><strong>${data.summary.num_columns}</strong></td></tr>
            <tr><td>Duplicate Rows Removed</td><td><strong>${data.summary.duplicate_rows.toLocaleString()}</strong></td></tr>
            <tr><td>Unique Invoices</td><td><strong>${(data.summary.unique_counts.InvoiceNo || 0).toLocaleString()}</strong></td></tr>
            <tr><td>Unique Products (SKUs)</td><td><strong>${(data.summary.unique_counts.Description || 0).toLocaleString()}</strong></td></tr>
            <tr><td>Unique Customers</td><td><strong>${(data.summary.unique_counts.CustomerID || 0).toLocaleString()}</strong></td></tr>
            <tr><td>Unique Countries</td><td><strong>${data.summary.unique_counts.Country || 0}</strong></td></tr>
        `;
    }

    // ==========================================
    // 👥 3. CUSTOMER RFM SEGMENTATION MODULE
    // ==========================================
    async function loadRFM() {
        const res = await fetch('/api/segmentation');
        const data = await res.json();

        data.summary.forEach(s => {
            if (s.Segment === 'VIP Customers') {
                document.getElementById('cntVIP').textContent = s.count.toLocaleString();
                document.getElementById('spendVIP').innerHTML = `Spend: £${s.total_spend.toLocaleString()}<br>Strategy: Exclusive Perks & Dedicated Manager`;
            } else if (s.Segment === 'Loyal Customers') {
                document.getElementById('cntLoyal').textContent = s.count.toLocaleString();
                document.getElementById('spendLoyal').innerHTML = `Spend: £${s.total_spend.toLocaleString()}<br>Strategy: Cross-sell & Loyalty Points`;
            } else if (s.Segment === 'Regular Customers') {
                document.getElementById('cntRegular').textContent = s.count.toLocaleString();
                document.getElementById('spendRegular').innerHTML = `Spend: £${s.total_spend.toLocaleString()}<br>Strategy: Re-engagement Discounts`;
            } else if (s.Segment === 'At Risk Customers') {
                document.getElementById('cntRisk').textContent = s.count.toLocaleString();
                document.getElementById('spendRisk').innerHTML = `Spend: £${s.total_spend.toLocaleString()}<br>Strategy: Win-Back Campaigns`;
            }
        });

        renderBarChart('chartSegmentRevenue', data.summary.map(s => s.Segment), data.summary.map(s => s.total_spend), 'Total Spend (£)', '#34D399');

        // Render Plotly 3D Scatter
        const rData = data.sample;
        const colorMap = {'VIP Customers': '#10B981', 'Loyal Customers': '#3B82F6', 'Regular Customers': '#F59E0B', 'At Risk Customers': '#EF4444'};
        
        const traces = [];
        const segments = ['VIP Customers', 'Loyal Customers', 'Regular Customers', 'At Risk Customers'];
        
        segments.forEach(seg => {
            const segPts = rData.filter(d => d.Segment === seg);
            traces.push({
                x: segPts.map(d => d.Recency),
                y: segPts.map(d => d.Frequency),
                z: segPts.map(d => d.Monetary),
                mode: 'markers',
                name: seg,
                marker: { size: 4, color: colorMap[seg] },
                type: 'scatter3d'
            });
        });

        const layout = {
            margin: { l: 0, r: 0, b: 0, t: 0 },
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            font: { family: 'Plus Jakarta Sans', color: '#94A3B8' },
            scene: {
                xaxis: { title: 'Recency' },
                yaxis: { title: 'Frequency' },
                zaxis: { title: 'Monetary' }
            }
        };

        Plotly.newPlot('plotRFM3D', traces, layout, {responsive: true});
    }

    // ==========================================
    // 🛒 4. MARKET BASKET ANALYSIS MODULE
    // ==========================================
    async function loadMarketBasket() {
        const minLift = parseFloat(document.getElementById('liftSlider').value);
        const res = await fetch(`/api/market-basket?min_lift=${minLift}`);
        const data = await res.json();

        document.getElementById('mbTotalRules').textContent = data.stats.total_rules.toLocaleString();
        document.getElementById('mbFilteredRules').textContent = data.stats.filtered_rules.toLocaleString();
        document.getElementById('mbMaxLift').textContent = data.stats.max_lift.toFixed(2);
        document.getElementById('mbMaxConf').textContent = `${data.stats.max_confidence.toFixed(1)}%`;
        
        document.getElementById('heroRules').textContent = `🛒 ${data.stats.total_rules.toLocaleString()} Rules`;

        const tbody = document.querySelector('#rulesTable tbody');
        tbody.innerHTML = '';
        data.rules.forEach(r => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><strong>${r.antecedents}</strong></td>
                <td><span style="color:#818CF8;">${r.consequents}</span></td>
                <td>${r.support}%</td>
                <td>${r.confidence}%</td>
                <td><span class="pill pill-emerald">Lift ${r.lift}</span></td>
            `;
            tbody.appendChild(tr);
        });
    }

    // ==========================================
    // 🤖 5. PRODUCT RECOMMENDER MODULE
    // ==========================================
    async function loadCatalogProducts() {
        const res = await fetch('/api/products');
        const data = await res.json();
        const select = document.getElementById('recProductSelect');
        select.innerHTML = '<option value="">Select Target Catalog Product...</option>';
        data.products.forEach(p => {
            const opt = document.createElement('option');
            opt.value = p;
            opt.textContent = p;
            select.appendChild(opt);
        });
    }

    // ==========================================
    // 📊 6. SALES PREDICTION MODULE
    // ==========================================
    async function loadPrediction() {
        const days = parseInt(document.getElementById('forecastHorizon').value);
        const res = await fetch(`/api/forecast?days=${days}`);
        const data = await res.json();

        document.getElementById('rfMAE').textContent = `£${data.metrics.mae.toLocaleString()}`;
        document.getElementById('rfRMSE').textContent = `£${data.metrics.rmse.toLocaleString()}`;
        document.getElementById('rfR2').textContent = data.metrics.r2.toFixed(4);

        const histDates = data.historical.map(d => d.Date);
        const histRev = data.historical.map(d => d.Revenue);
        const futDates = data.future.map(d => d.Date);
        const futRev = data.future.map(d => d.Predicted_Sales);

        renderForecastChart('chartForecast', histDates, histRev, futDates, futRev);
    }

    // ==========================================
    // ⚙️ EVENT LISTENERS & HANDLERS
    // ==========================================
    function initEventListeners() {
        // Minimum Lift Slider
        const liftSlider = document.getElementById('liftSlider');
        liftSlider.addEventListener('input', () => {
            document.getElementById('liftVal').textContent = liftSlider.value;
            loadMarketBasket();
        });

        // Forecast Horizon Slider
        const horizonSlider = document.getElementById('forecastHorizon');
        horizonSlider.addEventListener('input', () => {
            document.getElementById('daysVal').textContent = horizonSlider.value;
            loadPrediction();
        });

        // Get Recommendations Button
        document.getElementById('btnGetRecs').addEventListener('click', async () => {
            const prod = document.getElementById('recProductSelect').value;
            if (!prod) return alert('Please select a catalog product.');

            const res = await fetch(`/api/recommend?product=${encodeURIComponent(prod)}`);
            const data = await res.json();

            const grid = document.getElementById('recsGrid');
            grid.innerHTML = '';
            document.getElementById('recsResultsBox').style.display = 'block';

            data.recommendations.forEach((r, idx) => {
                const card = document.createElement('div');
                card.className = 'prod-card';
                card.innerHTML = `
                    <div class="rank">Recommendation #${idx+1}</div>
                    <div class="title">${r}</div>
                    <div class="badge">${data.is_fallback ? '🔥 Catalog Bestseller' : '✔ High Lift Co-Purchase'}</div>
                `;
                grid.appendChild(card);
            });
        });

        // Customer Lookup
        document.getElementById('btnLookupCust').addEventListener('click', async () => {
            const cid = document.getElementById('lookupCustInput').value.trim();
            if (!cid) return;

            const res = await fetch(`/api/segmentation/customer/${cid}`);
            const div = document.getElementById('custLookupResult');
            div.style.display = 'block';

            if (res.status === 404) {
                div.innerHTML = `<span style="color:#EF4444;">❌ Customer ID #${cid} not found in database.</span>`;
            } else {
                const data = await res.json();
                div.innerHTML = `
                    <strong style="color:#818CF8;">Customer #${data.CustomerID} Account Details:</strong><br>
                    Segment: <span class="pill pill-emerald">${data.Segment}</span><br>
                    Recency: <strong>${data.Recency} Days</strong> | Frequency: <strong>${data.Frequency} Orders</strong> | Monetary Spend: <strong>£${data.Monetary.toLocaleString()}</strong>
                `;
            }
        });

        // SKU Quick Search
        document.getElementById('skuSearchInput').addEventListener('input', debounce(async (e) => {
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

        // RAG Chatbot Tab Listeners
        document.getElementById('btnSendChat').addEventListener('click', () => executeChatQuery('chatInput', 'chatHistory'));
        document.getElementById('chatInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') executeChatQuery('chatInput', 'chatHistory');
        });

        // Chat Suggestion Chips (Tab 7)
        document.querySelectorAll('.chip-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const prompt = e.target.getAttribute('data-prompt');
                document.getElementById('chatInput').value = prompt;
                executeChatQuery('chatInput', 'chatHistory');
            });
        });

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
                    const prompt = e.target.getAttribute('data-prompt');
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
        botDiv.innerHTML = '<span style="color:#818CF8;">⏳ Searching active dataset FAISS vector index & analyzing query...</span>';
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
            
            // If cross-sell recommendations returned, embed interactive cards
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
        let html = text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/• (.*?)(?=\n|$)/g, '<li style="margin-left:14px;">$1</li>')
            .replace(/\n\n/g, '<br><br>')
            .replace(/\n/g, '<br>');
        return html;
    }

    // ==========================================
    // 🎨 CHART RENDER HELPER FUNCTIONS (Chart.js)
    // ==========================================
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
