const API_BASE = '/api/integration';

function selectPlatform(platform) {
    // Only Shopify supported
    if (platform !== 'shopify') return;

    // UI Update
    document.querySelectorAll('.platform-card').forEach(el => el.classList.remove('active', 'border-green-500', 'bg-green-50'));
    document.getElementById(`card-${platform}`).classList.add('active', 'border-green-500');
}

async function testConnection() {
    const btn = document.querySelector('button[onclick="testConnection()"]');
    const originalText = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> Testing...';
    btn.disabled = true;

    const statusDiv = document.getElementById('connection-status');
    statusDiv.classList.add('hidden');

    try {
        const clientId = document.getElementById('client_id').value;
        const storeUrl = document.getElementById('store_url').value;
        const accessToken = document.getElementById('access_token').value;
        const webhookSecret = document.getElementById('webhook_secret').value;

        if (!storeUrl || !accessToken) {
            throw new Error("Please enter Store URL and Access Token.");
        }

        const response = await fetch(`${API_BASE}/test-connection`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                platform: 'shopify',
                client_id: clientId,
                store_url: storeUrl,
                access_token: accessToken,
                webhook_secret: webhookSecret
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Connection failed');
        }

        // Success
        showStatus('success', 'Success!', data.details || 'Connected successfully.');
        document.getElementById('action-section').classList.remove('hidden');

        // Scroll to action section
        setTimeout(() => {
            document.getElementById('action-section').scrollIntoView({ behavior: 'smooth' });
        }, 500);

    } catch (error) {
        showStatus('error', 'Connection Failed', error.message);
        document.getElementById('action-section').classList.add('hidden');
    } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
}

async function triggerBulkSync() {
    const btn = document.getElementById('btn-sync');
    const originalText = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> Starting...';
    btn.disabled = true;

    const syncStatus = document.getElementById('sync-status');
    syncStatus.classList.remove('hidden');

    try {
        const clientId = document.getElementById('client_id').value;
        const storeUrl = document.getElementById('store_url').value;
        const accessToken = document.getElementById('access_token').value;
        const webhookSecret = document.getElementById('webhook_secret').value;

        const response = await fetch(`${API_BASE}/bulk-sync`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                platform: 'shopify',
                client_id: clientId,
                store_url: storeUrl,
                access_token: accessToken,
                webhook_secret: webhookSecret
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Sync failed start');
        }

        // Changed to info state
        btn.className = "w-full flex justify-center py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-blue-700 bg-blue-100 cursor-default";
        btn.innerHTML = '<i class="fas fa-check mr-2"></i> Sync Started';

        syncStatus.innerHTML = '<i class="fas fa-info-circle text-blue-500 mr-2"></i> The process is running in the background. You can close this window.';

    } catch (error) {
        alert("Failed to start sync: " + error.message);
        btn.innerHTML = originalText;
        btn.disabled = false;
        syncStatus.classList.add('hidden');
    }
}

function showStatus(type, title, message) {
    const div = document.getElementById('connection-status');
    const icon = document.getElementById('status-icon');
    const titleEl = document.getElementById('status-title');
    const msgEl = document.getElementById('status-message');

    div.classList.remove('hidden', 'bg-green-50', 'text-green-800', 'bg-red-50', 'text-red-800');
    icon.className = '';

    if (type === 'success') {
        div.classList.add('bg-green-50', 'text-green-800');
        icon.className = 'fas fa-check-circle text-green-400 text-xl';
    } else {
        div.classList.add('bg-red-50', 'text-red-800');
        icon.className = 'fas fa-times-circle text-red-400 text-xl';
    }

    titleEl.innerText = title;
    msgEl.innerText = message;
    div.classList.remove('hidden');
}
