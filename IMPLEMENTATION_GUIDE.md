# GUÍA DE IMPLEMENTACIÓN - CATEGORÍAS PERSONALIZADAS POR CLIENTE

## 1. DIAGNÓSTICO ACTUAL

### Estado de la Tabla Category
- El modelo `Category` EXISTE en `/models/models.py` (líneas 38-53)
- YA TIENE `client_id` (FK a Client) - PERFECTO para multi-tenant
- Tiene campos: `id`, `client_id`, `name`, `description`, `created_at`
- Relación: `Client.categories` ya definida (línea 32 en Client)
- **PROBLEMA**: No se integra con User.categoria (que es ENUM)

### Estado de User.categoria
- Campo `categoria` en tabla `user` (línea 82-88 en models.py)
- **TIPO ACTUAL**: db.Enum con valores fijos: "Coordinador", "Empleado", "Gestor"
- **LIMITACIÓN**: Hardcodeado, requiere migración para cambios
- **UBICACIÓN**: models/models.py línea 82-88

### Donde se Usa
1. **Base de datos**: Tabla `user` columna `categoria`
2. **Backend**: routes/admin.py (línea 20, 22-35, múltiples referencias)
3. **Frontend**: 
   - manage_users.html (filtro línea 32-37)
   - user_form.html (selector)
   - export_excel.html (filtros)
4. **Exportación**: routes/export.py (múltiples líneas)
5. **API**: admin_calendar (línea 803 en admin.py)

---

## 2. FLUJO ACTUAL DE CATEGORÍAS

```
┌─────────────────────────────────────────┐
│        CATEGORÍAS HARDCODEADAS          │
│      (DEFAULT_CATEGORIES en admin.py)   │
└──────────────┬──────────────────────────┘
               │
               ▼
        ["Coordinador",
         "Empleado",
         "Gestor"]
               │
    ┌──────────┴──────────┐
    │                     │
    ▼                     ▼
User.categoria        Filtros en
(ENUM)               Templates
    │                     │
    └────────┬────────────┘
             │
             ▼
    Exportaciones,
    Reportes,
    Calendario
```

---

## 3. FLUJO DESEADO (MULTI-TENANT DINÁMICO)

```
┌─────────────────────────────────────┐
│        Client                       │
│    (aluminios-lara, otro, etc)      │
└────────────┬────────────────────────┘
             │
             ▼
   ┌─────────────────────┐
   │  Category           │
   │  - client_id (FK)   │
   │  - name             │
   │  - description      │
   │  - created_at       │
   └────────┬────────────┘
            │ (1:N)
            │
    ┌───────┴────────┐
    │                │
    ▼                ▼
Coordinador    Empleado   Gestor
(dinámico)     (dinámico) (dinámico)
    │                │        │
    └───────┬────────┴────────┘
            │
            ▼
     ┌────────────────────┐
     │  User              │
     │  - category_id(FK) │ ← Nuevo: reemplaza ENUM
     │  - client_id       │
     │  - ... otros campos│
     └────────────────────┘
            │
    ┌───────┴────────────────────┐
    │                            │
    ▼                            ▼
Backend API            Frontend UI
(Filtros dinámicos)    (Selects dinámicos)
```

---

## 4. CAMBIOS EN MODELOS

### 4.1 Actualizar User Model (models/models.py)

**ANTES:**
```python
categoria = db.Column(
    db.Enum(
        "Coordinador", "Empleado", "Gestor",
        name="category_enum"
    ),
    nullable=True
)
```

**DESPUÉS:**
```python
category_id = db.Column(
    db.Integer, 
    db.ForeignKey("category.id", ondelete="SET NULL"), 
    nullable=True
)

# Relación
category_rel = db.relationship("Category", backref="users", lazy=True)

# Propiedad para compatibilidad (opcional)
@property
def categoria(self):
    """Compatibilidad con código antiguo"""
    return self.category_rel.name if self.category_rel else None
```

### 4.2 Agregar Category a TENANT_MODELS (models/database.py)

**ANTES:**
```python
TENANT_MODELS = {
    "User",
    "TimeRecord",
    "EmployeeStatus",
    "WorkPause",
    "LeaveRequest",
    "SystemConfig",
}
```

**DESPUÉS:**
```python
TENANT_MODELS = {
    "User",
    "Category",              # ← NUEVO
    "TimeRecord",
    "EmployeeStatus",
    "WorkPause",
    "LeaveRequest",
    "SystemConfig",
}
```

---

## 5. CAMBIOS EN RUTAS (routes/admin.py)

### 5.1 Actualizar get_categorias_disponibles()

**ACTUAL:**
```python
def get_categorias_disponibles():
    """
    Obtiene las categorías dinámicas del cliente actual desde la BD.
    Si no hay categorías definidas, retorna lista vacía.
    """
    client_id = session.get("client_id")
    if not client_id:
        return []

    categories = Category.query.filter_by(client_id=client_id).order_by(Category.name).all()
    if categories:
        return [c.name for c in categories]

    return DEFAULT_CATEGORIES.copy()  # ← Fallback (todavía necesario para compatibilidad)
```

**MEJORADO:**
```python
def get_categorias_disponibles():
    """
    Obtiene las categorías dinámicas del cliente actual desde la BD.
    Retorna lista de tuplas: [(id, name), ...]
    Para UI: retorna solo nombres
    """
    client_id = session.get("client_id")
    if not client_id:
        return []

    try:
        categories = Category.query.filter_by(client_id=client_id).order_by(Category.name).all()
        return [(c.id, c.name) for c in categories] if categories else []
    except Exception as e:
        app.logger.warning(f"Error loading categories: {e}")
        return []

def get_categorias_nombres():
    """Helper para obtener solo nombres (para compatibilidad)"""
    cats = get_categorias_disponibles()
    return [name for _, name in cats]
```

### 5.2 Agregar CRUD de Categorías

**NUEVAS RUTAS:**

```python
@admin_bp.route("/admin/categories", methods=["GET"])
@admin_required
def manage_categories():
    """Listar todas las categorías del cliente"""
    client_id = session.get("client_id")
    categories = Category.query.filter_by(client_id=client_id).order_by(Category.name).all()
    
    return render_template("manage_categories.html", 
                         categories=categories,
                         categorias=get_categorias_disponibles())

@admin_bp.route("/admin/categories/add", methods=["GET", "POST"])
@admin_required
def add_category():
    """Crear nueva categoría"""
    if request.method == "POST":
        client_id = session.get("client_id")
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        
        if not name:
            flash("El nombre de categoría es obligatorio.", "danger")
            return redirect(url_for("admin.add_category"))
        
        # Verificar que no exista
        existing = Category.query.filter_by(
            client_id=client_id, 
            name=name
        ).first()
        
        if existing:
            flash(f"La categoría '{name}' ya existe.", "warning")
            return redirect(url_for("admin.add_category"))
        
        category = Category(
            client_id=client_id,
            name=name,
            description=description or None
        )
        db.session.add(category)
        db.session.commit()
        
        flash(f"Categoría '{name}' creada exitosamente.", "success")
        return redirect(url_for("admin.manage_categories"))
    
    return render_template("category_form.html", action="add")

@admin_bp.route("/admin/categories/edit/<int:category_id>", methods=["GET", "POST"])
@admin_required
def edit_category(category_id):
    """Editar categoría existente"""
    category = Category.query.get_or_404(category_id)
    
    # Verificar que pertenece al cliente actual
    if category.client_id != session.get("client_id"):
        abort(403)
    
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        
        if not name:
            flash("El nombre de categoría es obligatorio.", "danger")
            return redirect(url_for("admin.edit_category", category_id=category_id))
        
        # Verificar nombre no duplicado
        existing = Category.query.filter(
            Category.client_id == category.client_id,
            Category.name == name,
            Category.id != category.id
        ).first()
        
        if existing:
            flash(f"La categoría '{name}' ya existe.", "warning")
            return redirect(url_for("admin.edit_category", category_id=category_id))
        
        category.name = name
        category.description = description or None
        db.session.commit()
        
        flash(f"Categoría '{name}' actualizada exitosamente.", "success")
        return redirect(url_for("admin.manage_categories"))
    
    return render_template("category_form.html", 
                         action="edit",
                         category=category)

@admin_bp.route("/admin/categories/delete/<int:category_id>", methods=["POST"])
@admin_required
def delete_category(category_id):
    """Eliminar categoría"""
    category = Category.query.get_or_404(category_id)
    
    # Verificar que pertenece al cliente actual
    if category.client_id != session.get("client_id"):
        abort(403)
    
    # Verificar que no hay usuarios usando esta categoría
    if category.users:
        flash(f"No se puede eliminar: hay {len(category.users)} usuario(s) con esta categoría.", "warning")
        return redirect(url_for("admin.manage_categories"))
    
    name = category.name
    db.session.delete(category)
    db.session.commit()
    
    flash(f"Categoría '{name}' eliminada exitosamente.", "success")
    return redirect(url_for("admin.manage_categories"))
```

### 5.3 Actualizar add_user() y edit_user()

**Cambios en add_user() (alrededor de línea 326):**

```python
# ANTES
categoria = request.form.get("categoria") or None

# DESPUÉS
category_id = request.form.get("category_id") or None
if category_id:
    try:
        category_id = int(category_id)
        # Verificar que categoria pertenece al cliente
        category = Category.query.get(category_id)
        if not category or category.client_id != session.get("client_id"):
            category_id = None
    except (ValueError, TypeError):
        category_id = None
```

**En la creación:**
```python
# ANTES
new_user = User(
    ...
    categoria=categoria,
    ...
)

# DESPUÉS
new_user = User(
    ...
    category_id=category_id,
    ...
)
```

### 5.4 Actualizar filtros en manage_users()

```python
# ANTES
filtro_categoria = request.args.get("categoria", type=str, default="")
if filtro_categoria:
    user_q = user_q.filter(User.categoria == filtro_categoria)

# DESPUÉS
filtro_categoria_id = request.args.get("category_id", type=int, default=0)
if filtro_categoria_id:
    user_q = user_q.filter(User.category_id == filtro_categoria_id)
```

---

## 6. CAMBIOS EN TEMPLATES

### 6.1 manage_users.html

**ANTES:**
```html
<select name="categoria" class="w-full...">
  <option value="">Todas</option>
  {% for cat in categorias %}
    <option value="{{ cat }}">{{ cat }}</option>
  {% endfor %}
</select>
```

**DESPUÉS:**
```html
<select name="category_id" class="w-full...">
  <option value="">Todas</option>
  {% for cat_id, cat_name in categorias %}
    <option value="{{ cat_id }}" 
            {{ 'selected' if request.args.get('category_id')|int == cat_id else '' }}>
      {{ cat_name }}
    </option>
  {% endfor %}
</select>
```

### 6.2 user_form.html

**ANTES:**
```html
<select name="categoria">
  {% for cat in categorias %}
    <option value="{{ cat }}" 
            {{ 'selected' if user and user.categoria == cat else '' }}>
      {{ cat }}
    </option>
  {% endfor %}
</select>
```

**DESPUÉS:**
```html
<select name="category_id">
  <option value="">Sin categoría</option>
  {% for cat_id, cat_name in categorias %}
    <option value="{{ cat_id }}" 
            {{ 'selected' if user and user.category_id == cat_id else '' }}>
      {{ cat_name }}
    </option>
  {% endfor %}
</select>
```

### 6.3 NUEVO: manage_categories.html

```html
{% extends 'base.html' %}

{% block title %}Gestionar Categorías - TimeTracker{% endblock %}

{% block header %}<span class="text-timetracker-primary">Gestionar Categorías</span>{% endblock %}

{% block content %}
<section class="bg-gray-800 shadow-md rounded-lg p-6 mb-6">
  <div class="mb-5">
    <a href="{{ url_for('admin.add_category') }}"
       class="inline-block py-2 px-4 rounded-lg text-white transition-all duration-300 ease-in-out shadow-md hover:opacity-90"
       style="background-color: var(--accent-primary);">
      Añadir Categoría
    </a>
  </div>

  <div class="bg-gray-900 shadow-md rounded-lg p-6 overflow-hidden">
    <div class="overflow-x-auto">
      <table class="min-w-full divide-y divide-gray-700 text-sm">
        <thead class="bg-gray-800 text-gray-400 text-xs uppercase">
          <tr>
            <th class="px-4 py-2 text-left">Nombre</th>
            <th class="px-4 py-2 text-left">Descripción</th>
            <th class="px-4 py-2 text-left">Usuarios</th>
            <th class="px-4 py-2 text-left">Acciones</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-700">
          {% for cat in categories %}
          <tr>
            <td class="px-3 py-2 text-gray-100">{{ cat.name }}</td>
            <td class="px-3 py-2 text-gray-400">{{ cat.description or '-' }}</td>
            <td class="px-3 py-2 text-gray-100">{{ cat.users|length }}</td>
            <td class="px-3 py-2 whitespace-nowrap">
              <a href="{{ url_for('admin.edit_category', category_id=cat.id) }}"
                 class="text-cyan-400 hover:underline mr-3">Editar</a>
              {% if not cat.users %}
                <form method="POST" 
                      action="{{ url_for('admin.delete_category', category_id=cat.id) }}"
                      style="display:inline;"
                      onsubmit="return confirm('¿Eliminar categoría?');">
                  <button type="submit" class="text-red-400 hover:underline">Eliminar</button>
                </form>
              {% else %}
                <span class="text-gray-500">No se puede eliminar</span>
              {% endif %}
            </td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
  </div>
</section>
{% endblock %}
```

### 6.4 NUEVO: category_form.html

```html
{% extends 'base.html' %}

{% block title %}
  {{ 'Añadir' if action == 'add' else 'Editar' }} Categoría
{% endblock %}

{% block header %}
  <span class="text-timetracker-primary">
    {{ 'Añadir Nueva' if action == 'add' else 'Editar' }} Categoría
  </span>
{% endblock %}

{% block content %}
<div class="max-w-2xl mx-auto bg-gray-900 border border-gray-700 rounded-lg shadow-md p-8">
  <form method="POST"
        action="{{ url_for('admin.add_category') if action == 'add' else url_for('admin.edit_category', category_id=category.id) }}">
    
    <!-- Nombre -->
    <div class="mb-4">
      <label for="name" class="block text-sm font-medium text-gray-300 mb-1">
        Nombre de categoría
      </label>
      <input type="text"
             id="name"
             name="name"
             required
             value="{{ category.name if category else '' }}"
             class="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded-md text-gray-100 focus:outline-none focus:ring-2 focus:ring-timetracker-primary"
             placeholder="Ej: Gerente, Operario, Supervisor">
    </div>

    <!-- Descripción -->
    <div class="mb-6">
      <label for="description" class="block text-sm font-medium text-gray-300 mb-1">
        Descripción (opcional)
      </label>
      <textarea id="description"
                name="description"
                rows="3"
                class="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded-md text-gray-100 focus:outline-none focus:ring-2 focus:ring-timetracker-primary"
                placeholder="Descripción de los responsabilidades">{{ category.description if category else '' }}</textarea>
    </div>

    <!-- Botones -->
    <div class="flex gap-3">
      <button type="submit" 
              class="px-6 py-2 rounded text-white transition-all hover:opacity-90"
              style="background-color: var(--accent-primary);">
        {{ 'Crear' if action == 'add' else 'Actualizar' }} Categoría
      </button>
      <a href="{{ url_for('admin.manage_categories') }}"
         class="px-6 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded transition-all">
        Cancelar
      </a>
    </div>
  </form>
</div>
{% endblock %}
```

---

## 7. MIGRACIÓN DE DATOS

### 7.1 Script de Migración Alembic

**Crear migración:**
```bash
flask db migrate -m "Replace categoria enum with category_id foreign key"
```

**Archivo generado:** `migrations/versions/XXXXX_replace_categoria_enum.py`

