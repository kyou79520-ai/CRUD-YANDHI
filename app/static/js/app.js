// ========== CONFIGURACIÓN ==========
const API_URL = '/api';
let TOKEN = localStorage.getItem('token');
let CURRENT_USER = (() => {
    try {
        const userData = localStorage.getItem('user');
        return userData ? JSON.parse(userData) : {};
    } catch (e) {
        console.error('Error parsing user data:', e);
        return {};
    }
})();
let CART = [];
let SUPPLIERS = [];

// ========== UTILIDADES ==========
function showScreen(screenId) {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    document.getElementById(screenId).classList.add('active');
}

function showSection(sectionId) {
    document.querySelectorAll('.content-section').forEach(s => s.classList.remove('active'));
    document.getElementById(sectionId + '-section').classList.add('active');
    document.querySelectorAll('.menu-item').forEach(m => m.classList.remove('active'));
    document.querySelector(`[data-section="${sectionId}"]`).classList.add('active');
}

function showError(elementId, message) {
    const el = document.getElementById(elementId);
    if (el) {
        el.textContent = message;
        el.style.display = 'block';
        setTimeout(() => el.style.display = 'none', 5000);
    }
}

function showModal(title, bodyHTML, onSubmit) {
    const modal = document.getElementById('modal');
    document.getElementById('modal-title').textContent = title;
    document.getElementById('modal-body').innerHTML = bodyHTML;
    modal.classList.add('active');
    
    const form = document.getElementById('modal-form');
    form.onsubmit = async (e) => {
        e.preventDefault();
        await onSubmit(new FormData(form));
        modal.classList.remove('active');
        form.reset();
    };
}

function closeModal() {
    document.getElementById('modal').classList.remove('active');
}

async function apiRequest(endpoint, method = 'GET', body = null) {
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json',
        }
    };
    
    const currentToken = localStorage.getItem('token');
    
    if (currentToken) {
        options.headers['Authorization'] = `Bearer ${currentToken}`;
    }
    
    if (body) {
        options.body = JSON.stringify(body);
    }
    
    try {
        const response = await fetch(API_URL + endpoint, options);
        
        if (response.status === 401) {
            localStorage.clear();
            TOKEN = null;
            CURRENT_USER = {};
            showScreen('login-screen');
            throw new Error('Sesión expirada. Por favor inicia sesión nuevamente.');
        }
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.msg || 'Error en la petición');
        }
        
        return data;
    } catch (error) {
        console.error('API Error:', error);
        if (error.message !== 'Sesión expirada. Por favor inicia sesión nuevamente.') {
            alert('Error: ' + error.message);
        }
        throw error;
    }
}

// ========== LOGIN ==========
document.getElementById('login-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    
    try {
        const data = await apiRequest('/auth/login', 'POST', { username, password });
        
        if (!data.access_token || !data.user) {
            throw new Error('Respuesta inválida del servidor');
        }
        
        TOKEN = data.access_token;
        CURRENT_USER = data.user;
        
        localStorage.setItem('token', TOKEN);
        localStorage.setItem('user', JSON.stringify(CURRENT_USER));
        
        document.getElementById('user-info').textContent = `👤 ${CURRENT_USER.username} (${CURRENT_USER.role})`;
        document.body.className = `role-${CURRENT_USER.role}`;
        
        showScreen('main-screen');
        loadDashboard();
    } catch (error) {
        console.error('Login error:', error);
        showError('login-error', error.message || 'Usuario o contraseña incorrectos');
    }
});

// ========== LOGOUT ==========
document.getElementById('logout-btn').addEventListener('click', () => {
    TOKEN = null;
    CURRENT_USER = {};
    CART = [];
    localStorage.clear();
    showScreen('login-screen');
    document.getElementById('login-form').reset();
});

