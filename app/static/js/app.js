// ========== CONFIGURACION ==========
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
    console.log('Cambiando a pantalla:', screenId);
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    const screen = document.getElementById(screenId);
    if (screen) {
        screen.classList.add('active');
        console.log('Pantalla activada:', screenId);
    } else {
        console.error('No se encontro la pantalla:', screenId);
    }
}

function showSection(sectionId) {
    document.querySelectorAll('.content-section').forEach(s => s.classList.remove('active'));
    document.getElementById(sectionId + '-section').classList.add('active');
    document.querySelectorAll('.menu-item').forEach(m => m.classList.remove('active'));
    const menuItem = document.querySelector(`[data-section="${sectionId}"]`);
    if (menuItem) menuItem.classList.add('active');
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
        console.log(`API Request: ${method} ${API_URL}${endpoint}`);
        const response = await fetch(API_URL + endpoint, options);
        
        const contentType = response.headers.get("content-type");
        if (!contentType || !contentType.includes("application/json")) {
            const text = await response.text();
            console.error('Respuesta no es JSON:', text.substring(0, 200));
            throw new Error('El servidor no devolvio JSON.');
        }
        
        if (response.status === 401) {
            console.warn('Sesion expirada');
            localStorage.clear();
            TOKEN = null;
            CURRENT_USER = {};
            showScreen('login-screen');
            throw new Error('Sesion expirada. Por favor inicia sesion nuevamente.');
        }
        
        const data = await response.json();
        
        if (!response.ok) {
            console.error('Error en respuesta:', data);
            throw new Error(data.msg || 'Error en la peticion');
        }
        
        console.log('API Response OK:', endpoint);
        return data;
    } catch (error) {
        console.error('API Error:', error);
        if (error.message !== 'Sesion expirada. Por favor inicia sesion nuevamente.') {
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
        console.log('Intentando login...');
        const data = await apiRequest('/auth/login', 'POST', { username, password });
        
        if (!data.access_token || !data.user) {
            throw new Error('Respuesta invalida del servidor');
        }
        
        TOKEN = data.access_token;
        CURRENT_USER = data.user;
        
        localStorage.setItem('token', TOKEN);
        localStorage.setItem('user', JSON.stringify(CURRENT_USER));
        
        console.log('Login exitoso:', CURRENT_USER);
        
        document.getElementById('user-info').textContent = `${CURRENT_USER.username} (${CURRENT_USER.role})`;
        document.body.className = `role-${CURRENT_USER.role}`;
        
        console.log('Cambiando a pantalla principal...');
        showScreen('main-screen');
        
        console.log('Cargando dashboard...');
        await loadDashboard();
        
    } catch (error) {
        console.error('Login error:', error);
        showError('login-error', error.message || 'Usuario o contrasena incorrectos');
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
        console.log('Cargando dashboard...');
        const data = await apiRequest('/dashboard');
        const products = await apiRequest('/products');
        
        document.getElementById('total-sales').textContent = `$${data.total_sales.toFixed(2)}`;
        document.getElementById('total-products').textContent = data.total_products;
        document.getElementById('total-customers').textContent = data.total_customers;
        document.getElementById('total-suppliers').textContent = data.total_suppliers || 0;
        
        const lowStockProducts = products.filter(p => p.is_low_stock);
        const lowStockAlert = document.getElementById('low-stock-alert');
        const lowStockList = document.getElementById('low-stock-list');
        
        if (lowStockProducts.length > 0) {
            lowStockAlert.style.display = 'block';
            lowStockList.innerHTML = lowStockProducts.map(p => `
                <div style="padding: 8px; border-bottom: 1px solid #ffc107;">
                    <strong>${p.name}</strong> - Stock: <span style="color: #dc3545; font-weight: bold;">${p.stock}</span> 
                    (Minimo: ${p.min_stock})
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
        
        console.log('Dashboard cargado exitosamente');
    } catch (error) {
        console.error('Error loading dashboard:', error);
        alert('Error al cargar el dashboard.');
    }
}

// ========== SALES PAGE ==========
async function loadSalesPage() {
    try {
        const products = await apiRequest('/products');
        const productsGrid = document.getElementById('products-grid');
        productsGrid.innerHTML = products.map(p => {
            const lowStockClass = p.is_low_stock ? 'style="border-color: #dc3545;"' : '';
            const lowStockBadge = p.is_low_stock ? '<span style="color: #dc3545; font-size: 11px;">Stock Bajo</span>' : '';
            const iva = p.iva_rate || 16;
            const priceWithIVA = p.price * (1 + iva / 100);
            return `
                <div class="product-card" ${lowStockClass} onclick="addToCart(${p.id}, '${p.name.replace(/'/g, "\\'")}', ${p.price}, ${p.stock}, ${iva})">
                    <h4>${p.name}</h4>
                    <p class="price">$${p.price.toFixed(2)}</p>
                    <p style="font-size: 11px; color: #666;">+ IVA (${iva}%): $${priceWithIVA.toFixed(2)}</p>
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

function addToCart(productId, name, price, stock, iva = 16) {
    const existing = CART.find(item => item.productId === productId);
    
    if (existing) {
        if (existing.quantity < stock) {
            existing.quantity++;
        } else {
            alert('No hay suficiente stock');
            return;
        }
    } else {
        CART.push({ productId, name, price, quantity: 1, stock, iva });
    }
    
    updateCartDisplay();
}

function updateCartDisplay() {
    const cartItems = document.getElementById('cart-items');
    const cartTotal = document.getElementById('cart-total');
    const cartSubtotal = document.getElementById('cart-subtotal');
    const cartIVA = document.getElementById('cart-iva');
    
    if (CART.length === 0) {
        cartItems.innerHTML = '<p style="text-align: center; color: #999;">Carrito vacio</p>';
        cartTotal.textContent = '0.00';
        if (cartSubtotal) cartSubtotal.textContent = '0.00';
        if (cartIVA) cartIVA.textContent = '0.00';
        return;
    }
    
    cartItems.innerHTML = CART.map((item, index) => {
        const subtotal = item.price * item.quantity;
        const ivaAmount = subtotal * (item.iva / 100);
        
        return `
        <div class="cart-item">
            <div class="cart-item-info">
                <h4>${item.name}</h4>
                <p>$${item.price.toFixed(2)} c/u (IVA: ${item.iva}%)</p>
                <small style="color: #666;">Subtotal: $${subtotal.toFixed(2)} + IVA: $${ivaAmount.toFixed(2)}</small>
            </div>
            <div class="cart-item-qty">
                <button onclick="updateCartQty(${index}, -1)">-</button>
                <span>${item.quantity}</span>
                <button onclick="updateCartQty(${index}, 1)">+</button>
                <button class="cart-item-remove" onclick="removeFromCart(${index})">X</button>
            </div>
        </div>
    `;
    }).join('');
    
    const subtotal = CART.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    const totalIVA = CART.reduce((sum, item) => {
        const itemSubtotal = item.price * item.quantity;
        return sum + (itemSubtotal * (item.iva / 100));
    }, 0);
    const total = subtotal + totalIVA;
    
    if (cartSubtotal) cartSubtotal.textContent = subtotal.toFixed(2);
    if (cartIVA) cartIVA.textContent = totalIVA.toFixed(2);
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
        alert('El carrito esta vacio');
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
        alert(`Venta completada! Total: $${result.total.toFixed(2)}`);
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
        alert(`Venta #${sale.id}\nCliente: ${sale.customer}\nVendedor: ${sale.user}\nMetodo de pago: ${sale.payment_method}\nFecha: ${new Date(sale.created_at).toLocaleString()}\n\nProductos:\n${sale.items.map(i => `${i.product} - ${i.quantity} x $${i.unit_price.toFixed(2)}`).join('\n')}\n\nTotal: $${sale.total.toFixed(2)}`);
    } catch (error) {
        alert('Error al cargar la venta');
    }
}

async function deleteSale(id) {
    if (!confirm('Eliminar esta venta?')) return;
    
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
        
        const searchHTML = `
            <div style="margin-bottom: 20px;">
                <input type="text" id="product-search" placeholder="Buscar producto..." 
                       style="width: 100%; padding: 12px; border: 2px solid #e0e0e0; border-radius: 8px; font-size: 14px;">
            </div>
        `;
        
        productsTable.innerHTML = searchHTML + `
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Nombre</th>
                            <th>Categoria</th>
                            <th>Proveedor</th>
                            <th>Precio</th>
                            <th>IVA (%)</th>
                            <th>Precio + IVA</th>
                            <th>Stock</th>
                            <th>Stock Min</th>
                            <th>Estado</th>
                            <th>Acciones</th>
                        </tr>
                    </thead>
                    <tbody id="products-tbody">
                        ${products.map(p => {
                            const stockStatus = p.is_low_stock ? 
                                '<span style="color: #dc3545; font-weight: bold;">Bajo</span>' : 
                                '<span style="color: #28a745;">OK</span>';
                            const iva = p.iva_rate || 16;
                            const priceWithIVA = p.price * (1 + iva / 100);
                            return `
                                <tr ${p.is_low_stock ? 'style="background-color: #fff3cd;"' : ''} 
                                    data-search="${p.name.toLowerCase()} ${(p.category || '').toLowerCase()} ${(p.supplier_name || '').toLowerCase()}">
                                    <td>${p.id}</td>
                                    <td>${p.name}</td>
                                    <td>${p.category || 'N/A'}</td>
                                    <td>${p.supplier_name || 'Sin proveedor'}</td>
                                    <td>$${p.price.toFixed(2)}</td>
                                    <td>${iva}%</td>
                                    <td>$${priceWithIVA.toFixed(2)}</td>
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
        
        document.getElementById('product-search').addEventListener('input', (e) => {
            const searchTerm = e.target.value.toLowerCase();
            const rows = document.querySelectorAll('#products-tbody tr');
            rows.forEach(row => {
                const searchText = row.dataset.search || '';
                row.style.display = searchText.includes(searchTerm) ? '' : 'none';
            });
        });
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
                <label>Descripcion:</label>
                <textarea name="description" rows="3"></textarea>
            </div>
            <div class="form-group">
                <label>Precio (sin IVA):</label>
                <input type="number" name="price" step="0.01" required>
            </div>
            <div class="form-group">
                <label>IVA (%):</label>
                <input type="number" name="iva_rate" value="16" min="0" max="100" required>
            </div>
            <div class="form-group">
                <label>Stock Actual:</label>
                <input type="number" name="stock" required>
            </div>
            <div class="form-group">
                <label>Stock Minimo:</label>
                <input type="number" name="min_stock" value="10" required>
            </div>
            <div class="form-group">
                <label>Categoria:</label>
                <input type="text" name="category">
            </div>
            <div class="form-group">
                <label>Proveedor:</label>
                <select name="supplier_id" required>
                    <option value="">Seleccione un proveedor</option>
                    ${suppliersOptions}
                </select>
            </div>
        `, async (formData) => {
            const data = Object.fromEntries(formData);
            data.price = parseFloat(data.price);
            data.iva_rate = parseFloat(data.iva_rate);
            data.stock = parseInt(data.stock);
            data.min_stock = parseInt(data.min_stock);
            data.supplier_id = data.supplier_id ? parseInt(data.supplier_id) : null;
            data.include_iva = true;
            
            if (!data.supplier_id) {
                alert('Debe seleccionar un proveedor');
                return;
            }
            
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
                <label>Descripcion:</label>
                <textarea name="description" rows="3">${product.description || ''}</textarea>
            </div>
            <div class="form-group">
                <label>Precio (sin IVA):</label>
                <input type="number" name="price" value="${product.price}" step="0.01" required>
            </div>
            <div class="form-group">
                <label>IVA (%):</label>
                <input type="number" name="iva_rate" value="${product.iva_rate || 16}" min="0" max="100" required>
            </div>
            <div class="form-group">
                <label>Stock Actual:</label>
                <input type="number" name="stock" value="${product.stock}" required>
            </div>
            <div class="form-group">
                <label>Stock Minimo:</label>
                <input type="number" name="min_stock" value="${product.min_stock}" required>
            </div>
            <div class="form-group">
                <label>Categoria:</label>
                <input type="text" name="category" value="${product.category || ''}">
            </div>
            <div class="form-group">
                <label>Proveedor:</label>
                <select name="supplier_id" required>
                    <option value="">Seleccione un proveedor</option>
                    ${suppliersOptions}
                </select>
            </div>
        `, async (formData) => {
            const data = Object.fromEntries(formData);
            data.price = parseFloat(data.price);
            data.iva_rate = parseFloat(data.iva_rate);
            data.stock = parseInt(data.stock);
            data.min_stock = parseInt(data.min_stock);
            data.supplier_id = data.supplier_id ? parseInt(data.supplier_id) : null;
            data.include_iva = true;
            
            if (!data.supplier_id) {
                alert('Debe seleccionar un proveedor');
                return;
            }
            
            await apiRequest(`/products/${id}`, 'PUT', data);
            alert('Producto actualizado');
            loadProducts();
        });
    } catch (error) {
        alert('Error al cargar el producto');
    }
}

async function deleteProduct(id) {
    if (!confirm('Eliminar este producto?')) return;
    
    try {
        await apiRequest(`/products/${id}`, 'DELETE');
        alert('Producto eliminado');
        loadProducts();
    } catch (error) {
        alert('Error al eliminar el producto');
    }
}

// ========== SUPPLIERS - ACTUALIZADO CON GESTION DE PRODUCTOS ==========
async function loadSuppliers() {
    try {
        const suppliers = await apiRequest('/suppliers');
        const suppliersTable = document.getElementById('suppliers-table');
        
        const searchHTML = `
            <div style="margin-bottom: 20px;">
                <input type="text" id="supplier-search" placeholder="Buscar proveedor..." 
                       style="width: 100%; padding: 12px; border: 2px solid #e0e0e0; border-radius: 8px; font-size: 14px;">
            </div>
        `;
        
        suppliersTable.innerHTML = searchHTML + `
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Nombre</th>
                            <th>Contacto</th>
                            <th>Email</th>
                            <th>Telefono</th>
                            <th>Direccion</th>
                            <th>Acciones</th>
                        </tr>
                    </thead>
                    <tbody id="suppliers-tbody">
                        ${suppliers.map(s => `
                            <tr data-search="${s.name.toLowerCase()} ${(s.contact_name || '').toLowerCase()} ${(s.email || '').toLowerCase()}">
                                <td>${s.id}</td>
                                <td>${s.name}</td>
                                <td>${s.contact_name || 'N/A'}</td>
                                <td>${s.email || 'N/A'}</td>
                                <td>${s.phone || 'N/A'}</td>
                                <td>${s.address || 'N/A'}</td>
                                <td class="actions">
                                    <button class="btn btn-small btn-primary" onclick="viewSupplierProducts(${s.id}, '${s.name.replace(/'/g, "\\'")}')">Ver Productos</button>
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
        
        document.getElementById('supplier-search').addEventListener('input', (e) => {
            const searchTerm = e.target.value.toLowerCase();
            const rows = document.querySelectorAll('#suppliers-tbody tr');
            rows.forEach(row => {
                const searchText = row.dataset.search || '';
                row.style.display = searchText.includes(searchTerm) ? '' : 'none';
            });
        });
    } catch (error) {
        console.error('Error loading suppliers:', error);
    }
}

// Botón "Agregar Proveedor"
document.getElementById('add-supplier-btn').addEventListener('click', () => {
    showModal('Agregar Proveedor', `
        <div class="form-group">
            <label>Nombre:</label>
            <input type="text" name="name" required>
        </div>
        <div class="form-group">
            <label>Contacto:</label>
            <input type="text" name="contact_name">
        </div>
        <div class="form-group">
            <label>Email:</label>
            <input type="email" name="email">
        </div>
        <div class="form-group">
            <label>Telefono:</label>
            <input type="tel" name="phone">
        </div>
        <div class="form-group">
            <label>Direccion:</label>
            <textarea name="address" rows="2"></textarea>
        </div>
    `, async (formData) => {
        const data = Object.fromEntries(formData);
        await apiRequest('/suppliers', 'POST', data);
        alert('Proveedor agregado');
        loadSuppliers();
    });
});

// Editar proveedor
async function editSupplier(id) {
    try {
        const suppliers = await apiRequest('/suppliers');
        const supplier = suppliers.find(s => s.id === id);

        if (!supplier) {
            alert('No se encontró el proveedor');
            return;
        }

        showModal('Editar Proveedor', `
            <div class="form-group">
                <label>Nombre:</label>
                <input type="text" name="name" value="${supplier.name || ''}" required>
            </div>
            <div class="form-group">
                <label>Contacto:</label>
                <input type="text" name="contact_name" value="${supplier.contact_name || ''}">
            </div>
            <div class="form-group">
                <label>Email:</label>
                <input type="email" name="email" value="${supplier.email || ''}">
            </div>
            <div class="form-group">
                <label>Telefono:</label>
                <input type="tel" name="phone" value="${supplier.phone || ''}">
            </div>
            <div class="form-group">
                <label>Direccion:</label>
                <textarea name="address" rows="2">${supplier.address || ''}</textarea>
            </div>
        `, async (formData) => {
            const data = Object.fromEntries(formData);
            await apiRequest(`/suppliers/${id}`, 'PUT', data);
            alert('Proveedor actualizado');
            loadSuppliers();
        });
    } catch (error) {
        console.error(error);
        alert('Error al cargar el proveedor');
    }
}

// Eliminar proveedor
async function deleteSupplier(id) {
    if (!confirm('¿Eliminar este proveedor?')) return;

    try {
        await apiRequest(`/suppliers/${id}`, 'DELETE');
        alert('Proveedor eliminado');
        loadSuppliers();
    } catch (error) {
        console.error(error);
        alert('Error al eliminar el proveedor');
    }
}


async function viewSupplierProducts(supplierId, supplierName) {
    try {
        const data = await apiRequest(`/suppliers/${supplierId}/products-catalog`);
        const allProducts = await apiRequest('/products');

        const assignedProductIds = data.products.map(p => p.product_id);
        const availableProducts = allProducts.filter(p => !assignedProductIds.includes(p.id));

        const modal = document.getElementById('modal');
        const modalContentEl = document.querySelector('.modal-content');
        const modalForm = document.getElementById('modal-form');
        const modalBody = document.getElementById('modal-body');

        // Guardar ancho original
        const originalMaxWidth = modalContentEl.style.maxWidth || '500px';

        // Hacer el modal más grande
        modalContentEl.style.maxWidth = '1200px';

        // NO ocultamos el form, solo desactivamos el submit
        modalForm.style.display = 'block';
        modalForm.onsubmit = (e) => e.preventDefault();

        document.getElementById('modal-title').textContent = 'Catálogo del Proveedor';

        const modalContent = `
            <div style="margin-bottom: 20px;">
                <h3 style="color: #333; margin-bottom: 10px;">Productos de ${supplierName}</h3>
                <p style="color: #666; margin-bottom: 15px;">Gestiona los productos que este proveedor te vende</p>
                
                ${CURRENT_USER.role !== 'viewer' ? `
                    <button class="btn btn-primary" onclick="addProductToSupplier(${supplierId}, '${supplierName.replace(/'/g, "\\'")}')">
                        + Agregar Producto
                    </button>
                ` : ''}
            </div>
            
            <div class="table-container" style="max-height: 400px; overflow-y: auto;">
                <table>
                    <thead style="position: sticky; top: 0; background: #667eea;">
                        <tr>
                            <th>Producto</th>
                            <th>Categoría</th>
                            <th>Precio Compra</th>
                            <th>Precio Venta</th>
                            <th>Ganancia</th>
                            <th>Margen %</th>
                            <th>Cantidad Disp.</th>
                            <th>Acciones</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.products.length === 0 ? `
                            <tr>
                                <td colspan="8" style="text-align: center; padding: 30px; color: #999;">
                                    No hay productos asignados a este proveedor.<br>
                                    <small>Haz clic en "+ Agregar Producto" para empezar.</small>
                                </td>
                            </tr>
                        ` : data.products.map(p => `
                            <tr>
                                <td><strong>${p.product_name}</strong></td>
                                <td>${p.product_category || 'N/A'}</td>
                                <td style="color: #dc3545; font-weight: bold;">$${(p.purchase_price || 0).toFixed(2)}</td>
                                <td style="color: #28a745; font-weight: bold;">$${(p.sale_price || 0).toFixed(2)}</td>
                                <td>$${(p.profit_margin || 0).toFixed(2)}</td>
                                <td style="color: ${
                                    p.profit_percentage > 30 ? '#28a745' :
                                    p.profit_percentage > 15 ? '#ffc107' :
                                    '#dc3545'
                                };">
                                    ${(p.profit_percentage || 0).toFixed(1)}%
                                </td>
                                <td>${p.quantity_available || 0}</td>
                                <td class="actions">
                                    ${CURRENT_USER.role !== 'viewer' ? `
                                        <button class="btn btn-small btn-primary"
                                            onclick="editSupplierProduct(
                                                ${supplierId},
                                                ${p.id},
                                                '${(p.product_name || '').replace(/'/g, "\\'")}',
                                                ${p.purchase_price || 0},
                                                ${p.quantity_available || 0},
                                                '${supplierName.replace(/'/g, "\\'")}'
                                            )">
                                            Editar
                                        </button>
                                        ${CURRENT_USER.role === 'admin' ? `
                                            <button class="btn btn-small btn-danger"
                                                onclick="deleteSupplierProduct(
                                                    ${supplierId},
                                                    ${p.id},
                                                    '${supplierName.replace(/'/g, "\\'")}'
                                                )">
                                                Eliminar
                                            </button>
                                        ` : ''}
                                    ` : ''}
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;

        modalBody.innerHTML = modalContent;
        modal.classList.add('active');

        // Funcion para cerrar y restaurar tamaño
        const closeModalFn = () => {
            modal.classList.remove('active');
            modalContentEl.style.maxWidth = originalMaxWidth;
            modalBody.innerHTML = '';
        };

        document.querySelectorAll('.close').forEach(el => {
            el.onclick = closeModalFn;
        });

        window.addEventListener('click', function closeOnOutside(e) {
            if (e.target === modal) {
                closeModalFn();
                window.removeEventListener('click', closeOnOutside);
            }
        });

    } catch (error) {
        console.error('Error loading supplier products:', error);
        alert('Error al cargar productos del proveedor: ' + error.message);
    }
}

