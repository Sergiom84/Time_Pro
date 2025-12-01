from sqlalchemy.exc import IntegrityError
from models.models import Category, User, db
from services.exceptions import ResourceNotFound, ResourceAlreadyExists, ValidationError, OperationNotAllowed

class CategoryService:
    @staticmethod
    def get_all(client_id):
        """Obtiene todas las categorías de un cliente."""
        return Category.query.filter_by(client_id=client_id).order_by(Category.name).all()

    @staticmethod
    def get_by_id(category_id, client_id):
        """Obtiene una categoría por ID y verifica que pertenezca al cliente."""
        # Filtrar directamente por client_id en la query para mayor seguridad
        return Category.query.filter_by(id=category_id, client_id=client_id).first()

    @staticmethod
    def get_by_name(name, client_id):
        """Obtiene una categoría por nombre y client_id."""
        if not name:
            return None
        return Category.query.filter_by(client_id=client_id, name=name).first()

    @staticmethod
    def create(client_id, name, description=None):
        """
        Crea una nueva categoría.
        """
        name = name.strip()
        if not name:
            raise ValidationError("El nombre de la categoría es obligatorio.")

        existing = Category.query.filter_by(client_id=client_id, name=name).first()
        if existing:
            raise ResourceAlreadyExists(f"Ya existe una categoría con el nombre '{name}'.")

        try:
            category = Category(
                client_id=client_id,
                name=name,
                description=description.strip() if description else None
            )
            db.session.add(category)
            db.session.commit()
            return category
        except IntegrityError:
            db.session.rollback()
            # Carrera con otro insert del mismo nombre
            raise ResourceAlreadyExists(f"Ya existe una categoría con el nombre '{name}'.")
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def update(category_id, client_id, name, description=None):
        """
        Actualiza una categoría existente.
        """
        category = CategoryService.get_by_id(category_id, client_id)
        if not category:
            raise ResourceNotFound("Categoría no encontrada o no pertenece al cliente.")

        name = name.strip()
        if not name:
            raise ValidationError("El nombre de la categoría es obligatorio.")

        # Verificar duplicados (excluyendo la propia categoría)
        existing = Category.query.filter(
            Category.client_id == client_id,
            Category.name == name,
            Category.id != category_id
        ).first()
        
        if existing:
            raise ResourceAlreadyExists(f"Ya existe otra categoría con el nombre '{name}'.")

        try:
            category.name = name
            category.description = description.strip() if description else None
            db.session.commit()
            return category
        except IntegrityError:
            db.session.rollback()
            raise ResourceAlreadyExists(f"Ya existe otra categoría con el nombre '{name}'.")
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def delete(category_id, client_id):
        """
        Elimina una categoría.
        """
        category = CategoryService.get_by_id(category_id, client_id)
        if not category:
            raise ResourceNotFound("Categoría no encontrada o no pertenece al cliente.")

        # Verificar si hay usuarios usando esta categoría
        users_count = User.query.filter_by(category_id=category_id).count()
        if users_count > 0:
            raise OperationNotAllowed(f"No puedes eliminar esta categoría porque está siendo utilizada por {users_count} usuario(s).")

        try:
            db.session.delete(category)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise
