from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import Query


class TenantAwareQuery(Query):
    """
    Query personalizada que aplica filtrado multitenant de forma transparente.
    """

    TENANT_MODELS = {
        "User",
        "TimeRecord",
        "EmployeeStatus",
        "WorkPause",
        "LeaveRequest",
        "SystemConfig",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._bypass_tenant = False
        self._tenant_filtered = False

    def _clone(self):
        """
        Propaga banderas personalizadas cuando SQLAlchemy clona la Query.
        """
        clone = super()._clone()
        clone._bypass_tenant = getattr(self, "_bypass_tenant", False)
        clone._tenant_filtered = getattr(self, "_tenant_filtered", False)
        return clone

    def bypass_tenant_filter(self):
        """
        Permite desactivar el filtro multitenant (solo usar en casos controlados).
        """
        self._bypass_tenant = True
        return self

    def _should_filter_entity(self, entity):
        if entity is None or not hasattr(entity, "__name__"):
            return False
        return entity.__name__ in self.TENANT_MODELS and hasattr(entity, "client_id")

    def _apply_tenant_filter(self):
        """
        Inserta el filtro por client_id si corresponde.
        """
        if self._bypass_tenant or getattr(self, "_tenant_filtered", False):
            return self

        try:
            from utils.multitenant import get_current_client_id

            client_id = get_current_client_id()
            if not client_id:
                return self
        except (RuntimeError, ImportError):
            return self

        query = self

        for desc in self.column_descriptions:
            entity = desc.get("entity")
            if not self._should_filter_entity(entity):
                continue

            # Permitir aplicar filtros aunque la Query ya tenga limit/offset
            query = query.enable_assertions(False)
            query = Query.filter(query, entity.client_id == client_id)
            query._tenant_filtered = True
            break

        return query

    # ------------------------------------------------------------------
    # Metodos sobreescritos para asegurar el filtrado
    # ------------------------------------------------------------------
    def all(self):
        return Query.all(self._apply_tenant_filter())

    def first(self):
        return Query.first(self._apply_tenant_filter())

    def one(self):
        return Query.one(self._apply_tenant_filter())

    def one_or_none(self):
        return Query.one_or_none(self._apply_tenant_filter())

    def count(self):
        return Query.count(self._apply_tenant_filter())

    def __iter__(self):
        return Query.__iter__(self._apply_tenant_filter())

    def get_or_404(self, ident, description=None):
        """
        Aplica el filtro multitenant al recuperar por ID.
        """
        from flask import abort

        instance = Query.get(self, ident)

        if instance is None:
            abort(404, description=description)

        try:
            from utils.multitenant import get_current_client_id

            client_id = get_current_client_id()
            if hasattr(instance, "client_id") and instance.client_id != client_id:
                abort(404, description=description)
        except RuntimeError:
            pass

        return instance


db = SQLAlchemy(query_class=TenantAwareQuery)