```python
from alembic import op
import sqlalchemy as sa

def upgrade():
    # 1. Crear nueva columna category_id (temporal)
    op.add_column('user', sa.Column('category_id_temp', sa.Integer(), nullable=True))
    
    # 2. Crear constraint FK (sin aplicar aún)
    op.create_foreign_key(
        'fk_user_category_temp',
        'user', 'category',
        ['category_id_temp'], ['id'],
        ondelete='SET NULL'
    )
    
    # 3. Migrar datos: mapear ENUM values a Category IDs
    op.execute("""
    UPDATE "user" u
    SET category_id_temp = c.id
    FROM category c
    WHERE u.categoria = c.name
      AND u.client_id = c.client_id
    """)
    
    # 4. Renombrar columa
    op.alter_column('user', 'category_id_temp', new_column_name='category_id')
    
    # 5. Eliminar constraint FK temporal y recrear con nombre correcto
    op.drop_constraint('fk_user_category_temp', 'user', type_='foreignkey')
    op.create_foreign_key(
        'fk_user_category_id',
        'user', 'category',
        ['category_id'], ['id'],
        ondelete='SET NULL'
    )
    
    # 6. Eliminar columna ENUM antigua
    op.drop_column('user', 'categoria')

def downgrade():
    # Revertir es complejo, mejor no permitir downgrade
    raise NotImplementedError("Downgrade no soportado para esta migración")
```

---

## 8. EXPORTACIÓN ACTUALIZADA

### 8.1 Actualizar export.py

**Cambio en queries de exportación:**

```python
# ANTES
if categoria:
    query = query.filter(User.categoria == categoria)

# DESPUÉS
if categoria_id:
    try:
        categoria_id = int(categoria_id)
        query = query.filter(User.category_id == categoria_id)
    except (ValueError, TypeError):
        pass
```

**Cambio en columnas:**

```python
# ANTES
ws1.cell(row=row_num, column=3).value = user.categoria if user and user.categoria else "-"

# DESPUÉS
categoria_name = user.category_rel.name if user and user.category_rel else "-"
ws1.cell(row=row_num, column=3).value = categoria_name
```

### 8.2 Actualizar export_excel.html

```html
<!-- Filtro categoría -->
<div>
  <label class="block text-xs text-gray-300 mb-1">Categoría</label>
  <select name="category_id" class="w-full px-3 py-2 rounded bg-gray-800 text-gray-200 border border-gray-700">
    <option value="">Todas</option>
    {% for cat_id, cat_name in categorias %}
      <option value="{{ cat_id }}" 
              {{ 'selected' if request.args.get('category_id') == cat_id|string else '' }}>
        {{ cat_name }}
      </option>
    {% endfor %}
  </select>
</div>
```

---

## 9. COMPATIBILIDAD Y PROPERTY

Para mantener compatibilidad con código que usa `user.categoria`:

```python
# En models.py - User class
@property
def categoria(self):
    """
    Propiedad para compatibilidad con código antiguo.
    Retorna el nombre de la categoría o None.
    """
    if self.category_rel:
        return self.category_rel.name
    return None

@categoria.setter
def categoria(self, value):
    """
    Para compatibilidad, permite setear por nombre.
    ADVERTENCIA: Solo funciona si la categoría existe en BD.
    """
    if value is None:
        self.category_id = None
        return
    
    if isinstance(value, int):
        self.category_id = value
        return
    
    # Si es string, buscar la categoría por nombre y client_id
    if hasattr(self, 'client_id'):
        cat = Category.query.filter_by(
            client_id=self.client_id,
            name=value
        ).first()
        if cat:
            self.category_id = cat.id
```

---

## 10. CHECKLIST DE IMPLEMENTACIÓN

- [ ] Crear backup BD
- [ ] Actualizar models.py (User + Category)
- [ ] Actualizar models/database.py (agregar Category a TENANT_MODELS)
- [ ] Crear migración Alembic
- [ ] Ejecutar migración en dev
- [ ] Crear CRUD categorías en admin.py
- [ ] Actualizar manage_users() para usar category_id
- [ ] Crear manage_categories.html
- [ ] Crear category_form.html
- [ ] Actualizar user_form.html
- [ ] Actualizar manage_users.html (filtros)
- [ ] Actualizar export.py
- [ ] Actualizar export_excel.html
- [ ] Actualizar admin_calendar (si usa categoría)
- [ ] Actualizar admin_dashboard (si muestra categorías)
- [ ] Pruebas: CRUD categorías
- [ ] Pruebas: Crear/editar usuarios con categorías
- [ ] Pruebas: Filtrar por categoría
- [ ] Pruebas: Exportar con categorías
- [ ] Ejecutar migración en producción
- [ ] Monitorear logs