// ========== MENU NAVIGATION ==========
document.querySelectorAll('.menu-item').forEach(item => {
    item.addEventListener('click', () => {
        const section = item.dataset.section;
        showSection(section);
        
        switch(section) {
            case 'dashboard':
                loadDashboard();
                break;
            case 'sales':
                loadSalesPage();
                break;
            case 'sales-history':
                loadSalesHistory();
                break;
            case 'products':
                loadProducts();
                break;
            case 'suppliers':
                loadSuppliers();
                break;
            case 'customers':
                loadCustomers();
                break;
            case 'users':
                loadUsers();
                break;
            case 'logs':
                loadLogs();
                break;
        }
    });
});

// ========== DASHBOARD ==========
async function loadDashboard() {
    try {
        const data = await apiRequest('/dashboard');
        const products = await apiRequest('/products');
        
        document.getElementById('total-sales').textContent = `$${data.total_sales.toFixed(2)}`;
        document.getElementById('total-products').textContent = data.total_products;
        document.getElementById('total-customers').textContent = data.total_customers;
        document.getElementById('total-suppliers').textContent = data.total_suppliers || 0;
        
        // Mostrar alerta de productos con stock bajo
        const lowStockProducts = products.filter(p => p.is_low_stock);
        const lowStockAlert = document.getElementById('low-stock-alert');
        const lowStockList = document.getElementById('low-stock-list');
        
        if (lowStockProducts.length > 0) {
            lowStockAlert.style.display = 'block';
            lowStockList.innerHTML = lowStockProducts.map(p => `
                <div style="padding: 8px; border-bottom: 1px solid #ffc107;">
                    <strong>${p.name}</strong> - Stock actual: <span style="color: #dc3545; font-weight: bold;">${p.stock}</span> 
                    (Mínimo: ${p.min_stock}) - Proveedor: ${p.supplier_name || 'Sin proveedor'}
                </div>
            `).join('');
        } else {
            lowStockAlert.style.display = 'none';
        }
        
        const recentSalesList = document.getElementById('recent-sales-list');
        recentSalesList.innerHTML = data.recent_sales.map(sale => `
            <div style="padding: 10px; border-bottom: 1px solid #e0e0e0;">
                <strong>Venta #${sale.id}</strong> - $${sale.total.toFixed(2)} 
                <small>(${new Date(sale.created_at).toLocaleString()})</small>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading dashboard:', error);
    }
}

// ========== SALES PAGE ==========
async function loadSalesPage() {
    try {
        const products = await apiRequest('/products');
        const productsGrid = document.getElementById('products-grid');
        productsGrid.innerHTML = products.map(p => {
            const lowStockClass = p.is_low_stock ? 'style="border-color: #dc3545;"' : '';
            const lowStockBadge = p.is_low_stock ? '<span style="color: #dc3545; font-size: 11px;">⚠️ Stock Bajo</span>' : '';
            return `
                <div class="product-card" ${lowStockClass} onclick="addToCart(${p.id}, '${p.name.replace(/'/g, "\\'")}', ${p.price}, ${p.stock})">
                    <h4>${p.name}</h4>
                    <p class="price">$${p.price.toFixed(2)}</p>
                    <p class="stock">Stock: ${p.stock}</p>
                    ${lowStockBadge}
                </div>
            `;
        }).join('');
        
        const customers = await apiRequest('/customers');
        const customerSelect = document.getElementById('cart-customer');
        customerSelect.innerHTML = '<option value="">Sin cliente</option>' + 
            customers.map(c => `<option value="${c.id}">${c.name}</option>`).join('');
        
        document.getElementById('search-product').addEventListener('input', (e) => {
            const search = e.target.value.toLowerCase();
            document.querySelectorAll('.product-card').forEach(card => {
                const name = card.querySelector('h4').textContent.toLowerCase();
                card.style.display = name.includes(search) ? 'block' : 'none';
            });
        });
        
        updateCartDisplay();
    } catch (error) {
        console.error('Error loading sales page:', error);
    }
}

function addToCart(productId, name, price, stock) {
    const existing = CART.find(item => item.productId === productId);
    
    if (existing) {
        if (existing.quantity < stock) {
            existing.quantity++;
        } else {
            alert('No hay suficiente stock');
            return;
        }
    } else {
        CART.push({ productId, name, price, quantity: 1, stock });
    }
    
    updateCartDisplay();
}

function updateCartDisplay() {
    const cartItems = document.getElementById('cart-items');
    const cartTotal = document.getElementById('cart-total');
    
    if (CART.length === 0) {
        cartItems.innerHTML = '<p style="text-align: center; color: #999;">Carrito vacío</p>';
        cartTotal.textContent = '0.00';
        return;
    }
    
    cartItems.innerHTML = CART.map((item, index) => `
        <div class="cart-item">
            <div class="cart-item-info">
                <h4>${item.name}</h4>
                <p>$${item.price.toFixed(2)} c/u</p>
            </div>
            <div class="cart-item-qty">
                <button onclick="updateCartQty(${index}, -1)">-</button>
                <span>${item.quantity}</span>
                <button onclick="updateCartQty(${index}, 1)">+</button>
                <button class="cart-item-remove" onclick="removeFromCart(${index})">🗑️</button>
            </div>
        </div>
    `).join('');
    
    const total = CART.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    cartTotal.textContent = total.toFixed(2);
}

function updateCartQty(index, change) {
    const item = CART[index];
    const newQty = item.quantity + change;
    
    if (newQty <= 0) {
        removeFromCart(index);
    } else if (newQty <= item.stock) {
        item.quantity = newQty;
        updateCartDisplay();
    } else {
        alert('No hay suficiente stock');
    }
}

function removeFromCart(index) {
    CART.splice(index, 1);
    updateCartDisplay();
}

document.getElementById('clear-cart-btn').addEventListener('click', () => {
    CART = [];
    updateCartDisplay();
});

document.getElementById('complete-sale-btn').addEventListener('click', async () => {
    if (CART.length === 0) {
        alert('El carrito está vacío');
        return;
    }
    
    const customerId = document.getElementById('cart-customer').value || null;
    const paymentMethod = document.getElementById('payment-method').value;
    
    const saleData = {
        customer_id: customerId ? parseInt(customerId) : null,
        payment_method: paymentMethod,
        items: CART.map(item => ({
            product_id: item.productId,
            quantity: item.quantity
        }))
    };
    
    try {
        const result = await apiRequest('/sales', 'POST', saleData);
        alert(`✅ Venta completada! Total: $${result.total.toFixed(2)}`);
        CART = [];
        updateCartDisplay();
        loadSalesPage();
    } catch (error) {
        alert('Error al completar la venta: ' + error.message);
    }
});

// ========== SALES HISTORY ==========
async function loadSalesHistory() {
    try {
        const sales = await apiRequest('/sales');
        const salesList = document.getElementById('sales-history-list');
        
        salesList.innerHTML = `
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Cliente</th>
                            <th>Vendedor</th>
                            <th>Total</th>
                            <th>Pago</th>
                            <th>Fecha</th>
                            <th>Acciones</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${sales.map(s => `
                            <tr>
                                <td>#${s.id}</td>
                                <td>${s.customer || 'N/A'}</td>
                                <td>${s.user}</td>
                                <td>$${s.total.toFixed(2)}</td>
                                <td>${s.payment_method}</td>
                                <td>${new Date(s.created_at).toLocaleString()}</td>
                                <td class="actions">
                                    <button class="btn btn-small btn-primary" onclick="viewSale(${s.id})">Ver</button>
                                    ${CURRENT_USER.role === 'admin' ? 
                                        `<button class="btn btn-small btn-danger" onclick="deleteSale(${s.id})">Eliminar</button>` 
                                        : ''}
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    } catch (error) {
        console.error('Error loading sales history:', error);
    }
}

async function viewSale(id) {
    try {
        const sale = await apiRequest(`/sales/${id}`);
        
        alert(`
Venta #${sale.id}
Cliente: ${sale.customer}
Vendedor: ${sale.user}
Método de pago: ${sale.payment_method}
Fecha: ${new Date(sale.created_at).toLocaleString()}

Productos:
${sale.items.map(i => `${i.product} - ${i.quantity} x $${i.unit_price.toFixed(2)}`).join('\n')}

Total: $${sale.total.toFixed(2)}
        `);
    } catch (error) {
        alert('Error al cargar la venta');
    }
}

async function deleteSale(id) {
    if (!confirm('¿Eliminar esta venta?')) return;
    
    try {
        await apiRequest(`/sales/${id}`, 'DELETE');
        alert('Venta eliminada');
        loadSalesHistory();
    } catch (error) {
        alert('Error al eliminar la venta');
    }
}

// ========== PRODUCTS ==========
async function loadProducts() {
    try {
        const products = await apiRequest('/products');
        const productsTable = document.getElementById('products-table');
        
        productsTable.innerHTML = `
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Nombre</th>
                            <th>Categoría</th>
                            <th>Proveedor</th>
                            <th>Precio</th>
                            <th>Stock</th>
                            <th>Stock Mín</th>
                            <th>Estado</th>
                            <th>Acciones</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${products.map(p => {
                            const stockStatus = p.is_low_stock ? 
                                '<span style="color: #dc3545; font-weight: bold;">⚠️ Bajo</span>' : 
                                '<span style="color: #28a745;">✓ OK</span>';
                            return `
                                <tr ${p.is_low_stock ? 'style="background-color: #fff3cd;"' : ''}>
                                    <td>${p.id}</td>
                                    <td>${p.name}</td>
                                    <td>${p.category || 'N/A'}</td>
                                    <td>${p.supplier_name || 'Sin proveedor'}</td>
                                    <td>$${p.price.toFixed(2)}</td>
                                    <td>${p.stock}</td>
                                    <td>${p.min_stock}</td>
                                    <td>${stockStatus}</td>
                                    <td class="actions">
                                        ${CURRENT_USER.role !== 'viewer' ? `
                                            <button class="btn btn-small btn-primary" onclick="editProduct(${p.id})">Editar</button>
                                            ${CURRENT_USER.role === 'admin' ? 
                                                `<button class="btn btn-small btn-danger" onclick="deleteProduct(${p.id})">Eliminar</button>` 
                                                : ''}
                                        ` : ''}
                                    </td>
                                </tr>
                            `;
                        }).join('')}
                    </tbody>
                </table>
            </div>
        `;
    } catch (error) {
        console.error('Error loading products:', error);
    }
}

document.getElementById('add-product-btn').addEventListener('click', async () => {
    try {
        SUPPLIERS = await apiRequest('/suppliers');
        const suppliersOptions = SUPPLIERS.map(s => `<option value="${s.id}">${s.name}</option>`).join('');
        
        showModal('Agregar Producto', `
            <div class="form-group">
                <label>Nombre:</label>
                <input type="text" name="name" required>
            </div>
            <div class="form-group">
                <label>Descripción:</label>
                <textarea name="description" rows="3"></textarea>
            </div>
            <div class="form-group">
                <label>Precio:</label>
                <input type="number" name="price" step="0.01" required>
            </div>
            <div class="form-group">
                <label>Stock Actual:</label>
                <input type="number" name="stock" required>
            </div>
            <div class="form-group">
                <label>Stock Mínimo:</label>
                <input type="number" name="min_stock" value="10" required>
            </div>
            <div class="form-group">
                <label>Categoría:</label>
                <input type="text" name="category">
            </div>
            <div class="form-group">
                <label>Proveedor:</label>
                <select name="supplier_id">
                    <option value="">Sin proveedor</option>
                    ${suppliersOptions}
                </select>
            </div>
        `, async (formData) => {
            const data = Object.fromEntries(formData);
            data.price = parseFloat(data.price);
            data.stock = parseInt(data.stock);
            data.min_stock = parseInt(data.min_stock);
            data.supplier_id = data.supplier_id ? parseInt(data.supplier_id) : null;
            
            await apiRequest('/products', 'POST', data);
            alert('Producto agregado');
            loadProducts();
        });
    } catch (error) {
        alert('Error al cargar proveedores');
    }
});

async function editProduct(id) {
    try {
        const products = await apiRequest('/products');
        SUPPLIERS = await apiRequest('/suppliers');
        const product = products.find(p => p.id === id);
        const suppliersOptions = SUPPLIERS.map(s => 
            `<option value="${s.id}" ${product.supplier_id === s.id ? 'selected' : ''}>${s.name}</option>`
        ).join('');
        
        showModal('Editar Producto', `
            <div class="form-group">
                <label>Nombre:</label>
                <input type="text" name="name" value="${product.name}" required>
            </div>
            <div class="form-group">
                <label>Descripción:</label>
                <textarea name="description" rows="3">${product.description || ''}</textarea>
            </div>
            <div class="form-group">
                <label>Precio:</label>
                <input type="number" name="price" value="${product.price}" step="0.01" required>
            </div>
            <div class="form-group">
                <label>Stock Actual:</label>
                <input type="number" name="stock" value="${product.stock}" required>
            </div>
            <div class="form-group">
                <label>Stock Mínimo:</label>
                <input type="number" name="min_stock" value="${product.min_stock}" required>
            </div>
            <div class="form-group">
                <label>Categoría:</label>
                <input type="text" name="category" value="${product.category || ''}">
            </div>
            <div class="form-group">
                <label>Proveedor:</label>
                <select name="supplier_id">
                    <option value="">Sin proveedor</option>
                    ${suppliersOptions}
                </select>
            </div>
        `, async (formData) => {
            const data = Object.fromEntries(formData);
            data.price = parseFloat(data.price);
            data.stock = parseInt(data.stock);
            data.min_stock = parseInt(data.min_stock);
            data.supplier_id = data.supplier_id ? parseInt(data.supplier_id) : null;
            
            await apiRequest(`/products/${id}`, 'PUT', data);
            alert('Producto actualizado');
            loadProducts();
        });
    } catch (error) {
        alert('Error al cargar el producto');
    }
}

async function deleteProduct(id) {
    if (!confirm('¿Eliminar este producto?')) return;
    
    try {
        await apiRequest(`/products/${id}`, 'DELETE');
        alert('Producto eliminado');
        loadProducts();
    } catch (error) {
        alert('Error al eliminar el producto');
    }
}

// ========== SUPPLIERS ==========
async function loadSuppliers() {
    try {
        const suppliers = await apiRequest('/suppliers');
        const suppliersTable = document.getElementById('suppliers-table');
        
        suppliersTable.innerHTML = `
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Nombre</th>
                            <th>Contacto</th>
                            <th>Email</th>
                            <th>Teléfono</th>
                            <th>Dirección</th>
                            <th>Acciones</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${suppliers.map(s => `
                            <tr>
                                <td>${s.id}</td>
                                <td>${s.name}</td>
                                <td>${s.contact_name || 'N/A'}</td>
                                <td>${s.email || 'N/A'}</td>
                                <td>${s.phone || 'N/A'}</td>
                                <td>${s.address || 'N/A'}</td>
                                <td class="actions">
                                    ${CURRENT_USER.role !== 'viewer' ? `
                                        <button class="btn btn-small btn-primary" onclick="editSupplier(${s.id})">Editar</button>
                                        ${CURRENT_USER.role === 'admin' ? 
                                            `<button class="btn btn-small btn-danger" onclick="deleteSupplier(${s.id})">Eliminar</button>` 
                                            : ''}
                                    ` : ''}
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    } catch (error) {
        console.error('Error loading suppliers:', error);
    }
}

document.getElementById('add-supplier-btn').addEventListener('click', () => {
    showModal('Agregar Proveedor', `
        <div class="form-group">
            <label>Nombre de la Empresa:</label>
            <input type="text" name="name" required>
        </div>
        <div class="form-group">
            <label>Nombre del Contacto:</label>
            <input type="text" name="contact_name">
        </div>
        <div class="form-group">
            <label>Email:</label>
            <input type="email" name="email">
        </div>
        <div class="form-group">
            <label>Teléfono:</label>
            <input type="tel" name="phone">
        </div>
        <div class="form-group">
            <label>Dirección:</label>
            <textarea name="address" rows="2"></textarea>
        </div>
    `, async (formData) => {
        const data = Object.fromEntries(formData);
        await apiRequest('/suppliers', 'POST', data);
        alert('Proveedor agregado');
        loadSuppliers();
    });
});

async function editSupplier(id) {
    try {
        const suppliers = await apiRequest('/suppliers');
        const supplier = suppliers.find(s => s.id === id);
        
        showModal('Editar Proveedor', `
            <div class="form-group">
                <label>Nombre de la Empresa:</label>
                <input type="text" name="name" value="${supplier.name}" required>
            </div>
            <div class="form-group">
                <label>Nombre del Contacto:</label>
                <input type="text" name="contact_name" value="${supplier.contact_name || ''}">
            </div>
            <div class="form-group">
                <label>Email:</label>
                <input type="email" name="email" value="${supplier.email || ''}">
            </div>
            <div class="form-group">
                <label>Teléfono:</label>
                <input type="tel" name="phone" value="${supplier.phone || ''}">
            </div>
            <div class="form-group">
                <label>Dirección:</label>
                <textarea name="address" rows="2">${supplier.address || ''}</textarea>
            </div>
        `, async (formData) => {
            const data = Object.fromEntries(formData);
            await apiRequest(`/suppliers/${id}`, 'PUT', data);
            alert('Proveedor actualizado');
            loadSuppliers();
        });
    } catch (error) {
        alert('Error al cargar el proveedor');
    }
}

async function deleteSupplier(id) {
    if (!confirm('¿Eliminar este proveedor?')) return;
    
    try {
        await apiRequest(`/suppliers/${id}`, 'DELETE');
        alert('Proveedor eliminado');
        loadSuppliers();
    } catch (error) {
        alert('Error al eliminar el proveedor');
    }
}

// ========== CUSTOMERS ==========
async function loadCustomers() {
    try {
        const customers = await apiRequest('/customers');
        const customersTable = document.getElementById('customers-table');
        
        customersTable.innerHTML = `
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Nombre</th>
                            <th>Email</th>
                            <th>Teléfono</th>
                            <th>Dirección</th>
                            <th>Acciones</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${customers.map(c => `
                            <tr>
                                <td>${c.id}</td>
                                <td>${c.name}</td>
                                <td>${c.email || 'N/A'}</td>
                                <td>${c.phone || 'N/A'}</td>
                                <td>${c.address || 'N/A'}</td>
                                <td class="actions">
                                    ${CURRENT_USER.role !== 'viewer' ? `
                                        <button class="btn btn-small btn-primary" onclick="editCustomer(${c.id})">Editar</button>
                                        ${CURRENT_USER.role === 'admin' ? 
                                            `<button class="btn btn-small btn-danger" onclick="deleteCustomer(${c.id})">Eliminar</button>` 
                                            : ''}
                                    ` : ''}
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    } catch (error) {
        console.error('Error loading customers:', error);
    }
}

document.getElementById('add-customer-btn').addEventListener('click', () => {
    showModal('Agregar Cliente', `
        <div class="form-group">
            <label>Nombre:</label>
            <input type="text" name="name" required>
        </div>
        <div class="form-group">
            <label>Email:</label>
            <input type="email" name="email">
        </div>
        <div class="form-group">
            <label>Teléfono:</label>
            <input type="tel" name="phone">
        </div>
        <div class="form-group">
            <label>Dirección:</label>
            <textarea name="address" rows="2"></textarea>
        </div>
    `, async (formData) => {
        const data = Object.fromEntries(formData);
        await apiRequest('/customers', 'POST', data);
        alert('Cliente agregado');
        loadCustomers();
    });
});

async function editCustomer(id) {
    try {
        const customers = await apiRequest('/customers');
        const customer = customers.find(c => c.id === id);
        
        showModal('Editar Cliente', `
            <div class="form-group">
                <label>Nombre:</label>
                <input type="text" name="name" value="${customer.name}" required>
            </div>
            <div class="form-group">
                <label>Email:</label>
                <input type="email"
                <input type="email" name="email" value="${customer.email || ''}">
            </div>
            <div class="form-group">
                <label>Teléfono:</label>
                <input type="tel" name="phone" value="${customer.phone || ''}">
            </div>
            <div class="form-group">
                <label>Dirección:</label>
                <textarea name="address" rows="2">${customer.address || ''}</textarea>
            </div>
        `, async (formData) => {
            const data = Object.fromEntries(formData);
            await apiRequest(`/customers/${id}`, 'PUT', data);
            alert('Cliente actualizado');
            loadCustomers();
        });
    } catch (error) {
        alert('Error al cargar el cliente');
    }
}

async function deleteCustomer(id) {
    if (!confirm('¿Eliminar este cliente?')) return;
    
    try {
        await apiRequest(`/customers/${id}`, 'DELETE');
        alert('Cliente eliminado');
        loadCustomers();
    } catch (error) {
        alert('Error al eliminar el cliente');
    }
}

// ========== USERS ==========
async function loadUsers() {
    try {
        const users = await apiRequest('/users');
        const usersTable = document.getElementById('users-table');
        
        usersTable.innerHTML = `
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Usuario</th>
                            <th>Rol</th>
                            <th>Creado</th>
                            <th>Acciones</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${users.map(u => `
                            <tr>
                                <td>${u.id}</td>
                                <td>${u.username}</td>
                                <td>${u.role}</td>
                                <td>${new Date(u.created_at).toLocaleDateString()}</td>
                                <td class="actions">
                                    <button class="btn btn-small btn-danger" onclick="deleteUser(${u.id})">Eliminar</button>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    } catch (error) {
        console.error('Error loading users:', error);
    }
}

document.getElementById('add-user-btn').addEventListener('click', () => {
    showModal('Agregar Usuario', `
        <div class="form-group">
            <label>Usuario:</label>
            <input type="text" name="username" required>
        </div>
        <div class="form-group">
            <label>Contraseña:</label>
            <input type="password" name="password" required>
        </div>
        <div class="form-group">
            <label>Rol:</label>
            <select name="role" required>
                <option value="viewer">Viewer (Solo lectura)</option>
                <option value="manager">Manager (Gestión)</option>
                <option value="admin">Admin (Control total)</option>
            </select>
        </div>
    `, async (formData) => {
        const data = Object.fromEntries(formData);
        await apiRequest('/users', 'POST', data);
        alert('Usuario creado');
        loadUsers();
    });
});

async function deleteUser(id) {
    if (!confirm('¿Eliminar este usuario?')) return;
    
    try {
        await apiRequest(`/users/${id}`, 'DELETE');
        alert('Usuario eliminado');
        loadUsers();
    } catch (error) {
        alert('Error al eliminar el usuario');
    }
}

// ========== LOGS ==========
async function loadLogs() {
    try {
        const logs = await apiRequest('/logs');
        const logsTable = document.getElementById('logs-table');
        
        logsTable.innerHTML = `
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Usuario</th>
                            <th>Acción</th>
                            <th>Detalles</th>
                            <th>Fecha</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${logs.map(l => `
                            <tr>
                                <td>${l.id}</td>
                                <td>${l.username || 'Sistema'}</td>
                                <td>${l.action}</td>
                                <td>${l.details || 'N/A'}</td>
                                <td>${new Date(l.timestamp).toLocaleString()}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    } catch (error) {
        console.error('Error loading logs:', error);
    }
}

// ========== MODAL CLOSE ==========
document.querySelectorAll('.close').forEach(el => {
    el.addEventListener('click', closeModal);
});

window.addEventListener('click', (e) => {
    const modal = document.getElementById('modal');
    if (e.target === modal) {
        closeModal();
    }
});

// ========== INICIALIZACIÓN ==========
if (TOKEN && CURRENT_USER.username) {
    document.getElementById('user-info').textContent = `👤 ${CURRENT_USER.username} (${CURRENT_USER.role})`;
    document.body.className = `role-${CURRENT_USER.role}`;
    showScreen('main-screen');
    loadDashboard();
}