async function addProductToSupplier(supplierId, supplierName) {
    try {
        const allProducts = await apiRequest('/products');
        const assignedProducts = await apiRequest(`/suppliers/${supplierId}/products-catalog`);
        const assignedProductIds = assignedProducts.products.map(p => p.product_id);
        const availableProducts = allProducts.filter(p => !assignedProductIds.includes(p.id));
        
        if (availableProducts.length === 0) {
            alert('Todos los productos ya estan asignados a este proveedor');
            return;
        }
        
        showModal('Agregar Producto al Proveedor', `
            <p style="color: #666; margin-bottom: 15px;">Proveedor: <strong>${supplierName}</strong></p>
            
            <div class="form-group">
                <label>Producto:</label>
                <select name="product_id" required>
                    <option value="">Seleccione un producto</option>
                    ${availableProducts.map(p => `
                        <option value="${p.id}">${p.name} (Precio venta: ${p.price.toFixed(2)})</option>
                    `).join('')}
                </select>
            </div>
            
            <div class="form-group">
                <label>Precio de Compra:</label>
                <input type="number" name="purchase_price" step="0.01" required 
                       placeholder="Precio al que el proveedor te vende">
                <small style="color: #666;">El precio de venta actual se usará para calcular el margen</small>
            </div>
            
            <div class="form-group">
                <label>Cantidad Disponible:</label>
                <input type="number" name="quantity_available" value="0" required
                       placeholder="Cantidad que el proveedor tiene disponible">
            </div>
        `, async (formData) => {
            const data = Object.fromEntries(formData);
            data.product_id = parseInt(data.product_id);
            data.purchase_price = parseFloat(data.purchase_price);
            data.quantity_available = parseInt(data.quantity_available);
            
            await apiRequest(`/suppliers/${supplierId}/products-catalog`, 'POST', data);
            alert('Producto agregado al proveedor');
            viewSupplierProducts(supplierId, supplierName);
        });
    } catch (error) {
        console.error('Error:', error);
        alert('Error al agregar producto');
    }
}

async function editSupplierProduct(supplierId, spId, productName, currentPrice, currentQty, supplierName) {
    showModal('Editar Producto del Proveedor', `
        <p style="color: #666; margin-bottom: 15px;">Producto: <strong>${productName}</strong></p>
        
        <div class="form-group">
            <label>Precio de Compra:</label>
            <input type="number" name="purchase_price" step="0.01" value="${currentPrice}" required>
        </div>
        
        <div class="form-group">
            <label>Cantidad Disponible:</label>
            <input type="number" name="quantity_available" value="${currentQty}" required>
        </div>
    `, async (formData) => {
        const data = Object.fromEntries(formData);
        data.purchase_price = parseFloat(data.purchase_price);
        data.quantity_available = parseInt(data.quantity_available);
        
        await apiRequest(`/suppliers/${supplierId}/products-catalog/${spId}`, 'PUT', data);
        alert('Producto actualizado');
        viewSupplierProducts(supplierId, supplierName);
    });
}

async function deleteSupplierProduct(supplierId, spId, supplierName) {
    if (!confirm('Eliminar este producto del proveedor?')) return;
    
    try {
        await apiRequest(`/suppliers/${supplierId}/products-catalog/${spId}`, 'DELETE');
        alert('Producto eliminado del proveedor');
        viewSupplierProducts(supplierId, supplierName);
    } catch (error) {
        alert('Error al eliminar producto del proveedor');
    }
}
// ========== CUSTOMERS ==========
async function loadCustomers() {
    try {
        const customers = await apiRequest('/customers');
        const customersTable = document.getElementById('customers-table');
        
        const searchHTML = `
            <div style="margin-bottom: 20px;">
                <input type="text" id="customer-search" placeholder="Buscar cliente..." 
                       style="width: 100%; padding: 12px; border: 2px solid #e0e0e0; border-radius: 8px; font-size: 14px;">
            </div>
        `;
        
        customersTable.innerHTML = searchHTML + `
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Nombre</th>
                            <th>Email</th>
                            <th>Telefono</th>
                            <th>Direccion</th>
                            <th>Acciones</th>
                        </tr>
                    </thead>
                    <tbody id="customers-tbody">
                        ${customers.map(c => `
                            <tr data-search="${c.name.toLowerCase()} ${(c.email || '').toLowerCase()} ${(c.phone || '').toLowerCase()}">
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
        
        document.getElementById('customer-search').addEventListener('input', (e) => {
            const searchTerm = e.target.value.toLowerCase();
            const rows = document.querySelectorAll('#customers-tbody tr');
            rows.forEach(row => {
                const searchText = row.dataset.search || '';
                row.style.display = searchText.includes(searchTerm) ? '' : 'none';
            });
        });
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
            <label>Telefono:</label>
            <input type="tel" name="phone">
        </div>
        <div class="form-group">
            <label>Direccion:</label>
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
                <input type="email" name="email" value="${customer.email || ''}">
            </div>
            <div class="form-group">
                <label>Telefono:</label>
                <input type="tel" name="phone" value="${customer.phone || ''}">
            </div>
            <div class="form-group">
                <label>Direccion:</label>
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
    if (!confirm('Eliminar este cliente?')) return;
    
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
            <label>Contrasena:</label>
            <input type="password" name="password" required>
        </div>
        <div class="form-group">
            <label>Rol:</label>
            <select name="role" required>
                <option value="viewer">Viewer (Solo lectura)</option>
                <option value="manager">Manager (Gestion)</option>
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
    if (!confirm('Eliminar este usuario?')) return;
    
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
                            <th>Accion</th>
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

// ========== INICIALIZACION ==========
console.log('Inicializando aplicacion...');
console.log('Token guardado:', TOKEN ? 'Si' : 'No');
console.log('Usuario guardado:', CURRENT_USER.username || 'No');

if (TOKEN && CURRENT_USER.username) {
    console.log('Usuario ya logueado, mostrando pantalla principal');
    document.getElementById('user-info').textContent = `${CURRENT_USER.username} (${CURRENT_USER.role})`;
    document.body.className = `role-${CURRENT_USER.role}`;
    showScreen('main-screen');
    loadDashboard();
} else {
    console.log('No hay sesion activa, mostrando login');
    showScreen('login-screen');
}